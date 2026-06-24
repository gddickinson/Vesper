"""The panda character: a round white panda with black ears, signature black eye
patches, and a little black nose. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_WHITE, _OFF, _BLACK = "#f2f4f7", "#dfe3ea", "#2a2e35"


class Panda(B.Character):
    name = "Panda"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        bw = R * 1.95 * (0.95 + 0.1 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        p.setBrush(B.qc(_OFF, 0.98))                          # body
        p.drawRoundedRect(QRectF(cx - bw / 2, cy + R * 0.5, bw, bh), R * 0.8, R * 0.8)
        p.setBrush(B.qc(_BLACK))                              # black arms
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * bw * 0.42, cy + R * 0.95), R * 0.28, R * 0.5)
        for s in (-1, 1):                                     # black ears
            p.drawEllipse(QPointF(cx + s * R * 0.68, cy - R * 0.8 - a.ear * R * 0.05),
                          R * 0.3, R * 0.3)
        g = QRadialGradient(cx, cy - R * 0.14, R * 1.3)       # white head
        g.setColorAt(0.0, B.qc("#ffffff")); g.setColorAt(1.0, B.qc(_WHITE))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.05, R)
        for s in (-1, 1):                                     # signature eye patches
            p.save()
            p.translate(cx + s * R * 0.42, cy - R * 0.04)
            p.rotate(s * 18)
            p.setBrush(B.qc(_BLACK))
            p.drawEllipse(QRectF(-R * 0.3, -R * 0.34, R * 0.6, R * 0.74))
            p.restore()
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.28, R * 0.42, a, iris=hue)
        my = cy + R * 0.32
        p.setBrush(B.qc(_BLACK))                              # nose
        p.drawEllipse(QPointF(cx, my), R * 0.13, R * 0.1)
        p.setBrush(B.qc("#ffffff", 0.45))
        p.drawEllipse(QPointF(cx - R * 0.04, my - R * 0.03), R * 0.035, R * 0.028)
        if a.mouth > 0.06:
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, my + R * 0.26), R * 0.13,
                          R * (0.05 + 0.2 * a.mouth))
        else:
            B.pen(p, B.qc(_BLACK), R * 0.04)
            p.drawPolyline(B.poly((cx, my + R * 0.1), (cx, my + R * 0.18)))
            r2 = R * 0.18
            span = int((150 + 40 * a.smile) * 16)
            p.drawArc(QRectF(cx - r2, my + R * 0.1, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my + R * 0.1, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.12)
