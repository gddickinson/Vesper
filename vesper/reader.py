"""The book **Reader** -- a non-sleep audiobook view (the user-requested novels
feature). Opens from the Books menu; degrades gracefully to an empty state until
books are added (the downloader / import land in later rounds).

Two presentations via a TOGGLE: **read-along** (the text scrolls and the current
sentence highlights as it is narrated) or **audio-only** (narration + the calm
visuals, no text). Either way it narrates a :class:`breathsim.books.Book` through
the shared :class:`narration.Narrator` at a steady reading pace (no breath-gating,
no Sleep wind-down), and **persists the resume position** as each sentence is
spoken, so a book picks up where it left off.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import (QCheckBox, QDialog, QHBoxLayout, QPushButton,
                               QTextEdit, QVBoxLayout)

from breathsim import bookreader, books

from . import theme, widgets
from .widgets import LabeledSlider, muted


def open_reader(win):
    dlg = _ReaderDialog(win)
    win._reader_dlg = dlg                       # keep a ref so it isn't GC'd
    dlg.show()                                  # modeless: the main loop keeps ticking
    return dlg


class _ReaderDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self._ranges = []                       # per-sentence (start, end) char offsets
        self._book = None
        self.setWindowTitle("Read a book")
        self.setStyleSheet(win.styleSheet() or theme.STYLESHEET)
        self.setMinimumWidth(560)
        v = QVBoxLayout(self)

        t = widgets.muted("")
        t.setText("Read a book")
        t.setObjectName("title")
        v.addWidget(t)

        self._index = {b["id"]: b for b in books.list_books()}
        items = [b["title"] for b in self._index.values()] or []
        self._ids = list(self._index.keys())
        self.combo = widgets.combo(items or ["(no books yet)"],
                                   current=(items[0] if items else None),
                                   on_change=lambda _t: self._load_selected())
        v.addWidget(muted("Book"))
        v.addWidget(self.combo)

        self.readalong = QCheckBox("Show read-along text (highlight as it reads)")
        self.readalong.setChecked(True)
        self.readalong.toggled.connect(self._sync_pane)
        v.addWidget(self.readalong)
        self.longpauses = QCheckBox("Longer pauses between paragraphs")
        self.longpauses.setChecked(True)
        v.addWidget(self.longpauses)
        self.speed = LabeledSlider("Reading speed", 0.6, 1.3, 1.0, decimals=2,
                                   suffix="x", on_change=self._on_speed)
        v.addWidget(self.speed)

        self.pane = QTextEdit()
        self.pane.setReadOnly(True)
        self.pane.setMinimumHeight(240)
        v.addWidget(self.pane, 1)

        row = QHBoxLayout()
        self.start_btn = QPushButton("Start reading")
        self.start_btn.setObjectName("accent")
        self.start_btn.clicked.connect(self._start)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)
        row.addWidget(self.start_btn)
        row.addWidget(self.stop_btn)
        v.addLayout(row)

        self.note = muted("")
        v.addWidget(self.note)

        if not items:
            self.note.setText("No books in your library yet. Downloading and "
                              "importing your own texts arrive soon.")
            self.start_btn.setEnabled(False)
            self.combo.setEnabled(False)
        else:
            self._load_selected()

        # a GUI-thread timer that follows the narrator's current sentence
        from PySide6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.setInterval(180)
        self._timer.timeout.connect(self._follow)
        self._last_hl = -1

    # --- book loading + read-along pane ---
    def _selected_id(self):
        i = self.combo.currentIndex()
        return self._ids[i] if 0 <= i < len(self._ids) else None

    def _load_selected(self):
        bid = self._selected_id()
        self._book = books.load(bid) if bid else None
        sents = self._book.sentences() if self._book else []
        starts = set(self._book.paragraph_starts()) if self._book else set()
        text, self._ranges = "", []
        for idx, s in enumerate(sents):
            if idx in starts and idx != 0:          # keep paragraph breaks readable
                text += "\n\n"
            a = len(text)
            text += s + " "
            self._ranges.append((a, a + len(s)))
        self.pane.setPlainText(text)
        self._last_hl = -1
        if self._book:
            pos = books.position(bid)
            done = self._book.sentence_count()
            where = (f"resume at sentence {pos + 1} of {done} "
                     f"({books.percent_read(bid)}% read)" if pos
                     else f"{done} sentences")
            self.note.setText(f"{self._book.title} — {where}.")
        self._sync_pane()

    def _sync_pane(self, *_):
        self.pane.setVisible(self.readalong.isChecked())

    def _on_speed(self, val):
        self.win.narrator.speed = float(val)

    # --- playback ---
    def _start(self):
        if not self._book:
            return
        bid = self._book.id
        lp, pp = (700, 1600) if self.longpauses.isChecked() else (650, 900)
        us = bookreader.units(self._book, start=books.position(bid),
                              line_pause=lp, para_pause=pp)
        self.win._reading = True                # reader owns the narration pace
        self.win.narrator.speed = float(self.speed.value())
        self.win.narrator.pause_scale = 1.0
        self._reader_idx = books.position(bid)
        self.win.narrator.start(us, lambda: 1.0, None, self._on_unit)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        if self.readalong.isChecked():
            self._timer.start()

    def _on_unit(self, unit):
        # narrator thread: only touch plain state + persist resume (a small write)
        i = int(unit.get("sentence", 0))
        self._reader_idx = i
        if self._book:
            books.set_position(self._book.id, i)

    def _follow(self):
        # GUI thread: highlight + scroll to the current sentence
        i = getattr(self, "_reader_idx", -1)
        if i == self._last_hl or not (0 <= i < len(self._ranges)):
            return
        self._last_hl = i
        a, b = self._ranges[i]
        sel = QTextEdit.ExtraSelection()
        cur = QTextCursor(self.pane.document())
        cur.setPosition(a)
        cur.setPosition(b, QTextCursor.MoveMode.KeepAnchor)
        sel.cursor = cur
        sel.format.setBackground(QColor(theme.ACCENT))
        sel.format.setForeground(QColor(theme.BG))
        self.pane.setExtraSelections([sel])
        scroll = QTextCursor(self.pane.document())
        scroll.setPosition(a)
        self.pane.setTextCursor(scroll)
        self.pane.ensureCursorVisible()

    def _stop(self):
        self._timer.stop()
        self.win.narrator.stop()
        self.win._reading = False
        if self._book:
            books.set_position(self._book.id, getattr(self, "_reader_idx", 0))
        self.start_btn.setEnabled(bool(self._book))
        self.stop_btn.setEnabled(False)

    def closeEvent(self, e):
        self._stop()
        super().closeEvent(e)
