"""The cow character: a sleepy cream-and-grey cow with a soft patch over one eye,
two short curved horns and a forelock tuft, big ears out to the sides and a gentle
pink-grey muzzle -- built on the shared cute-character kit (so it blinks, gazes and
breathes like the rest).
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_HEAD, _SHADOW = "#eef0f2", "#d6dade"
_PATCH = "#3a3a40"
_HORN, _HORN_DK = "#e6dcc4", "#cbbf9e"
_EAR_IN = "#e7b8c6"
_MUZZLE, _MUZZLE_DK = "#e8b8c0", "#d59aa6"
_NOSTRIL, _MOUTH = "#7d5660", "#6e4a54"


class Cow(B.Character):
    name = "Cow"

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
        self._horns(p, cx, cy, R, a)
        # head -- cream, lighter at the crown, a faint shadow rim for roundness
        g = QRadialGradient(cx, cy - R * 0.14, R * 1.28)
        g.setColorAt(0.0, B.qc(theme.blend(_HEAD, "#ffffff", 0.25)))
        g.setColorAt(0.78, B.qc(_HEAD))
        g.setColorAt(1.0, B.qc(_SHADOW))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.04, R)
        self._forelock(p, cx, cy, R, a)
        self._patches(p, cx, cy, R)
        my = cy + R * 0.3
        self._muzzle(p, cx, my, R)
        B.blush(p, cx, my - R * 0.02, R, R * 0.58, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, R, my, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.15)

    def _ears(self, p, cx, cy, R, a):
        perk = a.ear * 0.06 * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.96, cy - R * 0.12 - perk
            p.save()
            p.translate(ex, ey); p.rotate(s * 28)
            p.setBrush(B.qc(_SHADOW))
            p.drawEllipse(QPointF(0, 0), R * 0.42, R * 0.23)
            p.setBrush(B.qc(_EAR_IN, 0.85))
            p.drawEllipse(QPointF(0, R * 0.02), R * 0.27, R * 0.13)
            p.restore()

    def _horns(self, p, cx, cy, R, a):
        sway = math.sin(a.t * 0.5) * R * 0.015
        for s in (-1, 1):
            pts = B.poly(
                (cx + s * R * 0.20, cy - R * 0.58),
                (cx + s * R * 0.30, cy - R * 0.84),
                (cx + s * R * 0.50 + sway, cy - R * 1.02),
                (cx + s * R * 0.54, cy - R * 0.82),
                (cx + s * R * 0.42, cy - R * 0.60),
            )
            g = QRadialGradient(cx + s * R * 0.32, cy - R * 0.72, R * 0.5)
            g.setColorAt(0.0, B.qc(_HORN))
            g.setColorAt(1.0, B.qc(_HORN_DK))
            p.setBrush(QBrush(g))
            p.drawPolygon(pts)
            p.setBrush(B.qc("#fffdf6", 0.5))                  # rounded glossy tip
            p.drawEllipse(QPointF(cx + s * R * 0.5 + sway, cy - R * 1.0),
                          R * 0.06, R * 0.06)

    def _forelock(self, p, cx, cy, R, a):
        wob = math.sin(a.t * 0.7) * R * 0.02
        for dx, r in [(-0.13, 0.17), (0.0, 0.21), (0.13, 0.17)]:
            bx, by = cx + dx * R + wob * dx, cy - R * 0.6
            p.setBrush(B.qc(_SHADOW, 0.9))
            p.drawEllipse(QPointF(bx, by + R * 0.03), r * R, r * R * 0.9)
            p.setBrush(B.qc(theme.blend(_HEAD, "#ffffff", 0.25)))
            p.drawEllipse(QPointF(bx, by), r * R * 0.85, r * R * 0.8)

    def _patches(self, p, cx, cy, R):
        p.setBrush(B.qc(_PATCH, 0.85))
        # the classic dark patch dabbed over one eye/ear, asymmetrically
        p.drawEllipse(QPointF(cx - R * 0.46, cy - R * 0.22), R * 0.4, R * 0.42)
        p.drawEllipse(QPointF(cx - R * 0.18, cy - R * 0.4), R * 0.24, R * 0.22)
        # a smaller patch low on the opposite cheek
        p.drawEllipse(QPointF(cx + R * 0.5, cy + R * 0.16), R * 0.26, R * 0.24)

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.05 * (0.95 + 0.10 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        by = cy + R * 0.52 - R * 0.05 * a.breath
        p.setBrush(B.qc(_SHADOW, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_PATCH, 0.5))                          # a soft chest patch
        p.drawEllipse(QPointF(cx + bw * 0.18, by + bh * 0.5), R * 0.3, R * 0.34)
        p.setBrush(B.qc(theme.blend(_HEAD, "#ffffff", 0.2), 0.6))
        p.drawEllipse(QPointF(cx - bw * 0.06, by + bh * 0.55), bw * 0.2, bh * 0.36)

    def _muzzle(self, p, cx, my, R):
        g = QRadialGradient(cx, my, R * 0.7)
        g.setColorAt(0.0, B.qc(theme.blend(_MUZZLE, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_MUZZLE_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, my + R * 0.08), R * 0.62, R * 0.5)

    def _nose_mouth(self, p, cx, R, my, a):
        ny = my
        p.setBrush(B.qc(_NOSTRIL, 0.9))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.22, ny), R * 0.08, R * 0.1)
        my0 = my + R * 0.28
        if a.mouth < 0.06:
            B.pen(p, B.qc(_MOUTH), max(1.4, R * 0.03))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.16
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.2, R * (0.05 + 0.22 * a.mouth)
            p.setBrush(B.qc("#3a1f26"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)
