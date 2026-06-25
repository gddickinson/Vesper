"""The **Find & manage books** dialog -- search a public-domain catalog, download
a book into the local library, and remove books you no longer want.

SAFETY: opening this window does nothing on the network. A request happens ONLY
when you press **Search** or **Download** (an explicit action), reaches the open
public-domain catalog (Project Gutenberg via Gutendex -- no account, no key),
runs on a **daemon thread** so the UI never blocks, and **fails closed** (no
internet -> an empty result and a gentle note, never a crash). Downloaded text is
treated as untrusted and only ever parsed into a local :class:`books.Book`.
"""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout)

from breathsim import books, booksource

from . import theme, widgets
from .widgets import muted

_ROLE = Qt.ItemDataRole.UserRole


class _Worker(QObject):
    """Runs a callable on a daemon thread, delivers the result on the GUI thread."""
    done = Signal(object)        # the result, or an Exception

    def run(self, fn):
        def work():
            try:
                self.done.emit(fn())
            except Exception as e:
                self.done.emit(e)
        threading.Thread(target=work, daemon=True).start()


def open_library(win):
    dlg = _LibraryDialog(win)
    win._booklib_dlg = dlg
    dlg.show()
    return dlg


class _LibraryDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self._results = []
        self._workers = []
        self.setWindowTitle("Find & manage books")
        self.setStyleSheet(win.styleSheet() or theme.STYLESHEET)
        self.setMinimumWidth(560)
        v = QVBoxLayout(self)

        title = muted("Find & manage books")
        title.setObjectName("title")
        v.addWidget(title)
        blurb = muted("Search the public-domain library at Project Gutenberg "
                      "and download free books to read or fall asleep to. "
                      "Searching and downloading use the internet; nothing is "
                      "sent anywhere, and your own files stay on this device.")
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
        self.results.setMinimumHeight(150)
        self.results.itemSelectionChanged.connect(self._sync_buttons)
        v.addWidget(self.results, 1)
        self.dl_btn = QPushButton("Download selected")
        self.dl_btn.setObjectName("accent")
        self.dl_btn.setEnabled(False)
        self.dl_btn.clicked.connect(self._download)
        v.addWidget(self.dl_btn)

        v.addWidget(muted("Your library"))
        self.library = QListWidget()
        self.library.setMinimumHeight(110)
        self.library.itemSelectionChanged.connect(self._sync_buttons)
        v.addWidget(self.library, 1)
        self.del_btn = QPushButton("Delete selected book")
        self.del_btn.setEnabled(False)
        self.del_btn.clicked.connect(self._delete)
        v.addWidget(self.del_btn)

        self.note = muted("")
        v.addWidget(self.note)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

        self._refresh_library()

    # --- search ---
    def _search(self):
        q = self.query.text().strip()
        if not q:
            return
        self.search_btn.setEnabled(False)
        self.note.setText("Searching the public-domain catalog…")
        w = _Worker()
        self._workers.append(w)
        w.done.connect(self._on_results, Qt.ConnectionType.QueuedConnection)
        w.run(lambda: booksource.search(q))

    def _on_results(self, res):
        self.search_btn.setEnabled(True)
        if isinstance(res, Exception) or not res:
            self.results.clear()
            self.note.setText("No results (or no internet just now). "
                              "Your library still works offline.")
            return
        self._results = res
        self.results.clear()
        for r in res:
            label = r["title"] + (f"  --  {r['author']}" if r.get("author") else "")
            it = QListWidgetItem(label)
            it.setData(_ROLE, r)
            self.results.addItem(it)
        s = "book" if len(res) == 1 else "books"
        self.note.setText(f"{len(res)} public-domain {s} found.")

    # --- download ---
    def _download(self):
        it = self.results.currentItem()
        if not it:
            return
        result = it.data(_ROLE)
        self.dl_btn.setEnabled(False)
        self.note.setText(f"Downloading \"{result['title']}\"…")
        w = _Worker()
        self._workers.append(w)
        w.done.connect(self._on_downloaded, Qt.ConnectionType.QueuedConnection)
        w.run(lambda: booksource.download(result))

    def _on_downloaded(self, bid):
        self._sync_buttons()
        if isinstance(bid, Exception) or not bid:
            self.note.setText("That book could not be downloaded -- please try "
                              "another.")
            return
        self.note.setText("Saved to your library. Find it in the Reader and the "
                          "Sleep story picker.")
        self._refresh_library()
        # surface the new book in the Sleep picker + the Books count
        try:
            if hasattr(self.win, "rebuild_menu"):
                self.win.rebuild_menu()
            if getattr(self.win, "current_mode", None) == "Sleep":
                self.win.panel.build_workspace("Sleep")
        except Exception:
            pass

    # --- library list + delete ---
    def _refresh_library(self):
        self.library.clear()
        for b in books.list_books():
            label = b.get("title", "Untitled")
            if b.get("author"):
                label += f"  --  {b['author']}"
            label += f"   ({b.get('sentences', 0)} sentences)"
            it = QListWidgetItem(label)
            it.setData(_ROLE, b.get("id"))
            self.library.addItem(it)
        self._sync_buttons()

    def _delete(self):
        it = self.library.currentItem()
        if not it:
            return
        books.delete(it.data(_ROLE))
        self.note.setText("Removed from your library.")
        self._refresh_library()
        try:
            if hasattr(self.win, "rebuild_menu"):
                self.win.rebuild_menu()
            if getattr(self.win, "current_mode", None) == "Sleep":
                self.win.panel.build_workspace("Sleep")
        except Exception:
            pass

    def _sync_buttons(self):
        self.dl_btn.setEnabled(self.results.currentItem() is not None)
        self.del_btn.setEnabled(self.library.currentItem() is not None)
