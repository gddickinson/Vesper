"""The deer character: a gentle sleepy fawn with warm tan fur, a cream muzzle, big
tall ears, small soft antlers and a few pale fawn spots -- built on the shared
cute-character kit. Calm and drowsy, made for a bedtime app.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK, _FUR_LT = "#d8a868", "#b07e44", "#e8c898"
_MUZZLE, _INNER = "#fff4e8", "#f3d9c9"
_NOSE, _ANTLER, _SPOT = "#3a2820", "#a87a4a", "#fff4e0"


class Deer(B.Character):
    name = "Deer"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 7.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._antlers(p, cx, cy, R, a)
        self._body(p, cx, cy, R, a)
        self._ears(p, cx, cy, R, a)
        # head -- radial gradient, lighter toward the top
        g = QRadialGradient(cx, cy - R * 0.18, R * 1.3)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR_LT, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.0, R * 1.04)
        self._spots(p, cx, cy, R, a)
        my = cy + R * 0.34
        p.setBrush(B.qc(_MUZZLE, 0.95))
        p.drawEllipse(QPointF(cx, my + R * 0.06), R * 0.5, R * 0.46)
        B.blush(p, cx, my - R * 0.10, R, R * 0.52, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.5)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.12) * R
        for s in (-1, 1):
            p.save()
            p.translate(cx + s * R * 0.62, cy - R * 0.46 - perk)
            p.rotate(s * 26.0)
            p.setBrush(B.qc(_FUR))
            p.drawEllipse(QPointF(0.0, -R * 0.42), R * 0.27, R * 0.58)
            p.setBrush(B.qc(_INNER, 0.92))
            p.drawEllipse(QPointF(0.0, -R * 0.42), R * 0.15, R * 0.42)
            p.restore()

    def _antlers(self, p, cx, cy, R, a):
        B.pen(p, B.qc(_ANTLER), R * 0.085)
        for s in (-1, 1):
            base = (cx + s * R * 0.30, cy - R * 0.74)
            mid = (cx + s * R * 0.40, cy - R * 1.10)
            tip = (cx + s * R * 0.50, cy - R * 1.44)
            p.drawPolyline(B.poly(base, mid, tip))
            p.drawPolyline(B.poly(mid, (cx + s * R * 0.66, cy - R * 1.20)))
            p.drawPolyline(B.poly((cx + s * R * 0.45, cy - R * 1.27),
                                  (cx + s * R * 0.58, cy - R * 1.40)))
        p.setPen(B.NOPEN)

    def _body(self, p, cx, cy, R, a):
        bw = R * 1.9 * (0.95 + 0.10 * a.breath)
        bh = R * 1.55 * (1.0 + a.squash)
        by = cy + R * 0.52 - R * 0.05 * a.breath
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_MUZZLE, 0.42))                      # soft cream belly
        p.drawEllipse(QPointF(cx, by + bh * 0.55), bw * 0.22, bh * 0.42)

    def _spots(self, p, cx, cy, R, a):
        p.setBrush(B.qc(_SPOT, 0.5))
        for dx, dy, r in [(-0.30, -0.44, 0.07), (0.32, -0.42, 0.06),
                          (0.0, -0.56, 0.05), (-0.56, 0.04, 0.06),
                          (0.56, 0.06, 0.06)]:
            p.drawEllipse(QPointF(cx + dx * R, cy + dy * R), R * r, R * r)

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my - R * 0.06
        p.setBrush(B.qc(_NOSE))
        p.drawEllipse(QPointF(cx, ny), R * 0.13, R * 0.10)
        p.setBrush(B.qc("#ffffff", 0.5))
        p.drawEllipse(QPointF(cx - R * 0.04, ny - R * 0.03), R * 0.03, R * 0.02)
        my0 = ny + R * 0.16
        if a.mouth < 0.06:
            B.pen(p, B.qc(_FUR_DK), max(1.4, R * 0.026))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.14
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.16, R * (0.05 + 0.22 * a.mouth)
            p.setBrush(B.qc("#2a1410"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)
