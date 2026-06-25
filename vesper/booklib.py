"""The **Find & manage books** dialog -- search a public-domain catalog, see a
book's popularity / language / length *before* downloading, download it into the
local library, and manage what you have (rename, re-download, delete, with a
running library summary).

SAFETY: opening this window does nothing on the network. A request happens ONLY
when you press Search / Download / Check length (an explicit action), reaches the
open public-domain catalog (Project Gutenberg via Gutendex -- no account, no key),
runs on a **daemon thread** so the UI never blocks, and **fails closed with a
clear reason** (no internet -> a gentle note, never a crash). Downloaded text is
treated as untrusted and only ever parsed into a local :class:`books.Book`.
"""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QInputDialog, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton, QVBoxLayout)

from breathsim import bookmeta, books, booksource

from . import theme
from .widgets import muted

_ROLE = Qt.ItemDataRole.UserRole

# Friendly headlines for search failures (download failures carry their own
# detail sentence from booksource.Outcome).
_SEARCH_REASON = {
    "no_network": "No internet connection just now -- your library still works "
                  "offline.",
    "timeout": "The search timed out -- the network may be slow. Please try again.",
    "tls": "The secure connection timed out -- please try again.",
    "no_matches": "No public-domain matches -- try another title or author.",
    "error": "Could not search just now -- please try again.",
}


class _Worker(QObject):
    """Runs a callable on a daemon thread, delivers the result on the GUI thread."""
    done = Signal(object)

    def run(self, fn):
        def work():
            try:
                self.done.emit(fn())
            except Exception as e:
                self.done.emit(e)
        threading.Thread(target=work, daemon=True).start()


def _refresh_app(win):
    """Surface a library change in the menus AND the *current* workspace -- both
    Sleep and Read have a book picker, so whichever is showing gets rebuilt (the
    fix for 'a downloaded book never appears in the Read picker')."""
    try:
        if hasattr(win, "rebuild_menu"):
            win.rebuild_menu()
        mode = getattr(win, "current_mode", None)
        if mode in ("Sleep", "Read") and hasattr(win, "panel"):
            win.panel.build_workspace(mode)
    except Exception:
        pass


def open_library(win):
    dlg = _LibraryDialog(win)
    win._booklib_dlg = dlg
    dlg.show()
    return dlg


def import_book_dialog(win):
    """Pick a local .txt/.epub and import it into the library (stays on this
    device). Refreshes the Reader / Sleep picker / Books count on success."""
    from PySide6.QtWidgets import QFileDialog
    from breathsim import bookimport
    path, _ = QFileDialog.getOpenFileName(
        win, "Import a book", "",
        "Books (*.txt *.epub);;Text (*.txt);;EPUB (*.epub)")
    if not path:
        return None
    bid = bookimport.import_file(path)
    if not bid:
        QMessageBox.information(win, "Import a book",
                               "Could not read that file. Try a plain .txt or a "
                               "standard .epub.")
        return None
    _refresh_app(win)
    win.status.showMessage("Imported. Find it in the Reader and the Sleep story "
                           "picker.", 5000)
    return bid


