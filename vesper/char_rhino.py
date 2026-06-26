"""The rhino character: a broad, kindly, sleepy rhinoceros in soft blue-grey, with
a gentle nose horn (and a smaller second bump), small rounded ears, a wide muzzle
and small kind eyes -- built on the shared cute-character kit.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_SKIN, _SKIN_DK, _SKIN_LT = "#aab2bc", "#8b94a0", "#c4ccd4"
_HORN, _HORN_DK = "#d8d2c4", "#bfb9a8"
_MUZZLE, _INNER, _NOSE = "#bcc4cd", "#cdb3b8", "#5d6470"


class Rhino(B.Character):
    name = "Rhino"

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
        # head -- a slightly wide, blocky skull, lighter toward the top
        g = QRadialGradient(cx, cy - R * 0.18, R * 1.3)
        g.setColorAt(0.0, B.qc(theme.blend(_SKIN, "#ffffff", 0.22)))
        g.setColorAt(1.0, B.qc(_SKIN))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(QRectF(cx - R * 1.08, cy - R * 0.98,
                                 R * 2.16, R * 1.94), R * 0.7, R * 0.7)
        my = cy + R * 0.34
        p.setBrush(B.qc(_MUZZLE, 0.95))
        p.drawEllipse(QPointF(cx, my + R * 0.04), R * 0.64, R * 0.5)
        B.blush(p, cx, my - R * 0.04, R, R * 0.62, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.30, R * 0.46, a, iris=hue)
        self._horn(p, cx, cy, R, a)
        self._face(p, cx, cy, R, my, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.18)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.08) * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.78, cy - R * 0.74 - perk
            p.setBrush(B.qc(_SKIN_DK))
            p.drawEllipse(QPointF(ex, ey), R * 0.3, R * 0.36)
            p.setBrush(B.qc(_INNER, 0.85))
            p.drawEllipse(QPointF(ex, ey + R * 0.02), R * 0.17, R * 0.22)

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.35 * (0.95 + 0.10 * a.breath)
        bh = R * 1.7 * (1.0 + a.squash)
        by = cy + R * 0.52 - R * 0.05 * a.breath
        p.setBrush(B.qc(_SKIN_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.75, R * 0.75)
        p.setBrush(B.qc(_SKIN_LT, 0.4))
        p.drawEllipse(QPointF(cx, by + bh * 0.54), bw * 0.26, bh * 0.42)

    def _horn(self, p, cx, cy, R, a):
        # main nose horn: a smooth curved cone rising from the top of the muzzle
        by, ty, hw = cy + R * 0.06, cy - R * 0.46, R * 0.18
        g = QRadialGradient(cx, by, R * 0.7)
        g.setColorAt(0.0, B.qc(theme.blend(_HORN, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_HORN_DK))
        p.setBrush(QBrush(g))
        span = by - ty
        p.drawPolygon(B.poly(
            (cx - hw, by),
            (cx - hw * 0.58, by - span * 0.46),
            (cx, ty),
            (cx + hw * 0.58, by - span * 0.46),
            (cx + hw, by)))
        p.setBrush(B.qc(_HORN_DK, 0.4))                       # soft side shade
        p.drawPolygon(B.poly((cx, by), (cx, ty),
                             (cx + hw * 0.5, by - span * 0.42), (cx + hw, by)))
        # smaller second horn-bump above the first (forehead)
        by2, ty2, hw2 = ty + R * 0.04, cy - R * 0.66, R * 0.11
        p.setBrush(B.qc(_HORN, 0.95))
        p.drawPolygon(B.poly(
            (cx - hw2, by2),
            (cx, ty2),
            (cx + hw2, by2)))

    def _face(self, p, cx, cy, R, my, a):
        # two nostril dots low on the broad muzzle
        ny = my + R * 0.08
        p.setBrush(B.qc(_NOSE, 0.9))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.18, ny), R * 0.07, R * 0.055)
        # gentle, sleepy mouth
        my0 = ny + R * 0.22
        if a.mouth < 0.06:
            B.pen(p, B.qc(_SKIN_DK), max(1.4, R * 0.03))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.2
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.22, R * (0.05 + 0.24 * a.mouth)
            p.setBrush(B.qc("#241019"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)
