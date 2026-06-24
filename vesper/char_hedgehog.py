"""The hedgehog character: a little cream-faced hedgehog under a crown of soft
brown quills (they stand up taller when startled), a tiny dark nose and round
cheeks. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FACE, _FACE_DK, _SPIKE, _SPIKE_DK, _NOSE = "#e8cda6", "#cfb083", "#6f5c49", "#4f4235", "#2c2017"


class Hedgehog(B.Character):
    name = "Hedgehog"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        # spiky body (a rounded mound of quills) with cream tummy
        bw = R * 2.05 * (0.95 + 0.1 * a.breath)
        bh = R * 1.5 * (1.0 + a.squash)
        by = cy + R * 0.45
        self._spikes(p, cx, by + bh * 0.3, bw * 0.5, bh * 0.7, R, a, layer=1)
        p.setBrush(B.qc(_SPIKE_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_FACE, 0.5))
        p.drawEllipse(QPointF(cx, by + bh * 0.55), bw * 0.24, bh * 0.42)
        # the crown of quills over the top/back of the head
        self._spikes(p, cx, cy, R * 1.04, R * 1.0, R, a, layer=0)
        g = QRadialGradient(cx, cy + R * 0.05, R * 1.2)       # cream face
        g.setColorAt(0.0, B.qc(theme.blend(_FACE, "#ffffff", 0.2)))
        g.setColorAt(1.0, B.qc(_FACE_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy + R * 0.16), R * 0.78, R * 0.86)
        B.blush(p, cx, cy + R * 0.3, R, R * 0.5, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy + R * 0.04, R * 0.26, R * 0.36, a, iris=hue)
        ny = cy + R * 0.5                                     # little snout nose
        p.setBrush(B.qc(_NOSE))
        p.drawEllipse(QPointF(cx, ny), R * 0.1, R * 0.08)
        p.setBrush(B.qc("#ffffff", 0.5))
        p.drawEllipse(QPointF(cx - R * 0.03, ny - R * 0.02), R * 0.03, R * 0.025)
        if a.mouth > 0.06:
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, ny + R * 0.2), R * 0.1, R * (0.04 + 0.16 * a.mouth))
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.2)

    def _spikes(self, p, ccx, ccy, rx, ry, R, a, layer):
        col = _SPIKE if layer == 0 else _SPIKE_DK
        p.setBrush(B.qc(col, 0.97))
        n = 22
        grow = R * (0.16 + 0.34 * a.bristle)
        a0, a1 = (math.pi * 0.95, math.pi * 2.05) if layer == 0 else (math.pi, math.pi * 2.0)
        for i in range(n):
            ang = a0 + (a1 - a0) * i / (n - 1)
            rxp, ryp = math.cos(ang), math.sin(ang)
            bx, by = ccx + rxp * rx, ccy + ryp * ry
            spk = grow * (0.7 + 0.3 * math.sin(i * 1.7 + (0.0 if layer else 1.0)))
            tip = (ccx + rxp * (rx + spk), ccy + ryp * (ry + spk))
            side = R * 0.06
            p.drawPolygon(B.poly((bx - ryp * side, by + rxp * side),
                                 (bx + ryp * side, by - rxp * side), tip))
