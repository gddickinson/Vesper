"""A small hourglass session timer, drawn in a corner of the view.

`draw(p, rect, frac, t, running, spin)` paints a glass hourglass with sand: the
top bulb empties and the bottom fills as ``frac`` (elapsed fraction) goes 0→1, with
a thin falling stream and a growing heap. ``spin`` (degrees) rotates it for the
flip-to-reset gesture. Pure QPainter; the host decides when/where to show it.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPen, QPolygonF

_SAND = "#d8b074"          # warm sand
_GLASS = "#9fe0e6"         # faint cyan glass (matches the avatar)


def _qc(hexs, a=1.0):
    c = QColor(hexs)
    c.setAlphaF(max(0.0, min(1.0, a)))
    return c


def _tri(*pts):
    return QPolygonF([QPointF(*p) for p in pts])


def draw(p, rect, frac, t, running=True, spin=0.0):
    """Draw the hourglass inside *rect*. frac 0..1 = elapsed (0 = full top)."""
    frac = max(0.0, min(1.0, float(frac)))
    cx = rect.x() + rect.width() / 2.0
    cy = rect.y() + rect.height() / 2.0
    hw = rect.width() * 0.29              # half-width of a bulb
    hh = rect.height() * 0.40             # half-height (top bulb / bottom bulb)
    p.save()
    p.translate(cx, cy)
    if spin:
        p.rotate(spin)
    # faint glass body
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_qc(_GLASS, 0.07))
    p.drawPolygon(_tri((-hw, -hh), (hw, -hh), (0, 0)))
    p.drawPolygon(_tri((-hw, hh), (hw, hh), (0, 0)))
    # sand
    p.setBrush(_qc(_SAND, 0.92))
    r = 1.0 - frac
    if r > 0.002:                         # top sand: triangle, apex at the neck
        ys = -r * hh
        p.drawPolygon(_tri((0, 0), (-hw * r, ys), (hw * r, ys)))
    if frac > 0.002:                      # bottom heap: trapezoid + a small peak
        yb = hh - frac * hh
        hwb = hw * (yb / hh) if hh > 0 else 0.0
        p.drawPolygon(_tri((-hw, hh), (hw, hh), (hwb, yb), (-hwb, yb)))
        peak = min(hh * 0.22, frac * hh * 0.5)
        p.drawPolygon(_tri((-hwb, yb), (hwb, yb), (0, yb - peak)))
    if running and 0.002 < frac < 0.998:  # falling stream + a few grains
        yb = hh - frac * hh
        sw = max(1.0, hw * 0.06)
        p.setBrush(_qc(_SAND, 0.8))
        p.drawRect(QRectF(-sw / 2, 0, sw, max(0.0, yb)))
        p.setBrush(_qc(_SAND, 0.98))
        for i in range(3):
            gy = ((t * 1.7 + i * 0.37) % 1.0) * max(1.0, yb)
            p.drawEllipse(QPointF(0, gy), sw * 0.7, sw * 0.7)
    # glass frame + caps
    pen = QPen(_qc(_GLASS, 0.55))
    pen.setWidthF(1.6)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(pen)
    p.drawPolygon(_tri((-hw, -hh), (hw, -hh), (0, 0)))
    p.drawPolygon(_tri((-hw, hh), (hw, hh), (0, 0)))
    cap = QPen(_qc(_GLASS, 0.7))
    cap.setWidthF(2.4)
    p.setPen(cap)
    p.drawLine(QPointF(-hw * 1.12, -hh), QPointF(hw * 1.12, -hh))
    p.drawLine(QPointF(-hw * 1.12, hh), QPointF(hw * 1.12, hh))
    p.restore()


def corner_rect(w, h):
    """Bottom-right placement for the timer: visible but out of the way."""
    bw, bh, margin = 56, 92, 20
    return QRectF(w - bw - margin, h - bh - margin, bw, bh)


def draw_corner(p, w, h, state):
    """Draw the hourglass from a ``state`` dict (or skip if falsy). Returns the
    hit QRectF for click handling, or ``None`` when nothing was drawn."""
    if not state:
        return None
    rect = corner_rect(w, h)
    draw(p, rect, state.get("frac", 0.0), state.get("t", 0.0),
         state.get("running", True), state.get("spin", 0.0))
    return rect


def hit(rect, x, y, pad=10):
    """True if (x, y) falls within *rect* (with a little padding for easy tapping)."""
    if rect is None:
        return False
    return (rect.left() - pad <= x <= rect.right() + pad
            and rect.top() - pad <= y <= rect.bottom() + pad)
