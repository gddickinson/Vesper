"""The Read workspace's control card (a ControlPanel mixin).

Kept out of sections.py to stay under the file-size limit. Builds the "Reading"
card for Read mode: a book picker, an add-a-novel button, read-along toggle,
start/pause, reading speed, paragraph pauses and a narration-voice picker, with
a hint that breathing visuals (the left Start button) and a sleep fade (Sleep
mode) are opt-in. All actions call into the window's `_ReadMixin`.
"""
from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QPushButton

from .widgets import LabeledSlider, card, combo, muted


class _ReadCardMixin:
    def _card_read(self):
        from breathsim import books, narration
        frame, body = card("Reading")
        index = {b["id"]: b["title"] for b in books.list_books()}
        ids = list(index.keys())
        self._w["read_ids"] = ids
        titles = [index[i] for i in ids] or ["(no books yet)"]
        cur_title = index.get(getattr(self.win, "_read_bid", None))
        bk = combo(titles, cur_title or titles[0], self._on_read_book)
        bk.setEnabled(bool(ids))
        self._w["read_book"] = bk
        body.addWidget(muted("Book"))
        body.addWidget(bk)

        add = QPushButton("Add a novel (download or import)…")
        add.setToolTip("Get a free public-domain book or import your own "
                       ".txt/.epub. You can also drag a file onto the window.")
        add.clicked.connect(lambda: self._add_novel())
        body.addWidget(add)

        ch = QPushButton("Jump to a chapter…")
        ch.setToolTip("Open a searchable list of the book's chapters and jump to "
                      "one (your place is saved).")
        ch.clicked.connect(lambda: self._choose_chapter())
        ch.setEnabled(bool(self.win.book_chapters()))
        self._w["read_chapters"] = ch
        body.addWidget(ch)

        ra = QCheckBox("Show read-along text")
        ra.setChecked(getattr(self.win, "_read_along", True))
        ra.setToolTip("Scroll the text and highlight each sentence as it reads.")
        ra.toggled.connect(self.win.set_read_along)
        body.addWidget(ra)

        rb = QPushButton("Start / pause reading")
        rb.setObjectName("accent")
        rb.setEnabled(bool(ids))
        rb.clicked.connect(lambda: self.win.toggle_reading())
        self._w["read_btn"] = rb
        body.addWidget(rb)

        from .read_pane import THEME_NAMES
        body.addWidget(muted("Reading theme"))
        th = combo(THEME_NAMES, getattr(self.win, "_read_theme", "Night"),
                   self.win.set_reading_theme)
        th.setToolTip("Night (dark), Sepia (warm paper) or Day (light).")
        body.addWidget(th)

        s = LabeledSlider("Reading speed", 0.6, 1.3,
                          getattr(self.win, "_read_speed", 1.0), decimals=2,
                          suffix="x", on_change=self.win.set_reading_speed)
        body.addWidget(s)
        lp = QCheckBox("Longer pauses between paragraphs")
        lp.setChecked(getattr(self.win, "_read_long", True))
        lp.toggled.connect(self.win.set_reading_pauses)
        body.addWidget(lp)

        from . import sleeptimer
        body.addWidget(muted("Sleep fade  (fall asleep to the book)"))
        sf = combo([lbl for lbl, _m in sleeptimer.OPTIONS],
                   sleeptimer.label_for(getattr(self.win, "_read_fade_min", 0)),
                   self._on_read_fade)
        sf.setToolTip("Gently quieten the reading and stop after a set time, so "
                      "you can drift off mid-chapter.")
        self._w["read_fade"] = sf
        body.addWidget(sf)

        from .picker import PickerButton
        cur = self.win.narrator.voice or narration.best_voice(self.win.speech)
        vc = PickerButton(cur, lambda: narration.voice_groups(self.win.speech),
                          self.win.set_reading_voice, title="Narration voice",
                          label_fn=lambda v: narration.voice_label(v, self.win.speech),
                          win=self.win)
        self._w["read_voice"] = vc
        body.addWidget(muted("Narration voice  (★ = most realistic)"))
        body.addWidget(vc)
        lbl = narration.engine_label(self.win.speech) or "no narration"
        body.addWidget(muted(f"Engine: {lbl}"))
        body.addWidget(muted("Reading-focused by default. Press Start (left) to "
                             "add breathing visuals; for a sleep fade-out, use "
                             "Sleep mode."))
        return frame

    def _on_read_book(self, _t=None):
        bk = self._w.get("read_book")
        ids = self._w.get("read_ids") or []
        i = bk.currentIndex() if bk else -1
        if 0 <= i < len(ids):
            self.win.set_reading_book(ids[i])
        ch = self._w.get("read_chapters")
        if ch is not None:
            ch.setEnabled(bool(self.win.book_chapters()))

    def refresh_read_chapters(self):
        """Re-evaluate the Chapters button's enabled state when the book changes
        (the card may have been built before a book was loaded)."""
        ch = self._w.get("read_chapters")
        if ch is None:
            return
        try:
            ch.setEnabled(bool(self.win.book_chapters()))
        except RuntimeError:
            pass            # widget was destroyed by a workspace rebuild

    def _on_read_fade(self, label):
        from . import sleeptimer
        for lbl, m in sleeptimer.OPTIONS:
            if lbl == label:
                self.win.set_read_fade(m)
                return

    def _choose_chapter(self):
        """Searchable chapter picker -> jump the reader to the chosen chapter."""
        from .picker import choose
        chs = self.win.book_chapters()
        if not chs:
            return
        items = [(si, (f"{n}.  {title}" if title else f"Section {n}"))
                 for n, (si, title) in enumerate(chs, 1)]
        here = getattr(self.win, "_read_idx", 0)
        cur = max((si for si, _ in chs if si <= here), default=None)
        pick = choose(self.win, "Jump to a chapter", [("Chapters", items)],
                      current=cur, placeholder="Search chapters…")
        if pick is not None:
            self.win.jump_to_chapter(pick)
