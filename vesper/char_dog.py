"""The dog character: a warm tan pup with long floppy ears that swing as it moves,
a soft muzzle, a lolling tongue when it talks, a wagging tail (faster when excited)
and fur that ruffles up when startled. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK, _MUZZLE = "#c79a6b", "#9c7245", "#f0e2cd"
_NOSE, _TONGUE, _EARDK = "#3b2c22", "#e7889a", "#a87e4f"


class Dog(B.Character):
    name = "Dog"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 8.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._tail(p, cx, cy, R, a)
        self._body(p, cx, cy, R, a)
        self._ears(p, cx, cy, R, a)
        self._bristle(p, cx, cy, R, a)
        g = QRadialGradient(cx, cy - R * 0.14, R * 1.3)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.2)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.06, R)
        my = cy + R * 0.3
        p.setBrush(B.qc(_MUZZLE, 0.96))                      # soft muzzle
        p.drawEllipse(QPointF(cx, my + R * 0.06), R * 0.66, R * 0.5)
        B.blush(p, cx, my - R * 0.04, R, R * 0.64, amt=0.4 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.08, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _tail(self, p, cx, cy, R, a):
        bx, by = cx - R * 1.05, cy + R * 1.2
        wag = a.tail * (1.0 + a.excite)
        ang = 2.5 - wag
        ex = bx - math.cos(ang) * R * 1.2
        ey = by - math.sin(ang) * R * 1.2
        B.pen(p, B.qc(_FUR_DK), R * 0.22)
        p.drawPolyline(B.poly((bx, by), ((bx + ex) / 2, (by + ey) / 2 - R * 0.2),
                              (ex, ey)))
        p.setPen(B.NOPEN)

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.1 * (0.95 + 0.1 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        by = cy + R * 0.5
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.6, R * 0.6)
        p.setBrush(B.qc(_MUZZLE, 0.4))                       # chest fluff
        p.drawEllipse(QPointF(cx, by + bh * 0.5), bw * 0.22, bh * 0.42)

    def _ears(self, p, cx, cy, R, a):
        swing = a.sway * 14.0 + a.ear * 6.0
        p.setBrush(B.qc(_EARDK))
        for s in (-1, 1):
            p.save()
            p.translate(cx + s * R * 0.92, cy - R * 0.5)
            p.rotate(s * (18 - swing * s))                   # floppy swing
            p.drawEllipse(QRectF(-R * 0.34, -R * 0.1, R * 0.6, R * 1.5))
            p.restore()

    def _bristle(self, p, cx, cy, R, a):
        if a.bristle < 0.05:
            return
        p.setBrush(B.qc(_FUR, 0.9))
        n = 14
        for i in range(n):
            ang = math.pi * (1.1 + i / (n - 1) * 0.8)
            rx, ry = math.cos(ang), math.sin(ang)
            spk = R * (0.08 + 0.3 * a.bristle) * (0.6 + 0.4 * math.sin(i * 1.9))
            base = (cx + rx * R * 1.0, cy + ry * R * 0.95)
            tip = (cx + rx * (R + spk), cy + ry * (R * 0.95 + spk))
            side = R * 0.05
            p.drawPolygon(B.poly((base[0] - ry * side, base[1] + rx * side),
                                 (base[0] + ry * side, base[1] - rx * side), tip))

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my - R * 0.04
        if a.mouth > 0.06:                                   # lolling tongue
            ow = R * 0.16
            p.setBrush(B.qc(_TONGUE))
            p.drawRoundedRect(QRectF(cx - ow, ny + R * 0.12, ow * 2,
                                     R * (0.2 + 0.5 * a.mouth)), ow, ow)
        p.setBrush(B.qc(_NOSE))                              # nose
        p.drawEllipse(QPointF(cx, ny), R * 0.15, R * 0.12)
        p.setBrush(B.qc("#ffffff", 0.5))
        p.drawEllipse(QPointF(cx - R * 0.05, ny - R * 0.03), R * 0.04, R * 0.03)
        B.pen(p, B.qc(_FUR_DK), max(1.5, R * 0.028))
        p.drawLine(QPointF(cx, ny + R * 0.12), QPointF(cx, my + R * 0.06))
        r2 = R * 0.2
        span = int((150 + 40 * a.smile) * 16)
        p.drawArc(QRectF(cx - r2, my - r2 * 0.1, r2, r2), 205 * 16, span)
        p.drawArc(QRectF(cx, my - r2 * 0.1, r2, r2), (335 * 16) - span, span)
        p.setPen(B.NOPEN)
