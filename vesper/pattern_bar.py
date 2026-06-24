"""A small, on-theme diagram of the current breath pattern's phases.

`segments(pattern)` is pure + testable: it turns a BreathPattern's four phase
durations (inhale / hold_full / exhale / hold_empty) into the non-zero segments
with their seconds and width fractions. `PatternBar` paints them as a compact
bar tinted with the theme's per-phase hues, each labelled with its duration, and
softly highlights the live phase while a session runs. It just visualises the
numbers -- no claims.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from . import theme

_PHASES = [("inhale", "In"), ("hold_full", "Hold"),
           ("exhale", "Out"), ("hold_empty", "Hold")]


def segments(pattern):
    """[(key, label, seconds, fraction)] for the non-zero phases of *pattern*."""
    durs = [(k, lbl, float(getattr(pattern, k, 0.0))) for k, lbl in _PHASES]
    durs = [(k, lbl, s) for k, lbl, s in durs if s > 0.01]
    total = sum(s for _, _, s in durs) or 1.0
    return [(k, lbl, s, s / total) for k, lbl, s in durs]


def _fmt(s):
    return f"{int(s)}" if abs(s - round(s)) < 0.05 else f"{s:g}"


class PatternBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(44)
        self._segs = []
        self._sig = None
        self._phase = None

    def set_pattern(self, pattern):
        sig = (pattern.name, pattern.inhale, pattern.hold_full,
               pattern.exhale, pattern.hold_empty)
        if sig == self._sig:
            return
        self._sig = sig
        self._segs = segments(pattern)
        self.update()

    def set_phase(self, phase):
        if phase != self._phase:
            self._phase = phase
            self.update()

    def refresh(self, controller):
        """Convenience: update segments (if changed) + the live phase highlight."""
        self.set_pattern(controller.pattern)
        self.set_phase(controller.current_state().phase
                       if controller.running else None)

    def paintEvent(self, _e):
        if not self._segs:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        gap, barh, y = 3, 18, 3
        n = len(self._segs)
        avail = max(1.0, w - gap * (n - 1))
        f = QFont()
        f.setPointSize(9)
        x = 0.0
        for k, lbl, s, frac in self._segs:
            seg_w = frac * avail
            hue = theme.phase_hue(k)
            active = (k == self._phase)
            col = QColor(theme.glow(hue, 0.3) if active else hue)
            col.setAlphaF(0.95 if active else 0.55)
            p.setBrush(col)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(x, y, seg_w, barh), 4, 4)
            p.setPen(QColor(theme.TEXT if active else theme.MUTED))
            p.setFont(f)
            p.drawText(QRectF(x, y + barh + 1, seg_w, 16),
                       Qt.AlignmentFlag.AlignCenter, f"{lbl} {_fmt(s)}s")
            x += seg_w + gap
        p.end()
