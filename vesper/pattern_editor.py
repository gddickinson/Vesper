"""Pattern Editor dialog (Qt) -- create / edit custom breath patterns.

A themed QDialog that mirrors the legacy Tkinter ``pattern_editor``: a name
field plus four phase sliders (inhale / hold-full / exhale / hold-empty in
seconds), a live read-out of the total cycle length and the resulting
breaths-per-minute, and Save / Apply / Close buttons.

Save builds a :class:`BreathPattern`, persists it via ``store.save_pattern``,
registers it in the shared ``patterns.PRESETS`` (``patterns.add_pattern``),
applies it to the session and refreshes the menu + control panel.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout)

from breathsim import patterns, store
from breathsim.patterns import BreathPattern

from .widgets import LabeledSlider, card, muted

# Phase keys -> friendly labels (matches the legacy editor's order).
_FIELDS = [
    ("inhale", "Inhale"),
    ("hold_full", "Hold (full)"),
    ("exhale", "Exhale"),
    ("hold_empty", "Hold (empty)"),
]

# Slider range / resolution, roughly matching the legacy 0..20 @ 0.5s scales
# but trimmed to the requested 0..12 s window with 0.5 s steps.
_MIN, _MAX, _STEP = 0.0, 12.0, 0.5
_STEPS = int(round((_MAX - _MIN) / _STEP))   # 24 discrete 0.5 s notches


def open_pattern_editor(win):
    """Open the Pattern Editor against the running MainWindow *win*."""
    dlg = PatternEditor(win)
    dlg.exec()
    return dlg


class PatternEditor(QDialog):
    """Create or edit a custom breath pattern and apply / save it."""

    def __init__(self, win):
        super().__init__(win)
        self._win = win
        self.setWindowTitle("Pattern Editor")
        self.setStyleSheet(win.styleSheet())
        self.setMinimumWidth(360)

        outer = QVBoxLayout(self)
        title = QLabel("Pattern Editor")
        title.setObjectName("title")
        outer.addWidget(title)

        frame, body = card("")
        outer.addWidget(frame)

        cur = win.controller.pattern

        # Name field (seed from the current pattern, else a friendly default).
        name_row = QHBoxLayout()
        name_row.addWidget(muted("Name"))
        self._name = QLineEdit(getattr(cur, "name", "") or "My Pattern")
        name_row.addWidget(self._name, 1)
        body.addLayout(name_row)
        self._name.textChanged.connect(self._refresh_info)

        # Phase sliders.
        self._sliders = {}
        for key, label in _FIELDS:
            init = float(getattr(cur, key, 0.0))
            s = LabeledSlider(label, _MIN, _MAX, init, decimals=1, suffix=" s",
                              on_change=lambda _v: self._refresh_info(),
                              steps=_STEPS)
            body.addWidget(s)
            self._sliders[key] = s

        # Live cycle / breaths-per-minute read-out.
        self._info = muted("")
        body.addWidget(self._info)

        # Buttons: Apply (preview), Save (persist + register), Close.
        bar = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bar.addWidget(apply_btn)
        bar.addWidget(save_btn)
        bar.addWidget(close_btn)
        outer.addLayout(bar)

        self._refresh_info()

    # -- helpers ------------------------------------------------------------

    def _build(self) -> BreathPattern:
        """Assemble a BreathPattern from the current widget values."""
        return BreathPattern(
            (self._name.text().strip() or "My Pattern"),
            round(self._sliders["inhale"].value(), 2),
            round(self._sliders["hold_full"].value(), 2),
            round(self._sliders["exhale"].value(), 2),
            round(self._sliders["hold_empty"].value(), 2),
            "Custom pattern.",
        )

    def _refresh_info(self, *_):
        p = self._build()
        cycle = p.cycle
        bpm = 60.0 / cycle if cycle > 0 else 0.0
        self._info.setText(
            f"{p.summary()}   cycle {cycle:g}s   ~{bpm:.1f} breaths/min")

    def _apply(self):
        """Preview the pattern live without persisting it."""
        p = self._build()
        self._win.controller.change_pattern(p)
        self._refresh_info()

    def _save(self):
        """Persist, register in PRESETS, apply to the session and refresh UI."""
        p = self._build()
        store.save_pattern(dict(
            name=p.name, inhale=p.inhale, hold_full=p.hold_full,
            exhale=p.exhale, hold_empty=p.hold_empty,
            description="Custom pattern."))
        # store.save_pattern already registers it; do so explicitly too so the
        # editor's contract holds even if the store changes (idempotent).
        patterns.add_pattern(p)
        self._win.set_pattern(p.name)
        self._win.rebuild_menu()
        self._win.panel.sync()
        self.accept()
