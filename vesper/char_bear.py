"""The bear character: a round, huggable brown bear with little ears, a soft
muzzle and a dark nose. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK, _MUZZLE, _NOSE, _INNER = "#a9764f", "#855a39", "#e8d4ba", "#2c211c", "#caa074"


class Bear(B.Character):
    name = "Bear"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        bw = R * 2.0 * (0.95 + 0.1 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        p.setBrush(B.qc(_FUR_DK, 0.97))                       # body
        p.drawRoundedRect(QRectF(cx - bw / 2, cy + R * 0.5, bw, bh), R * 0.8, R * 0.8)
        p.setBrush(B.qc(_MUZZLE, 0.45))
        p.drawEllipse(QPointF(cx, cy + R * 1.1), bw * 0.26, bh * 0.42)
        for s in (-1, 1):                                     # round ears (perk a touch)
            p.setBrush(B.qc(_FUR))
            p.drawEllipse(QPointF(cx + s * R * 0.66, cy - R * 0.82 - a.ear * R * 0.06),
                          R * 0.34, R * 0.34)
            p.setBrush(B.qc(_INNER, 0.9))
            p.drawEllipse(QPointF(cx + s * R * 0.66, cy - R * 0.78), R * 0.17, R * 0.17)
        g = QRadialGradient(cx, cy - R * 0.14, R * 1.3)       # head
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.05, R)
        my = cy + R * 0.34
        p.setBrush(B.qc(_MUZZLE, 0.96))                       # muzzle
        p.drawEllipse(QPointF(cx, my + R * 0.04), R * 0.5, R * 0.4)
        B.blush(p, cx, cy + R * 0.2, R, R * 0.66, amt=0.4 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.1, R * 0.3, R * 0.44, a, iris=hue)
        p.setBrush(B.qc(_NOSE))                               # nose
        p.drawEllipse(QPointF(cx, my), R * 0.14, R * 0.1)
        p.setBrush(B.qc("#ffffff", 0.5))
        p.drawEllipse(QPointF(cx - R * 0.05, my - R * 0.03), R * 0.04, R * 0.03)
        if a.mouth > 0.06:
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, my + R * 0.28), R * 0.14,
                          R * (0.05 + 0.2 * a.mouth))
        else:
            B.pen(p, B.qc(_FUR_DK), R * 0.045)
            p.drawPolyline(B.poly((cx, my + R * 0.1), (cx, my + R * 0.2)))
            r2 = R * 0.2
            span = int((150 + 40 * a.smile) * 16)
            p.drawArc(QRectF(cx - r2, my + R * 0.12, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my + R * 0.12, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.16)
