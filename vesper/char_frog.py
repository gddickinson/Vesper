"""The frog character: a squat green frog with big eyes bulging up off the top of
its head and a wide cheerful grin. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_SKIN, _SKIN_DK, _BELLY, _DARK = "#6fb86a", "#4f9a52", "#dcefcf", "#26321f"


class Frog(B.Character):
    name = "Frog"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, scale=0.22, ypos=0.5)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 5.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        # webbed feet
        p.setBrush(B.qc(_SKIN_DK))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.95, cy + R * 0.95), R * 0.32, R * 0.16)
        # body (wide, squat) + belly
        bw = R * 1.5 * (0.96 + 0.08 * a.breath)
        bh = R * 1.25 * (1.0 + a.squash)
        g = QRadialGradient(cx, cy - R * 0.1, R * 1.6)
        g.setColorAt(0.0, B.qc(theme.blend(_SKIN, "#ffffff", 0.16)))
        g.setColorAt(1.0, B.qc(_SKIN_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy + R * 0.25), bw, bh)
        p.setBrush(B.qc(_BELLY, 0.9))
        p.drawEllipse(QPointF(cx, cy + R * 0.55), bw * 0.6, bh * 0.6)
        # eye bulges on top of the head + the cute eyes inside them
        ey = cy - R * 0.55
        eye_lift = a.bristle * R * 0.1
        for s in (-1, 1):
            p.setBrush(B.qc(_SKIN))
            p.drawEllipse(QPointF(cx + s * R * 0.5, ey - eye_lift), R * 0.46, R * 0.5)
        B.cute_eyes(p, cx, ey - eye_lift, R * 0.34, R * 0.5, a, iris=hue)
        # nostrils + wide grin
        p.setBrush(B.qc(_DARK))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.1, cy + R * 0.0), R * 0.035, R * 0.03)
        self._mouth(p, cx, cy, R, a)
        B.blush(p, cx, cy + R * 0.2, R, R * 0.7, color="#f29db1", amt=0.4 + 0.5 * a.smile)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.15)

    def _mouth(self, p, cx, cy, R, a):
        my = cy + R * 0.28
        if a.mouth > 0.06:                                   # croak: open wide
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, my), R * 0.55, R * (0.1 + 0.34 * a.mouth))
            p.setBrush(B.qc("#e7889a", 0.85))
            p.drawEllipse(QPointF(cx, my + R * 0.12), R * 0.3, R * 0.12)
        else:                                                # wide cheerful grin
            B.pen(p, B.qc(_DARK), R * 0.06)
            ww = R * (0.7 + 0.12 * a.smile)
            p.drawArc(QRectF(cx - ww, my - R * 0.4, ww * 2, R * 0.7), 200 * 16, 140 * 16)
            p.setPen(B.NOPEN)
