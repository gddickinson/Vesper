"""Read mode runtime for the MainWindow (a mixin).

A dedicated reading screen: the central area keeps the face/scene visualization
and adds the read-along pane (`read_pane.ReadAlongPane`) **below** it in a vertical
splitter. Reading is narration-first -- the shared `Narrator` reads `bookreader`
units while the text follows along -- with breathing visuals and a sleep-style
fade left as opt-in extras. It coexists with the Reader dialog and the Sleep
novel option, reusing books / bookreader / narration / cast and the per-book
resume position. `_build_center` also assembles the whole central widget (kept
here so window.py stays slim).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QSplitter, QStackedWidget


class _ReadMixin:
    def _build_center(self):
        """Assemble the central area: [ face/scene stack  /  read-along pane ] | panel.
        Called from __init__ after face / viz / panel exist."""
        self.stack = QStackedWidget()
        self.stack.addWidget(self.face)             # index 0
        self.stack.addWidget(self.viz)              # index 1
        from .read_pane import ReadAlongPane
        self.read_pane = ReadAlongPane(self)
        self.read_pane.hide()                       # only shown in Read mode
        self._read_timer = QTimer(self)             # GUI-thread sentence follower
        self._read_timer.setInterval(160)
        self._read_timer.timeout.connect(self._read_follow)
        # reading state
        self._reading = False
        self._read_bid = None
        self._read_idx = 0
        self._read_speed = 1.0
        self._read_long = True
        self._read_along = True
        self._read_fade_min = 0.0       # opt-in Read sleep fade (minutes); 0 = off
        self._read_fade_t0 = 0.0        # monotonic mark when the fade was armed/started
        self._read_theme = getattr(self, "_read_theme", "Night")
        self.read_pane.set_theme(self._read_theme)
        center = QSplitter(Qt.Orientation.Vertical)
        center.addWidget(self.stack)
        center.addWidget(self.read_pane)
        center.setStretchFactor(0, 1)
        center.setStretchFactor(1, 1)
        center.setCollapsible(0, False)
        center.setCollapsible(1, True)
        self.center_split = center
        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(center)
        split.addWidget(self.panel)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 0)
        split.setChildrenCollapsible(False)
        split.setSizes([800, 400])
        self.setCentralWidget(split)

    # --- entering / leaving the Read screen --------------------------------
    def enter_read(self):
        """Show the read-along pane and load the best book to start from."""
        from breathsim import books
        bid = self._read_bid
        if not bid:                                 # prefer an in-progress book
            ip = books.in_progress()
            lib = books.list_books()
            bid = (ip[0]["id"] if ip else (lib[0]["id"] if lib else None))
        self.set_reading_book(bid)
        if self._read_along:
            self.read_pane.show()
            self.center_split.setSizes([300, 500])  # favour the text while reading

    def leave_read(self):
        self.stop_reading()
        self.read_pane.hide()

    def set_reading_book(self, bid):
        from breathsim import books, bookreader
        self._read_bid = bid
        book = books.load(bid) if bid else None
        self._read_idx = books.position(bid) if bid else 0
        pct = books.percent_read(bid) if bid else 0
        self._read_chapters = bookreader.chapters(book) if book else []
        self.read_pane.set_book(book, self._read_idx, pct)
        panel = getattr(self, "panel", None)
        if panel is not None and hasattr(panel, "refresh_read_chapters"):
            panel.refresh_read_chapters()

    def book_chapters(self):
        """Detected chapters of the book loaded in Read mode (may be []):
        ``[(sentence_index, title), ...]``. Computed once per book load."""
        return list(getattr(self, "_read_chapters", []))

    def jump_to_chapter(self, sentence_index):
        """Move the reader to a chapter's first sentence (persisting the resume
        position). If currently narrating, restart from there; otherwise just
        move the read-along highlight + scroll."""
        if not self._read_bid:
            return
        from breathsim import books
        i = max(0, int(sentence_index))
        books.set_position(self._read_bid, i)
        self._read_idx = i
        if self._reading:
            self.stop_reading()
            self.start_reading()
        else:
            self.read_pane.highlight(i)

    def set_read_along(self, on):
        self._read_along = bool(on)
        self.read_pane.setVisible(self._read_along and self.current_mode == "Read")
        if self._read_along and self.current_mode == "Read":
            self.center_split.setSizes([300, 500])

    def set_reading_speed(self, v):
        self._read_speed = float(v)
        if self._reading:
            self.narrator.speed = self._read_speed

    def set_reading_pauses(self, long_pauses):
        self._read_long = bool(long_pauses)

    def set_reading_voice(self, v):
        self.narrator.set_voice(v)
        if self._reading:                           # re-apply the voice live
            self.stop_reading()
            self.start_reading()

    def set_reading_theme(self, name):
        """Reading-comfort page theme (Night / Sepia / Day); persisted."""
        self._read_theme = name
        self.read_pane.set_theme(name)
        from breathsim import store
        store.save_settings({"reading_theme": name})

    def set_read_fade(self, minutes):
        """Opt-in Read sleep fade: gently quieten the narration and stop after N
        minutes (0 = off), so you can fall asleep to a book in the Read screen.
        Uses its own monotonic clock (Read often runs without the breath session),
        and defaults off each launch like the Sleep timer."""
        import time
        self._read_fade_min = max(0.0, float(minutes))
        self._read_fade_t0 = time.monotonic()
        if self._read_fade_min > 0:
            self.status.showMessage(
                f"Reading will fade out and stop after {int(self._read_fade_min)} "
                "min.", 4000)
        else:
            self.status.showMessage("Reading sleep fade off.", 3000)

    def _read_level(self):
        """Narration level 0..1 for the reader, following the opt-in sleep fade
        (1.0 when the fade is off or not reading)."""
        if self._read_fade_min <= 0 or not self._reading:
            return 1.0
        import time
        from . import sleeptimer
        gain, _done = sleeptimer.fade_gain(
            self._read_fade_min, time.monotonic() - self._read_fade_t0)
        return max(0.0, min(1.0, gain))

    # --- narration playback ------------------------------------------------
    def read_with_transport(self, starting):
        """In Read mode the **main transport** (the big Play / Space) also drives the
        novel narration, so the one obvious Play button reads the book -- not just the
        breathing visuals. (Reading used to start only from the read-along pane's own
        button, so pressing Play gave "just breathing".) Guides the user when no book
        is loaded yet. A no-op outside Read mode."""
        if getattr(self, "current_mode", None) != "Read":
            return
        if starting:
            if not self._read_bid:
                self.status.showMessage(
                    "No book loaded yet -- open the Books menu to add or download one.",
                    6000)
            elif not self._reading:
                self.start_reading()
        elif self._reading:
            self.stop_reading()

    def toggle_reading(self):
        self.stop_reading() if self._reading else self.start_reading()

    def start_reading(self):
        from breathsim import books, bookreader
        if not self._read_bid:
            return
        book = books.load(self._read_bid)
        if not book:
            return
        lp, pp = (700, 1600) if self._read_long else (650, 900)
        start = books.position(self._read_bid)
        units = bookreader.units(book, start=start, line_pause=lp, para_pause=pp)
        self._reading = True
        self._reader_busy = True
        self._read_idx = start
        import time
        self._read_fade_t0 = time.monotonic()       # (re)start the sleep-fade clock
        self.narrator.speed = self._read_speed
        self.narrator.pause_scale = 1.0
        self._cast = (self.build_cast(book)         # dramatized cast (or None)
                      if getattr(self, "_dramatize", False) else None)
        self.narrator.start(units, self._read_level, None, self._on_read_unit)
        self.read_pane.set_playing(True)
        self._read_timer.start()

    def _on_read_unit(self, unit):
        # narrator thread: only touch plain state + persist resume
        i = int(unit.get("sentence", 0))
        self._read_idx = i
        if self._read_bid:
            from breathsim import books
            books.set_position(self._read_bid, i)
        if getattr(self, "_cast", None):
            self.cast_annotate(unit)

    def _read_follow(self):
        if not self._reading:
            return
        self.read_pane.highlight(self._read_idx)
        if self._read_fade_min > 0:                  # opt-in sleep fade: stop at the end
            import time
            from . import sleeptimer
            _g, done = sleeptimer.fade_gain(
                self._read_fade_min, time.monotonic() - self._read_fade_t0)
            if done:
                self.stop_reading()

    def stop_reading(self):
        if not self._reading:
            return
        self._reading = False
        self._read_timer.stop()
        self.narrator.stop()
        if self._read_bid:
            from breathsim import books
            books.set_position(self._read_bid, self._read_idx)
        self._cast = None
        self._restore_cast_character()
        self.read_pane.set_playing(False)
