"""The central **read-along pane** for Read mode (and any in-app reading).

A scrolling text view that shows a book and highlights + auto-scrolls the
sentence currently being narrated. It sits *below* the face/scene in the central
vertical splitter, so Read mode keeps the visualization and adds the text. Hidden
unless reading with read-along on. The narration itself is driven by
``win_read._ReadMixin``; this is just the view plus a slim header (title,
progress, play/pause, font size).
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QTextEdit,
                               QVBoxLayout, QWidget)

from . import theme

# Reading-comfort themes for the text pane: (page bg, ink, highlight bg, highlight ink).
THEMES = {
    "Night": ("#0f1117", "#cdd2da", theme.ACCENT, "#0b0d12"),   # dark, default
    "Sepia": ("#efe5d0", "#43381f", "#caa45a", "#2a2412"),      # warm paper
    "Day":   ("#e9ecef", "#1b1f24", "#7fb4d8", "#11161b"),      # light room
}
THEME_NAMES = list(THEMES)


class ReadAlongPane(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self._ranges = []                       # per-sentence (start, end) offsets
        self._book = None
        self._last_hl = -1
        self._font_pt = 15
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 6, 12, 10)
        hdr = QHBoxLayout()
        self.title = QLabel("Read")
        self.title.setObjectName("title")
        self.prog = QLabel("")
        self.prog.setObjectName("muted")
        am = QPushButton("A-")
        ap = QPushButton("A+")
        am.setMaximumWidth(40)
        ap.setMaximumWidth(40)
        am.setToolTip("Smaller reading text")
        ap.setToolTip("Larger reading text")
        am.clicked.connect(lambda: self.bump_font(-1))
        ap.clicked.connect(lambda: self.bump_font(1))
        self.play = QPushButton("Read")
        self.play.setObjectName("accent")
        self.play.setToolTip("Start or pause the narration")
        self.play.clicked.connect(lambda: self.win.toggle_reading())
        hdr.addWidget(self.title, 1)
        hdr.addWidget(self.prog)
        hdr.addWidget(am)
        hdr.addWidget(ap)
        hdr.addWidget(self.play)
        v.addLayout(hdr)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setMinimumHeight(160)
        v.addWidget(self.text, 1)
        self._hl_bg, self._hl_fg = theme.ACCENT, "#0b0d12"
        self.set_theme("Night")
        self._apply_font()

    def set_theme(self, name):
        """Recolour the reading page (Night / Sepia / Day) + the highlight."""
        bg, ink, hl_bg, hl_fg = THEMES.get(name, THEMES["Night"])
        self._theme = name if name in THEMES else "Night"
        self._hl_bg, self._hl_fg = hl_bg, hl_fg
        self.text.setStyleSheet(
            f"QTextEdit {{ background:{bg}; color:{ink}; border:none; "
            f"selection-background-color:{hl_bg}; padding:6px; }}")
        cur, self._last_hl = self._last_hl, -1      # force re-highlight in the new colours
        if 0 <= cur < len(self._ranges):
            self.highlight(cur)

    def bump_font(self, d):
        self._font_pt = max(10, min(30, self._font_pt + d))
        self._apply_font()

    def _apply_font(self):
        f = self.text.font()
        f.setPointSize(self._font_pt)
        self.text.setFont(f)

    def set_playing(self, on):
        self.play.setText("Pause" if on else "Read")

    def set_book(self, book, pos=0, percent=0):
        """Render the book's text, keep per-sentence char ranges, jump to pos."""
        self._book = book
        self._ranges = []
        self._last_hl = -1
        if not book:
            self.title.setText("Read")
            self.prog.setText("no book yet")
            self.text.setPlainText(                 # a helpful empty state, not a blank box
                "No book loaded yet.\n\n"
                "Open the Books menu and choose \"Find & manage books\" to download a "
                "free classic from Project Gutenberg or Standard Ebooks -- or simply "
                "drag a .txt or .epub file onto the window.\n\n"
                "Then press Read, and the text will follow along, line by line, as it "
                "is gently narrated to you.")
            return
        sents = book.sentences()
        starts = set(book.paragraph_starts())
        text = ""
        for idx, s in enumerate(sents):
            if idx in starts and idx != 0:
                text += "\n\n"                  # keep paragraph breaks readable
            a = len(text)
            text += s + " "
            self._ranges.append((a, a + len(s)))
        self.text.setPlainText(text)
        self.title.setText(book.title)
        self.prog.setText(f"{percent}% read" if percent else f"{len(sents)} sentences")
        if pos:
            self.highlight(pos)

    def highlight(self, i):
        """Highlight + scroll to sentence i (call on the GUI thread)."""
        if i == self._last_hl or not (0 <= i < len(self._ranges)):
            return
        self._last_hl = i
        a, b = self._ranges[i]
        sel = QTextEdit.ExtraSelection()
        cur = QTextCursor(self.text.document())
        cur.setPosition(a)
        cur.setPosition(b, QTextCursor.MoveMode.KeepAnchor)
        sel.cursor = cur
        sel.format.setBackground(QColor(self._hl_bg))
        sel.format.setForeground(QColor(self._hl_fg))
        self.text.setExtraSelections([sel])
        scroll = QTextCursor(self.text.document())
        scroll.setPosition(a)
        self.text.setTextCursor(scroll)
        self.text.ensureCursorVisible()
        self.prog.setText(f"sentence {i + 1} of {len(self._ranges)}")
