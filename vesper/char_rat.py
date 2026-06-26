"""The rat character: a soft grey-brown rat -- a larger, leaner, longer-faced
cousin of the mouse, with big almond-shaped ears, a clearly pointed snout tipped
with a pink nose, fine whiskers and a long curling tail -- built on the shared
cute-character kit.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK, _FUR_LT = "#b4ab9f", "#897f72", "#cabfb0"
_INNER, _MUZZLE, _NOSE = "#e6b6c2", "#e3dcd0", "#e29aa6"


class Rat(B.Character):
    name = "Rat"

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
        # head -- a touch taller + narrower than the mouse (longer-faced, leaner)
        g = QRadialGradient(cx, cy - R * 0.16, R * 1.32)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.26)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 0.94, R * 1.06)
        my = cy + R * 0.34
        ny = self._snout(p, cx, R, my)
        B.blush(p, cx, my - R * 0.04, R, R * 0.52, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, R, ny, a)
        self._whiskers(p, cx, R, a, ny)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.3)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.12) * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.72, cy - R * 0.74 - perk
            p.save()
            p.translate(ex, ey); p.rotate(s * 18.0)
            p.setBrush(B.qc(_FUR))                          # large almond outer
            p.drawEllipse(QPointF(0.0, 0.0), R * 0.46, R * 0.6)
            p.setBrush(B.qc(_INNER, 0.9))                   # pink inner
            p.drawEllipse(QPointF(0.0, R * 0.04), R * 0.28, R * 0.42)
            p.restore()

    def _body(self, p, cx, cy, R, a):
        bw = R * 1.86 * (0.95 + 0.10 * a.breath)            # leaner than the mouse
        bh = R * 1.72 * (1.0 + a.squash)
        by = cy + R * 0.5 - R * 0.05 * a.breath
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.68, R * 0.68)
        p.setBrush(B.qc(_MUZZLE, 0.42))                     # soft belly patch
        p.drawEllipse(QPointF(cx, by + bh * 0.54), bw * 0.22, bh * 0.4)

    def _tail(self, p, cx, cy, R, a):
        bx, by = cx - R * 0.95, cy + R * 1.55                # long, thin, curling
        x, y, d = bx, by, 2.4 + a.tail * 0.5
        pts = [(bx, by)]
        for _ in range(5):
            d += 0.82 + 0.12 * a.tail
            x -= math.cos(d) * R * 0.6
            y -= math.sin(d) * R * 0.6
            pts.append((x, y))
        B.pen(p, B.qc(_NOSE), R * 0.15)
        p.drawPolyline(B.poly(*pts))
        p.setPen(B.NOPEN)

    def _snout(self, p, cx, R, my):
        """Soft muzzle pad tapering forward/down into a pointed snout tip; returns
        the nose anchor at the very tip."""
        tipy = my + R * 0.5
        p.setBrush(B.qc(_MUZZLE, 0.94))
        p.drawEllipse(QPointF(cx, my), R * 0.5, R * 0.44)
        p.setBrush(B.qc(theme.blend(_MUZZLE, _FUR_LT, 0.22), 0.96))
        p.drawPolygon(B.poly((cx - R * 0.32, my + R * 0.02),
                             (cx + R * 0.32, my + R * 0.02),
                             (cx + R * 0.13, tipy),
                             (cx - R * 0.13, tipy)))
        p.drawEllipse(QPointF(cx, tipy - R * 0.02), R * 0.15, R * 0.13)
        return tipy

    def _nose_mouth(self, p, cx, R, ny, a):
        p.setBrush(B.qc(_NOSE))                             # pink nose at the tip
        p.drawEllipse(QPointF(cx, ny), R * 0.11, R * 0.09)
        p.setBrush(B.qc("#ffffff", 0.55))
        p.drawEllipse(QPointF(cx - R * 0.035, ny - R * 0.025), R * 0.022, R * 0.018)
        my0 = ny + R * 0.13
        if a.mouth < 0.06:
            B.pen(p, B.qc(_FUR_DK), max(1.4, R * 0.028))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.15
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.18, R * (0.05 + 0.22 * a.mouth)
            p.setBrush(B.qc("#241019"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.03 + oh), ow, oh)

    def _whiskers(self, p, cx, R, a, ny):
        B.pen(p, B.qc("#f3ece2", 0.6), max(1.0, R * 0.012))
        for s in (-1, 1):
            wx = cx + s * R * 0.14
            for k, (dy, ln, drop) in enumerate(
                    [(-0.06, 0.92, -0.08), (0.04, 1.0, 0.05), (0.14, 0.88, 0.18)]):
                sway = math.sin(a.t * 0.9 + k) * 0.015 + a.ear * 0.03
                y0 = ny + R * dy
                mid = (wx + s * R * ln * 0.5, y0 + R * (drop * 0.4 + sway))
                end = (wx + s * R * ln, y0 + R * (drop + sway))
                p.drawPolyline(B.poly((wx, y0), mid, end))
        p.setPen(B.NOPEN)
