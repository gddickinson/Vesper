"""The giraffe character: a gentle long-necked giraffe with warm tan fur, soft
reddish-brown patches, two knobbed ossicones and big calm eyes -- built on the
shared cute-character kit.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_LT = "#f3d27a", "#f8e0a0"
_PATCH, _MUZZLE = "#c98a4a", "#fbedc8"
_NOSE, _INNER = "#b07b46", "#f6e3b0"
_OSS, _KNOB = "#e8c87a", "#8a5a2b"


class Giraffe(B.Character):
    name = "Giraffe"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 7.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._neck(p, cx, cy, R, a)
        self._body(p, cx, cy, R, a)
        self._ossicones(p, cx, cy, R, a)
        self._ears(p, cx, cy, R, a)
        # head -- a touch taller than wide, lighter at the crown
        g = QRadialGradient(cx, cy - R * 0.22, R * 1.3)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.22)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 0.92, R * 1.04)
        self._patches(p, cx, cy, R)
        my = cy + R * 0.3
        p.setBrush(B.qc(_MUZZLE, 0.95))
        p.drawEllipse(QPointF(cx, my + R * 0.1), R * 0.5, R * 0.42)
        B.blush(p, cx, my - R * 0.02, R, R * 0.5, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.65)

    def _ossicones(self, p, cx, cy, R, a):
        sway = math.sin(a.t * 0.6) * R * 0.02
        for s in (-1, 1):
            bx, by = cx + s * R * 0.3, cy - R * 0.82
            tx, ty = cx + s * R * 0.34 + sway, cy - R * 1.45
            B.pen(p, B.qc(_OSS), R * 0.14)
            p.drawLine(QPointF(bx, by), QPointF(tx, ty))
            p.setPen(B.NOPEN)
            p.setBrush(B.qc(_KNOB))
            p.drawEllipse(QPointF(tx, ty), R * 0.16, R * 0.16)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.08) * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.8, cy - R * 0.66 - perk
            p.save()
            p.translate(ex, ey); p.rotate(s * 40)
            p.setBrush(B.qc(_FUR))
            p.drawEllipse(QPointF(0, 0), R * 0.36, R * 0.21)
            p.setBrush(B.qc(_INNER, 0.9))
            p.drawEllipse(QPointF(0, 0), R * 0.23, R * 0.12)
            p.restore()

    def _neck(self, p, cx, cy, R, a):
        poly = B.poly((cx - R * 0.42, cy + R * 0.2), (cx + R * 0.42, cy + R * 0.2),
                      (cx + R * 0.56, cy + R * 1.55), (cx - R * 0.56, cy + R * 1.55))
        g = QRadialGradient(cx, cy + R * 0.7, R * 1.4)
        g.setColorAt(0.0, B.qc(_FUR_LT))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawPolygon(poly)
        p.setBrush(B.qc(_PATCH, 0.5))
        p.drawEllipse(QPointF(cx - R * 0.16, cy + R * 0.72), R * 0.16, R * 0.18)
        p.drawEllipse(QPointF(cx + R * 0.2, cy + R * 1.08), R * 0.15, R * 0.16)

    def _body(self, p, cx, cy, R, a):
        bw = R * 1.7 * (0.95 + 0.10 * a.breath)
        bh = R * 1.2 * (1.0 + a.squash)
        by = cy + R * 1.25 - R * 0.05 * a.breath
        p.setBrush(B.qc(_FUR, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.6, R * 0.6)
        p.setBrush(B.qc(_PATCH, 0.45))
        p.drawEllipse(QPointF(cx - bw * 0.2, by + bh * 0.42), R * 0.2, R * 0.22)
        p.drawEllipse(QPointF(cx + bw * 0.22, by + bh * 0.56), R * 0.18, R * 0.2)

    def _patches(self, p, cx, cy, R):
        p.setBrush(B.qc(_PATCH, 0.5))
        for dx, dy, rx, ry in [(-0.52, -0.28, 0.2, 0.18), (0.48, -0.12, 0.18, 0.2),
                               (0.32, 0.34, 0.16, 0.15), (-0.42, 0.32, 0.15, 0.17)]:
            p.drawEllipse(QPointF(cx + dx * R, cy + dy * R), rx * R, ry * R)

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my + R * 0.04
        p.setBrush(B.qc(_NOSE, 0.75))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.14, ny), R * 0.045, R * 0.06)
        my0 = ny + R * 0.2
        if a.mouth < 0.06:
            B.pen(p, B.qc(_NOSE), max(1.4, R * 0.028))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.15
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.18, R * (0.05 + 0.22 * a.mouth)
            p.setBrush(B.qc("#5a3422"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)
