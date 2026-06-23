"""Reusable themed Qt widgets for the control panel.

Small building blocks shared by every workspace card: a hairline-bordered
``card`` container, a ``LabeledSlider`` (slider + live numeric read-out) and combo
/ row helpers. Keeping these here lets the card builders in ``sections.py`` stay
declarative and short.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QSlider,
                               QVBoxLayout, QWidget)

from . import theme


def muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("muted")
    return lbl


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    """A titled, hairline-bordered section container. Returns (frame, body)."""
    frame = QFrame()
    frame.setObjectName("card")
    frame.setStyleSheet(
        f"QFrame#card {{ background: {theme.CARD}; border: 1px solid "
        f"{theme.BORDER}; border-radius: 8px; }}")
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(12, 10, 12, 12)
    outer.setSpacing(7)
    if title:
        head = QLabel(title)
        head.setStyleSheet(
            f"color: {theme.ACCENT}; font-weight: 600; background: transparent;")
        outer.addWidget(head)
    return frame, outer


def combo(items, current=None, on_change=None) -> QComboBox:
    box = QComboBox()
    box.addItems([str(i) for i in items])
    if current is not None and str(current) in [str(i) for i in items]:
        box.setCurrentText(str(current))
    if on_change is not None:
        box.activated.connect(lambda _i: on_change(box.currentText()))
    return box


def combo_row(label: str, items, current=None, on_change=None):
    """A muted label above a combo. Returns (container_widget, combo)."""
    box = combo(items, current, on_change)
    wrap = QWidget()
    lay = QVBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(3)
    lay.addWidget(muted(label))
    lay.addWidget(box)
    return wrap, box


class LabeledSlider(QWidget):
    """A label + horizontal slider + live value read-out, over a float range."""

    changed = Signal(float)

    def __init__(self, label, minv, maxv, value, decimals=2, suffix="",
                 on_change=None, steps=1000):
        super().__init__()
        self._min, self._max, self._steps = float(minv), float(maxv), int(steps)
        self._dec, self._suffix = decimals, suffix
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        head = QHBoxLayout()
        self._name = muted(label)
        self._read = QLabel("")
        self._read.setStyleSheet(f"color: {theme.TEXT}; background: transparent;")
        self._read.setAlignment(Qt.AlignmentFlag.AlignRight)
        head.addWidget(self._name)
        head.addWidget(self._read)
        lay.addLayout(head)
        self._s = QSlider(Qt.Orientation.Horizontal)
        self._s.setRange(0, self._steps)
        self._s.setValue(self._to_slider(float(value)))
        self._s.valueChanged.connect(self._on)
        lay.addWidget(self._s)
        self._cb = on_change
        self._refresh(float(value))

    def _to_slider(self, v):
        v = max(self._min, min(self._max, v))
        span = self._max - self._min or 1.0
        return int(round((v - self._min) / span * self._steps))

    def _from_slider(self, i):
        return self._min + (i / self._steps) * (self._max - self._min)

    def _on(self, i):
        v = self._from_slider(i)
        self._refresh(v)
        if self._cb:
            self._cb(v)
        self.changed.emit(v)

    def _refresh(self, v):
        self._read.setText(f"{v:.{self._dec}f}{self._suffix}")

    def value(self) -> float:
        return self._from_slider(self._s.value())

    def set_value(self, v: float):
        self._s.blockSignals(True)
        self._s.setValue(self._to_slider(float(v)))
        self._refresh(float(v))
        self._s.blockSignals(False)

    def set_caption(self, text: str):
        self._read.setText(text)
