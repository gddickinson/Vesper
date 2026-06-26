"""The lion character: a warm golden-faced lion ringed by a fluffy scalloped mane,
with small rounded ears and a soft cream muzzle -- built on the shared cute kit.
Regal but cuddly and sleepy.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FACE, _FACE_LT = "#f3c060", "#f8d488"
_MANE, _MANE_DK = "#c8821e", "#a8690f"
_MUZZLE, _NOSE = "#f6ead0", "#6b4a2e"


class Lion(B.Character):
    name = "Lion"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 7.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._body(p, cx, cy, R, a)
        self._mane(p, cx, cy, R, a)
        self._ears(p, cx, cy, R, a)
        # head
        g = QRadialGradient(cx, cy - R * 0.12, R * 1.25)
        g.setColorAt(0.0, B.qc(_FACE_LT))
        g.setColorAt(1.0, B.qc(_FACE))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.0, R)
        my = cy + R * 0.32
        p.setBrush(B.qc(_MUZZLE, 0.95))
        p.drawEllipse(QPointF(cx, my + R * 0.05), R * 0.58, R * 0.46)
        B.blush(p, cx, my - R * 0.04, R, R * 0.58, color="#f0a878",
                amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        self._whiskers(p, cx, cy, R, a, my)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.5)

    def _mane(self, p, cx, cy, R, a):
        """A ring of scalloped tufts all the way around the head, in two amber
        shades for depth -- swells gently on the in-breath."""
        n = 16
        rad = R * 1.25 * (1.0 + 0.04 * a.breath)
        # darker outer ring first, then a lighter ring nudged inwards
        for color, rr, tuft, off in (
                (_MANE_DK, rad * 1.06, R * 0.46, 0.0),
                (_MANE, rad, R * 0.42, math.pi / n)):
            p.setBrush(B.qc(color))
            for i in range(n):
                ang = off + 2.0 * math.pi * i / n
                tx = cx + math.cos(ang) * rr
                ty = cy + math.sin(ang) * rr
                p.drawEllipse(QPointF(tx, ty), tuft, tuft)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.08) * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.66, cy - R * 0.72 - perk
            p.setBrush(B.qc(_FACE))
            p.drawEllipse(QPointF(ex, ey), R * 0.3, R * 0.3)
            p.setBrush(B.qc(_MUZZLE, 0.9))
            p.drawEllipse(QPointF(ex, ey + R * 0.02), R * 0.17, R * 0.17)

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.0 * (0.95 + 0.10 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        by = cy + R * 0.55 - R * 0.05 * a.breath
        p.setBrush(B.qc(theme.blend(_FACE, _MANE, 0.35), 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_MUZZLE, 0.4))
        p.drawEllipse(QPointF(cx, by + bh * 0.52), bw * 0.22, bh * 0.4)

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my - R * 0.04
        p.setBrush(B.qc(_NOSE))
        # a soft rounded triangle nose
        p.drawEllipse(QPointF(cx, ny), R * 0.13, R * 0.1)
        p.setBrush(B.qc("#ffffff", 0.5))
        p.drawEllipse(QPointF(cx - R * 0.04, ny - R * 0.03), R * 0.03, R * 0.022)
        my0 = ny + R * 0.14
        B.pen(p, B.qc(_NOSE, 0.85), max(1.4, R * 0.026))
        p.drawPolyline(B.poly((cx, ny + R * 0.06), (cx, my0)))  # philtrum
        p.setPen(B.NOPEN)
        if a.mouth < 0.06:
            B.pen(p, B.qc(_NOSE), max(1.4, R * 0.028))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.17
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.2, R * (0.05 + 0.24 * a.mouth)
            p.setBrush(B.qc("#5a2018"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.06 + oh), ow, oh)

    def _whiskers(self, p, cx, cy, R, a, my):
        B.pen(p, B.qc("#fff6e2", 0.6), max(1.0, R * 0.012))
        for s in (-1, 1):
            wx = cx + s * R * 0.28
            for k, (dy, ln, drop) in enumerate(
                    [(-0.02, 0.7, -0.05), (0.08, 0.76, 0.05), (0.18, 0.66, 0.16)]):
                sway = math.sin(a.t * 0.9 + k) * 0.015 + a.ear * 0.03
                y0 = my + R * dy
                mid = (wx + s * R * ln * 0.5, y0 + R * (drop * 0.4 + sway))
                end = (wx + s * R * ln, y0 + R * (drop + sway))
                p.drawPolyline(B.poly((wx, y0), mid, end))
        p.setPen(B.NOPEN)
