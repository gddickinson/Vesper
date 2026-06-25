"""The mouse character: a tiny soft grey mouse with big round ears, a little pink
nose, fine whiskers and a curling tail -- built on the shared cute-character kit.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK = "#9aa6b4", "#6f7d8c"
_INNER, _MUZZLE, _NOSE = "#e7b8c6", "#dfe6ec", "#e7a6b0"


class Mouse(B.Character):
    name = "Mouse"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 7.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._tail(p, cx, cy, R, a)
        self._body(p, cx, cy, R, a)
        self._ears(p, cx, cy, R, a)
        # head
        g = QRadialGradient(cx, cy - R * 0.12, R * 1.25)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.24)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.02, R)
        my = cy + R * 0.3
        p.setBrush(B.qc(_MUZZLE, 0.92))
        p.drawEllipse(QPointF(cx, my + R * 0.06), R * 0.56, R * 0.46)
        B.blush(p, cx, my - R * 0.02, R, R * 0.56, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        self._whiskers(p, cx, cy, R, a, my)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.1) * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.74, cy - R * 0.66 - perk
            p.setBrush(B.qc(_FUR))
            p.drawEllipse(QPointF(ex, ey), R * 0.56, R * 0.56)
            p.setBrush(B.qc(_INNER, 0.9))
            p.drawEllipse(QPointF(ex, ey + R * 0.03), R * 0.36, R * 0.36)

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.0 * (0.95 + 0.10 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        by = cy + R * 0.5 - R * 0.05 * a.breath
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_MUZZLE, 0.45))
        p.drawEllipse(QPointF(cx, by + bh * 0.52), bw * 0.22, bh * 0.4)

    def _tail(self, p, cx, cy, R, a):
        bx, by = cx - R * 1.0, cy + R * 1.5
        ang = 2.5 + a.tail * 0.6                              # gentle curl
        mx = bx - math.cos(ang) * R * 1.0
        my = by - math.sin(ang) * R * 1.0
        ex = mx + math.cos(ang + 1.6) * R * 0.9
        ey = my - math.sin(ang + 1.6) * R * 0.9
        B.pen(p, B.qc(_NOSE), R * 0.13)
        p.drawPolyline(B.poly((bx, by), (mx, my), (ex, ey)))
        p.setPen(B.NOPEN)

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my - R * 0.0
        p.setBrush(B.qc(_NOSE))
        p.drawEllipse(QPointF(cx, ny), R * 0.1, R * 0.085)
        p.setBrush(B.qc("#ffffff", 0.55))
        p.drawEllipse(QPointF(cx - R * 0.03, ny - R * 0.02), R * 0.02, R * 0.016)
        my0 = ny + R * 0.12
        if a.mouth < 0.06:
            B.pen(p, B.qc(_FUR_DK), max(1.4, R * 0.028))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.15
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.2, R * (0.05 + 0.24 * a.mouth)
            p.setBrush(B.qc("#241019"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)

    def _whiskers(self, p, cx, cy, R, a, my):
        B.pen(p, B.qc("#eef4f8", 0.66), max(1.0, R * 0.012))
        for s in (-1, 1):
            wx = cx + s * R * 0.22
            for k, (dy, ln, drop) in enumerate(
                    [(-0.01, 0.78, -0.04), (0.08, 0.84, 0.06), (0.17, 0.74, 0.15)]):
                sway = math.sin(a.t * 0.9 + k) * 0.015 + a.ear * 0.03
                y0 = my + R * dy
                mid = (wx + s * R * ln * 0.5, y0 + R * (drop * 0.4 + sway))
                end = (wx + s * R * ln, y0 + R * (drop + sway))
                p.drawPolyline(B.poly((wx, y0), mid, end))
        p.setPen(B.NOPEN)
