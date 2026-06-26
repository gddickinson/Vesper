"""The elephant character: a soft warm-grey baby elephant with big floppy fan
ears, a gently curling trunk and little cream tusks -- built on the shared
cute-character kit. Sleepy, calm and round.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_GREY, _GREY_DK, _GREY_LT = "#b4b2c0", "#928fa0", "#cccad6"
_INNER, _TUSK = "#cdbfc9", "#f3eee2"


class Elephant(B.Character):
    name = "Elephant"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 7.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._body(p, cx, cy, R, a)
        self._ears(p, cx, cy, R, a)
        # head -- radial gradient, lighter toward the top
        g = QRadialGradient(cx, cy - R * 0.18, R * 1.3)
        g.setColorAt(0.0, B.qc(theme.blend(_GREY, "#ffffff", 0.22)))
        g.setColorAt(1.0, B.qc(_GREY))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.06, R * 1.0)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.30, R * 0.46, a, iris=hue)
        B.blush(p, cx, cy + R * 0.20, R, R * 0.62, amt=0.5 + 0.5 * a.smile)
        self._tusks(p, cx, cy, R)
        tip = self._trunk(p, cx, cy, R, a)
        self._tip(p, tip, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _ears(self, p, cx, cy, R, a):
        flap = (18.0 + 4.0 * a.breath + 3.0 * a.ear)        # gentle floppy spread
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.92, cy - R * 0.06
            p.save()
            p.translate(ex, ey)
            p.rotate(s * flap)
            p.setBrush(B.qc(_GREY_DK))                       # big fan-shaped ear
            p.drawEllipse(QPointF(0.0, 0.0), R * 0.80, R * 0.98)
            p.setBrush(B.qc(_INNER, 0.85))                   # lighter inner
            p.drawEllipse(QPointF(s * R * 0.06, R * 0.05), R * 0.54, R * 0.70)
            p.restore()

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.05 * (0.95 + 0.10 * a.breath)
        bh = R * 1.55 * (1.0 + a.squash)
        by = cy + R * 0.52 - R * 0.05 * a.breath
        p.setBrush(B.qc(theme.blend(_GREY, _GREY_DK, 0.4), 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.75, R * 0.75)
        p.setBrush(B.qc(_GREY_LT, 0.40))                     # soft tummy
        p.drawEllipse(QPointF(cx, by + bh * 0.54), bw * 0.24, bh * 0.40)

    def _tusks(self, p, cx, cy, R):
        p.setBrush(B.qc(_TUSK, 0.95))
        for s in (-1, 1):
            bx, by = cx + s * R * 0.30, cy + R * 0.44       # curl inward + down
            p.drawPolygon(B.poly(
                (bx - s * R * 0.07, by),
                (bx + s * R * 0.07, by),
                (cx + s * R * 0.15, cy + R * 0.86),
            ))

    def _trunk(self, p, cx, cy, R, a):
        """Tapering trunk down the centre of the face, curling at the tip. Drawn
        as stacked ellipses along a curve that bends to one side near the end."""
        curl = 0.55 + 0.30 * math.sin(a.t * 0.7)            # the tip sways gently
        n, x0, y0 = 16, cx, cy - R * 0.02
        x = y = rad = 0.0
        for i in range(n + 1):
            t = i / n
            y = y0 + R * (0.16 + 1.06 * t)
            bend = (max(0.0, t - 0.58) / 0.42) ** 2          # straight, then curls
            x = cx + R * 0.40 * bend * curl
            rad = R * (0.27 - 0.185 * t)                     # widen-to-narrow taper
            col = theme.blend(_GREY, _GREY_DK, 0.18 + 0.5 * t)
            p.setBrush(B.qc(col))
            p.drawEllipse(QPointF(x, y), rad, rad * 1.06)
        p.setBrush(B.qc(_GREY_LT, 0.30))                     # soft top highlight
        p.drawEllipse(QPointF(cx - R * 0.05, y0 + R * 0.3), R * 0.10, R * 0.34)
        return (x, y, rad)

    def _tip(self, p, tip, R, a):
        tx, ty, trad = tip
        p.setBrush(B.qc(_GREY_DK))                           # two little nostrils
        for s in (-1, 1):
            p.drawEllipse(QPointF(tx + s * trad * 0.42, ty - trad * 0.15),
                          trad * 0.24, trad * 0.32)
        my0 = ty + trad * 0.85                               # gentle smiling mouth
        if a.mouth < 0.06:
            B.pen(p, B.qc(_GREY_DK), max(1.4, R * 0.026))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.13
            p.drawArc(QRectF(tx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(tx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.15, R * (0.05 + 0.20 * a.mouth)
            p.setBrush(B.qc("#3a2433"))
            p.drawEllipse(QPointF(tx, my0 + oh), ow, oh)
