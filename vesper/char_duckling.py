"""The duckling character: a round fluffy yellow duckling with a wide orange bill,
a little head tuft that fluffs up when startled, stubby wings and webbed feet.
Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_BODY, _BODY_DK, _BILL, _FEET = "#f6df7a", "#e3c84e", "#f2a43c", "#ef9a3a"


class Duckling(B.Character):
    name = "Duckling"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, scale=0.205, ypos=0.42)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy + R * 0.4, R, hue, a.breath)
        bcy = cy + R * 1.0
        bw = R * 1.5 * (0.96 + 0.08 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        p.setBrush(B.qc(_FEET))                               # webbed feet
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.4, bcy + bh * 0.9), R * 0.3, R * 0.14)
        self._wings(p, cx, bcy, R, bw, a)
        g = QRadialGradient(cx, bcy - bh * 0.2, bh * 1.2)     # body
        g.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.2)))
        g.setColorAt(1.0, B.qc(_BODY_DK))
        p.setBrush(QBrush(g)); p.drawEllipse(QPointF(cx, bcy), bw, bh)
        self._tuft(p, cx, cy, R, a)
        gg = QRadialGradient(cx, cy - R * 0.2, R * 1.3)       # head
        gg.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.2)))
        gg.setColorAt(1.0, B.qc(_BODY))
        p.setBrush(QBrush(gg)); p.drawEllipse(QPointF(cx, cy), R * 1.0, R)
        B.blush(p, cx, cy + R * 0.22, R, R * 0.58, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.06, R * 0.28, R * 0.42, a, iris=hue)
        self._bill(p, cx, cy, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _tuft(self, p, cx, cy, R, a):
        up = R * (0.14 + 0.4 * a.bristle)
        p.setBrush(B.qc(_BODY_DK))
        for k in (-1, 0, 1):
            fx = cx + k * R * 0.13
            p.drawPolygon(B.poly((fx - R * 0.06, cy - R * 0.9),
                                 (fx + R * 0.06, cy - R * 0.9),
                                 (fx + k * R * 0.04, cy - R * 0.9 - up)))

    def _bill(self, p, cx, cy, R, a):
        y = cy + R * 0.2
        p.setBrush(B.qc(_BILL))
        if a.mouth > 0.06:
            p.drawEllipse(QPointF(cx, y - R * 0.02), R * 0.34, R * 0.12)   # upper
            p.setBrush(B.qc(theme.blend(_BILL, "#000000", 0.2)))
            p.drawEllipse(QPointF(cx, y + R * (0.12 + 0.18 * a.mouth)),
                          R * 0.3, R * (0.08 + 0.14 * a.mouth))
        else:
            p.drawEllipse(QPointF(cx, y + R * 0.04), R * 0.36, R * 0.18)
            B.pen(p, B.qc(theme.blend(_BILL, "#000000", 0.25)), R * 0.03)
            p.drawLine(QPointF(cx - R * 0.3, y + R * 0.04),
                       QPointF(cx + R * 0.3, y + R * 0.04))
            p.setPen(B.NOPEN)

    def _wings(self, p, cx, bcy, R, bw, a):
        flap = (0.3 + 1.4 * a.excite) * math.sin(a.t * (2.4 + 6.0 * a.excite))
        p.setBrush(B.qc(_BODY_DK, 0.92))
        for s in (-1, 1):
            p.save()
            p.translate(cx + s * bw * 0.85, bcy - R * 0.05)
            p.rotate(s * (16 + 26 * flap * s))
            p.drawEllipse(QRectF(-R * 0.2, -R * 0.24, R * 0.5, R * 0.95))
            p.restore()