class _LibraryDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self._results = []
        self._workers = []
        self._busy = False
        self.setWindowTitle("Find & manage books")
        self.setStyleSheet(win.styleSheet() or theme.STYLESHEET)
        self.setMinimumWidth(600)
        v = QVBoxLayout(self)

        title = muted("Find & manage books")
        title.setObjectName("title")
        v.addWidget(title)
        blurb = muted("Search the public-domain library at Project Gutenberg and "
                      "download free books to read or fall asleep to. Searching "
                      "and downloading use the internet; nothing is sent anywhere, "
                      "and your own files stay on this device.")
        blurb.setWordWrap(True)
        v.addWidget(blurb)

        row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText("Search by title or author (e.g. Austen)…")
        self.query.returnPressed.connect(self._search)
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self._search)
        row.addWidget(self.query, 1)
        row.addWidget(self.search_btn)
        v.addLayout(row)

        self.results = QListWidget()
        self.results.setMinimumHeight(160)
        self.results.itemSelectionChanged.connect(self._sync_buttons)
        self.results.itemDoubleClicked.connect(lambda _i: self._download())
        v.addWidget(self.results, 1)

        drow = QHBoxLayout()
        self.dl_btn = QPushButton("Download selected")
        self.dl_btn.setObjectName("accent")
        self.dl_btn.setEnabled(False)
        self.dl_btn.clicked.connect(self._download)
        self.len_btn = QPushButton("Check length")
        self.len_btn.setEnabled(False)
        self.len_btn.setToolTip("Ask the server how big this book is (an estimate; "
                                "the exact length always shows once it's saved).")
        self.len_btn.clicked.connect(self._check_length)
        drow.addWidget(self.dl_btn, 1)
        drow.addWidget(self.len_btn)
        v.addLayout(drow)

        imp = QPushButton("Import a file (.txt / .epub) from this device…")
        imp.clicked.connect(self._import)
        v.addWidget(imp)

        self.lib_header = muted("Your library")
        v.addWidget(self.lib_header)
        self.library = QListWidget()
        self.library.setMinimumHeight(120)
        self.library.itemSelectionChanged.connect(self._sync_buttons)
        v.addWidget(self.library, 1)

        mrow = QHBoxLayout()
        self.open_btn = QPushButton("Open in Reader")
        self.open_btn.clicked.connect(self._open_in_reader)
        self.rename_btn = QPushButton("Rename…")
        self.rename_btn.clicked.connect(self._rename)
        self.again_btn = QPushButton("Re-download…")
        self.again_btn.setToolTip("Search for this title again to fetch a fresh "
                                  "copy (useful if a book came through shortened).")
        self.again_btn.clicked.connect(self._redownload)
        self.del_btn = QPushButton("Delete…")
        self.del_btn.clicked.connect(self._delete)
        for b in (self.open_btn, self.rename_btn, self.again_btn, self.del_btn):
            b.setEnabled(False)
            mrow.addWidget(b)
        v.addLayout(mrow)

        self.note = muted("")
        self.note.setWordWrap(True)
        v.addWidget(self.note)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

        self._refresh_library()

    # --- search ---
    def _search(self):
        q = self.query.text().strip()
        if not q or self._busy:
            return
        self._set_busy(True)
        self.note.setText("Searching the public-domain catalog…")
        w = _Worker()
        self._workers.append(w)
        w.done.connect(self._on_results, Qt.ConnectionType.QueuedConnection)
        w.run(lambda: booksource.search_ex(q))

    def _on_results(self, res):
        self._set_busy(False)
        rows, reason = res if isinstance(res, tuple) else ([], "error")
        if isinstance(res, Exception):
            rows, reason = [], "error"
        self.results.clear()
        self._results = rows
        if not rows:
            self.note.setText(_SEARCH_REASON.get(reason, "No results just now."))
            self._sync_buttons()
            return
        for r in rows:
            label = r["title"] + (f"  --  {r['author']}" if r.get("author") else "")
            cap = booksource.result_caption(r)
            it = QListWidgetItem(label + (f"\n      {cap}" if cap else ""))
            it.setData(_ROLE, r)
            self.results.addItem(it)
        s = "book" if len(rows) == 1 else "books"
        self.note.setText(f"{len(rows)} public-domain {s} found. "
                          "Stars show popularity; download to see the exact length.")
        self._sync_buttons()

    # --- download ---
    def _download(self):
        it = self.results.currentItem()
        if not it or self._busy:
            return
        result = it.data(_ROLE)
        self._set_busy(True)
        self.note.setText(f"Downloading \"{result['title']}\"… (verifying it "
                          "arrives whole)")
        w = _Worker()
        self._workers.append(w)
        w.done.connect(self._on_downloaded, Qt.ConnectionType.QueuedConnection)
        w.run(lambda: booksource.download_ex(result))

    def _on_downloaded(self, out):
        self._set_busy(False)
        if isinstance(out, Exception) or out is None:
            self.note.setText("That book could not be downloaded -- please try "
                              "again.")
            return
        if not out.ok:
            self.note.setText(out.detail or "That book could not be downloaded.")
            return
        mins = bookmeta.estimate_minutes(sentences=out.sentences)
        dur = bookmeta.format_duration(mins)
        size = bookmeta.format_size(out.byte_size)
        extra = "  -  ".join(p for p in (f"{out.sentences:,} sentences", dur, size) if p)
        self.note.setText(f"Saved \"{out.title}\" ({extra}). Find it in the Reader "
                          "and the Sleep story picker.")
        self._refresh_library()
        _refresh_app(self.win)

    def _check_length(self):
        it = self.results.currentItem()
        if not it or self._busy:
            return
        result = it.data(_ROLE)
        self._set_busy(True)
        self.note.setText(f"Checking the size of \"{result['title']}\"…")
        w = _Worker()
        self._workers.append(w)
        w.done.connect(lambda sz: self._on_length(result, sz),
                       Qt.ConnectionType.QueuedConnection)
        w.run(lambda: booksource.probe_size(result))

    def _on_length(self, result, size):
        self._set_busy(False)
        if isinstance(size, Exception) or not size:
            self.note.setText("The server didn't report this book's size -- the "
                              "exact length will show once it's downloaded.")
            return
        length = bookmeta.length_from_bytes(size)
        self.note.setText(f"\"{result['title']}\" is {bookmeta.format_size(size)}"
                          + (f"  -  {length}." if length else "."))
        # re-render the row to include the now-known length
        it = self.results.currentItem()
        if it and it.data(_ROLE) is result:
            cap = booksource.result_caption(result)
            base = it.text().split("\n")[0]
            it.setText(base + (f"\n      {cap}" if cap else ""))

    # --- library list + management ---
    def _refresh_library(self):
        self.library.clear()
        for b in books.list_books():
            label = b.get("title", "Untitled")
            if b.get("author"):
                label += f"  --  {b['author']}"
            pct = books.percent_read(b.get("id"))
            desc = bookmeta.describe_book(b)
            size = bookmeta.format_size(books.disk_bytes(b.get("id")))
            bits = [f"{pct}% read"] if pct else []
            bits += [desc] + ([size] if size else [])
            it = QListWidgetItem(label + "\n      " + "  -  ".join(p for p in bits if p))
            it.setData(_ROLE, b.get("id"))
            self.library.addItem(it)
        self.lib_header.setText("Your library  -  "
                                + bookmeta.report_line(bookmeta.library_report()))
        self._sync_buttons()

    def _selected_book(self):
        it = self.library.currentItem()
        return it.data(_ROLE) if it else None

    def _book_meta(self, bid):
        return next((b for b in books.list_books() if b.get("id") == bid), {})

    def _open_in_reader(self):
        bid = self._selected_book()
        if not bid:
            return
        if hasattr(self.win, "set_reading_book"):
            try:
                if getattr(self.win, "current_mode", None) != "Read" \
                        and hasattr(self.win, "apply_mode"):
                    self.win.apply_mode("Read")
                self.win.set_reading_book(bid)
                self.note.setText("Opened in the Reader.")
                self.accept()
            except Exception:
                self.note.setText("Could not open the Reader just now.")

    def _rename(self):
        bid = self._selected_book()
        if not bid:
            return
        meta = self._book_meta(bid)
        title, ok = QInputDialog.getText(self, "Rename book", "Title:",
                                         text=meta.get("title", ""))
        if not ok or not title.strip():
            return
        author, ok = QInputDialog.getText(self, "Rename book",
                                          "Author (optional):",
                                          text=meta.get("author", ""))
        if not ok:
            author = meta.get("author", "")
        books.update_meta(bid, title=title, author=author)
        self.note.setText("Renamed.")
        self._refresh_library()
        _refresh_app(self.win)

    def _redownload(self):
        meta = self._book_meta(self._selected_book())
        if not meta:
            return
        q = " ".join(p for p in (meta.get("title", ""), meta.get("author", "")) if p)
        self.query.setText(q.strip())
        self.note.setText("Searching for a fresh copy -- download it again below, "
                          "then delete the old one if you like.")
        self._search()

    def _delete(self):
        bid = self._selected_book()
        if not bid:
            return
        meta = self._book_meta(bid)
        title = meta.get("title", "this book")
        if QMessageBox.question(
                self, "Delete book",
                f"Remove \"{title}\" from your library?\n\nThis deletes the saved "
                "text and your reading place. You can download it again any time.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        books.delete(bid)
        self.note.setText(f"Removed \"{title}\" from your library.")
        self._refresh_library()
        _refresh_app(self.win)

    def _import(self):
        if import_book_dialog(self.win):
            self._refresh_library()

    # --- shared UI state ---
    def _set_busy(self, busy):
        self._busy = busy
        for b in (self.search_btn, self.dl_btn, self.len_btn, self.again_btn):
            b.setEnabled(not busy)
        if not busy:
            self._sync_buttons()

    def _sync_buttons(self):
        if self._busy:
            return
        has_res = self.results.currentItem() is not None
        self.dl_btn.setEnabled(has_res)
        self.len_btn.setEnabled(has_res)
        has_lib = self.library.currentItem() is not None
        for b in (self.open_btn, self.rename_btn, self.again_btn, self.del_btn):
            b.setEnabled(has_lib)
