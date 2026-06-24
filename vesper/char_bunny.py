"""The bunny character: a soft round rabbit with tall twitchy ears, a little pink
nose, two tiny front teeth and a fluffy tail. Shares the cute eyes + breathing.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK, _INNER, _NOSE = "#dfe5ee", "#c2cad9", "#f4c4d2", "#e58aa0"


class Bunny(B.Character):
    name = "Bunny"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 7.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        # tail puff + body
        p.setBrush(B.qc("#ffffff", 0.9))
        p.drawEllipse(QPointF(cx - R * 1.1, cy + R * 1.35), R * 0.3, R * 0.3)
        bw = R * 1.9 * (0.95 + 0.1 * a.breath)
        bh = R * 1.55 * (1.0 + a.squash)
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, cy + R * 0.5, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc("#ffffff", 0.5))
        p.drawEllipse(QPointF(cx, cy + R * 1.1), bw * 0.24, bh * 0.42)
        self._ears(p, cx, cy, R, a)
        g = QRadialGradient(cx, cy - R * 0.14, R * 1.3)       # head
        g.setColorAt(0.0, B.qc("#ffffff")); g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.0, R)
        B.blush(p, cx, cy + R * 0.24, R, R * 0.6, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.06, R * 0.3, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.7)               # crown is above the ears

    def _ears(self, p, cx, cy, R, a):
        twitch = a.ear * 8.0 + math.sin(a.t * 0.9) * 2.0
        for s in (-1, 1):
            p.save()
            p.translate(cx + s * R * 0.34, cy - R * 0.7)
            p.rotate(s * (8 + twitch * s) - s * a.bristle * 6)
            p.setBrush(B.qc(_FUR))
            p.drawEllipse(QRectF(-R * 0.2, -R * 1.2, R * 0.4, R * 1.3))
            p.setBrush(B.qc(_INNER, 0.9))
            p.drawEllipse(QRectF(-R * 0.11, -R * 1.05, R * 0.22, R * 1.0))
            p.restore()

    def _nose_mouth(self, p, cx, cy, R, a):
        ny = cy + R * 0.26
        p.setBrush(B.qc(_NOSE))                               # little nose
        p.drawPolygon(B.poly((cx - R * 0.08, ny), (cx + R * 0.08, ny),
                             (cx, ny + R * 0.08)))
        B.pen(p, B.qc(_FUR_DK), R * 0.03)                     # philtrum
        p.drawPolyline(B.poly((cx, ny + R * 0.08), (cx, ny + R * 0.2)))
        p.setPen(B.NOPEN)
        if a.mouth > 0.06:
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, ny + R * 0.3), R * 0.12, R * (0.05 + 0.2 * a.mouth))
        else:                                                # two tiny teeth (cute)
            p.setBrush(B.qc("#ffffff"))
            for s in (-1, 1):
                p.drawRoundedRect(QRectF(cx + s * R * 0.005 - R * 0.06 * (s > 0),
                                         ny + R * 0.22, R * 0.06, R * 0.1),
                                  R * 0.02, R * 0.02)
