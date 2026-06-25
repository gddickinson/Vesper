"""The sheep character: a soft fluffy lamb -- a cloud of cream wool around a calm
tan face, little floppy ears and a curl of wool on the brow. Built on the shared
cute-character kit (so it blinks, gazes and breathes like the rest).
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_WOOL, _WOOL_DK, _FACE, _EAR = "#eef0f2", "#cfd6dd", "#c9b9a6", "#b6a48f"


class Sheep(B.Character):
    name = "Sheep"

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
        self._wool(p, cx, cy - R * 0.5, R * 1.15, a, n=11)    # fluffy crown
        # face
        g = QRadialGradient(cx, cy + R * 0.05, R * 1.1)
        g.setColorAt(0.0, B.qc(theme.blend(_FACE, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_FACE))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy + R * 0.08), R * 0.82, R * 0.92)
        self._curl(p, cx, cy - R * 0.62, R, a)
        my = cy + R * 0.34
        B.blush(p, cx, my - R * 0.04, R, R * 0.52, amt=0.45 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy + R * 0.02, R * 0.3, R * 0.4, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.2)

    def _wool(self, p, cx, cy, R, a, n=11):
        for i in range(n):
            ang = math.pi * (0.04 + 0.92 * i / (n - 1))      # across the top arc
            rx, ry = -math.cos(ang), -math.sin(ang)
            bx, by = cx + rx * R * 0.92, cy + ry * R * 0.62
            r = R * (0.30 + 0.05 * math.sin(i * 1.9 + a.t * 0.6))
            p.setBrush(B.qc(_WOOL_DK, 0.9))
            p.drawEllipse(QPointF(bx, by + R * 0.04), r, r)
            p.setBrush(B.qc(theme.blend(_WOOL, "#ffffff", 0.2)))
            p.drawEllipse(QPointF(bx, by), r * 0.92, r * 0.92)

    def _body(self, p, cx, cy, R, a):
        by = cy + R * 0.5 - R * 0.05 * a.breath
        bw = R * 2.3 * (0.96 + 0.10 * a.breath)
        bh = R * 1.6 * (1.0 + a.squash)
        # a fluffy cloud body: overlapping wool bumps over a base
        p.setBrush(B.qc(_WOOL_DK, 0.9))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.8, R * 0.8)
        for i in range(7):
            f = i / 6.0
            bx = cx - bw * 0.42 + bw * 0.84 * f
            r = R * (0.42 + 0.06 * math.sin(i * 2.1))
            p.setBrush(B.qc(theme.blend(_WOOL, "#ffffff", 0.16)))
            p.drawEllipse(QPointF(bx, by + bh * 0.32), r, r)

    def _ears(self, p, cx, cy, R, a):
        droop = (0.2 - a.ear * 0.12) * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.78, cy + R * 0.1
            p.setBrush(B.qc(_EAR))
            p.save()
            p.translate(ex, ey); p.rotate(s * 38)
            p.drawEllipse(QRectF(-R * 0.16, droop, R * 0.32, R * 0.52))
            p.restore()

    def _curl(self, p, cx, cy, R, a):
        B.pen(p, B.qc(_WOOL_DK, 0.95), R * 0.12)
        rr = R * 0.16
        p.drawArc(QRectF(cx - rr, cy - rr * 0.4, rr * 2, rr * 1.6), 20 * 16, 300 * 16)
        p.setPen(B.NOPEN)

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my + R * 0.02
        p.setBrush(B.qc("#8c7a68"))
        p.drawEllipse(QPointF(cx, ny), R * 0.09, R * 0.07)
        my0 = ny + R * 0.13
        if a.mouth < 0.06:
            B.pen(p, B.qc("#8c7a68"), max(1.3, R * 0.026))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.15
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.18, R * (0.05 + 0.22 * a.mouth)
            p.setBrush(B.qc("#3a2a22"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)
