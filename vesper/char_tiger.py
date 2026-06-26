"""The tiger character: a warm, sleepy little tiger with rounded ears, soft black
stripes, a white muzzle, chin and brow patches, a pink nose and fine whiskers --
built on the shared cute-character kit.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_LT, _FUR_DK = "#f59030", "#f8ad5c", "#d9772a"
_WHITE, _NOSE = "#fbeede", "#e79aa8"
_STRIPE, _INNER, _MOUTH = "#2a1d14", "#1d140d", "#6e4326"


class Tiger(B.Character):
    name = "Tiger"

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
        # head
        g = QRadialGradient(cx, cy - R * 0.12, R * 1.25)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.24)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.04, R)
        # white brow patches above the eyes
        p.setBrush(B.qc(_WHITE, 0.85))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.34, cy - R * 0.28), R * 0.2, R * 0.15)
        self._stripes(p, cx, cy, R, a)
        my = cy + R * 0.34
        # white muzzle + chin
        p.setBrush(B.qc(_WHITE, 0.96))
        p.drawEllipse(QPointF(cx, my + R * 0.04), R * 0.6, R * 0.5)
        B.blush(p, cx, my - R * 0.06, R, R * 0.62, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        self._whiskers(p, cx, cy, R, a, my)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.1) * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.7, cy - R * 0.74 - perk
            p.setBrush(B.qc(_FUR))
            p.drawEllipse(QPointF(ex, ey), R * 0.5, R * 0.5)
            p.setBrush(B.qc(_INNER, 0.88))                 # soft black inner
            p.drawEllipse(QPointF(ex, ey + R * 0.04), R * 0.34, R * 0.34)
            p.setBrush(B.qc(_WHITE, 0.92))                 # white tuft
            p.drawEllipse(QPointF(ex, ey + R * 0.08), R * 0.2, R * 0.2)

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.0 * (0.95 + 0.10 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        by = cy + R * 0.5 - R * 0.05 * a.breath
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_WHITE, 0.42))                     # soft belly
        p.drawEllipse(QPointF(cx, by + bh * 0.52), bw * 0.24, bh * 0.42)

    def _taper(self, p, x0, y0, x1, y1, wid):
        """A thin tapered stripe: wide at the base (x0,y0), narrow at the tip."""
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        p.drawPolygon(B.poly(
            (x0 + nx * wid, y0 + ny * wid),
            (x0 - nx * wid, y0 - ny * wid),
            (x1 - nx * wid * 0.2, y1 - ny * wid * 0.2),
            (x1 + nx * wid * 0.2, y1 + ny * wid * 0.2),
        ))

    def _stripes(self, p, cx, cy, R, a):
        p.setBrush(B.qc(_STRIPE, 0.8))
        # forehead stripes fanning gently upward (base -> tip, width factor)
        fore = [
            (0.00, -0.42, 0.00, -0.96, 0.085),
            (-0.26, -0.38, -0.42, -0.90, 0.072),
            (0.26, -0.38, 0.42, -0.90, 0.072),
            (-0.50, -0.24, -0.78, -0.64, 0.062),
            (0.50, -0.24, 0.78, -0.64, 0.062),
        ]
        for bx, by, tx, ty, wd in fore:
            self._taper(p, cx + bx * R, cy + by * R, cx + tx * R, cy + ty * R, R * wd)
        # a cheek stripe each side, curving down beside the muzzle
        for s in (-1, 1):
            self._taper(p, cx + s * R * 0.7, cy + R * 0.02,
                        cx + s * R * 1.02, cy + R * 0.2, R * 0.058)

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my - R * 0.06
        p.setBrush(B.qc(_NOSE))
        p.drawEllipse(QPointF(cx, ny), R * 0.13, R * 0.1)
        p.setBrush(B.qc("#ffffff", 0.5))
        p.drawEllipse(QPointF(cx - R * 0.04, ny - R * 0.025), R * 0.025, R * 0.02)
        my0 = ny + R * 0.14
        if a.mouth < 0.06:
            B.pen(p, B.qc(_MOUTH), max(1.4, R * 0.03))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.15
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.2, R * (0.05 + 0.24 * a.mouth)
            p.setBrush(B.qc("#3a1d12"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)

    def _whiskers(self, p, cx, cy, R, a, my):
        B.pen(p, B.qc(_MOUTH, 0.45), max(1.0, R * 0.012))
        for s in (-1, 1):
            wx = cx + s * R * 0.3
            for k, (dy, ln, drop) in enumerate(
                    [(-0.04, 0.84, -0.05), (0.06, 0.9, 0.05), (0.16, 0.8, 0.14)]):
                sway = math.sin(a.t * 0.9 + k) * 0.015 + a.ear * 0.03
                y0 = my + R * dy
                mid = (wx + s * R * ln * 0.5, y0 + R * (drop * 0.4 + sway))
                end = (wx + s * R * ln, y0 + R * (drop + sway))
                p.drawPolyline(B.poly((wx, y0), mid, end))
        p.setPen(B.NOPEN)
