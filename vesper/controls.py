"""The control panel (Qt): a workspace-driven view.

The mode bar is the primary navigation. Selecting a mode rebuilds the scrollable
body into that mode's curated set of cards (``workspaces.py`` + the card builders
in ``sections.py``). The title, mode bar, volume and transport stay pinned.
``sync`` pushes engine/controller state into the visible widgets; ``tick``
refreshes live read-outs each frame. Calls back into the MainWindow for all
actions; nothing here owns audio/logic state.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSlider, QVBoxLayout, QWidget)

from breathsim import modes

from . import workspaces
from .sections import _SectionsMixin
from .widgets import muted


class ControlPanel(_SectionsMixin, QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self._w: dict = {}            # live widget refs for the current workspace
        self.setObjectName("panel")
        self.setMinimumWidth(360)          # roomy enough for sliders + long labels
        self.setMaximumWidth(520)          # (resizable via the splitter in window.py)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 12)
        v.setSpacing(8)

        title = QLabel("Vesper")
        title.setObjectName("title")
        v.addWidget(title)
        self._head = muted("")
        self._head.setWordWrap(True)
        v.addWidget(self._head)

        v.addWidget(muted("Mode"))
        self.mode_group = QButtonGroup(self)
        grid = QHBoxLayout()
        self._mode_btns = {}
        col = QVBoxLayout()
        for i, name in enumerate(modes.names()):
            b = QPushButton(name)
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, n=name: self.win.apply_mode(n))
            self.mode_group.addButton(b)
            self._mode_btns[name] = b
            col.addWidget(b)
            if i == 2:
                grid.addLayout(col)
                col = QVBoxLayout()
        grid.addLayout(col)
        v.addLayout(grid)

        # Scrollable, per-mode body.
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        holder = QWidget()
        self._body = QVBoxLayout(holder)
        self._body.setContentsMargins(0, 4, 18, 4)   # right gap clears the scrollbar
        self._body.setSpacing(10)
        self._body.addStretch(1)
        self.scroll.setWidget(holder)
        v.addWidget(self.scroll, 1)

        # Pinned visualization toggle (face ↔ scene).
        v.addWidget(muted("Visualization"))
        vrow = QHBoxLayout()
        self._view_btns = {}
        for key, label in (("face", "Face"), ("scene", "Scene")):
            b = QPushButton(label)
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self.win.set_view(k))
            vrow.addWidget(b)
            self._view_btns[key] = b
        v.addLayout(vrow)

        # Pinned volume + transport.
        v.addWidget(muted("Master volume"))
        self.vol = QSlider(Qt.Orientation.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(int(win.user_volume * 100))
        self.vol.valueChanged.connect(lambda x: self.win.set_volume(x / 100.0))
        v.addWidget(self.vol)
        row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("accent")
        self.start_btn.clicked.connect(self.win.toggle_transport)
        reset = QPushButton("Reset")
        reset.clicked.connect(self.win.reset)
        row.addWidget(self.start_btn)
        row.addWidget(reset)
        v.addLayout(row)

    # --- workspace lifecycle ----------------------------------------------
    def build_workspace(self, name):
        """Clear and rebuild the body with this mode's cards."""
        while self._body.count():
            item = self._body.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)        # remove from display immediately
                w.deleteLater()
        self._w = {}
        spec = workspaces.get(name)
        for key in spec["cards"]:
            builder = getattr(self, f"_card_{key}", None)
            if builder is not None:
                self._body.addWidget(builder())
        self._body.addStretch(1)
        self.sync()

    def sync(self):
        """Push current engine/controller state into the visible widgets."""
        if not self.vol.isSliderDown():
            self.vol.blockSignals(True)
            self.vol.setValue(int(self.win.user_volume * 100))
            self.vol.blockSignals(False)
        bar = self._w.get("pattern_bar")
        if bar is not None:
            bar.set_pattern(self.win.controller.pattern)
        self._reflect_state()

    def _reflect_state(self):
        """Make every selection box mirror live engine/controller/narrator state.
        Runs each frame (from ``tick``) so the panel always reflects changes made
        anywhere -- the menus, a guided-program stage, a character swapping its
        voice -- not just direct panel edits. Guarded so it never fights an open
        dropdown or a slider being dragged."""
        eng = self.win.engine
        self._set_combo("pattern", self.win.controller.pattern.name)
        self._set_combo("voice_a", eng.voice_a)
        self._set_combo("voice_out", eng.voice_out or "Same as inhale")
        self._set_combo("persona", eng.persona.name)
        self._set_combo("cue_style", self.win.speech.style)
        self._set_combo("ambience", eng.slot_voice.get("ambience") or "None")
        self._set_combo("effect", eng.slot_voice.get("effects") or "None")
        self._set_combo("phrase", eng.phrase.name if eng.phrase else "None")
        if "story_voice" in self._w:                  # grouped combo -> match by id
            from breathsim import narration
            self._set_combo_data(
                "story_voice",
                self.win.narrator.voice or narration.best_voice(self.win.speech))

    def _set_combo(self, key, value):
        box = self._w.get(key)
        if box is None or value is None or box.view().isVisible():
            return                                     # skip while the popup is open
        if box.currentText() != str(value):
            box.blockSignals(True)
            box.setCurrentText(str(value))
            box.blockSignals(False)

    def _set_combo_data(self, key, value):
        """Select the item whose userData == *value* (for grouped_combo boxes)."""
        box = self._w.get(key)
        if box is None or value is None or box.view().isVisible():
            return
        for i in range(box.count()):
            if box.itemData(i) == value:
                if box.currentIndex() != i:
                    box.blockSignals(True)
                    box.setCurrentIndex(i)
                    box.blockSignals(False)
                return

    def tick(self):
        """Refresh live read-outs each frame (cheap, guarded)."""
        self._reflect_state()                        # keep all selection boxes in sync
        stage = self._w.get("prog_stage")
        if stage is not None:
            info = self.win.director.stage_info()
            if info:
                title, i, n, srem, _trem = info
                stage.setText(f"Stage {i}/{n}: {title} — {int(srem)}s left")
            else:
                stage.setText("")
        if "hold_btn" in self._w:
            self._refresh_hold()
        bar = self._w.get("pattern_bar")
        if bar is not None:
            bar.refresh(self.win.controller)         # live phase highlight + segments
        syl = self._w.get("chant_syllable")          # sing-along: current syllable
        if syl is not None:
            cur = self.win.engine.current_syllable()
            syl.setText(f"♪  {cur}" if cur else "")

    # --- reflection from the window ---------------------------------------
    def reflect_mode(self, name):
        b = self._mode_btns.get(name)
        if b:
            b.setChecked(True)
        m = modes.get(name)
        if m:
            self._head.setText(m.description)
        self.build_workspace(name)

    def reflect_running(self, running):
        self.start_btn.setText("Pause" if running else "Start")

    def reflect_view(self, name):
        for k, b in getattr(self, "_view_btns", {}).items():
            b.setChecked(k == name)
