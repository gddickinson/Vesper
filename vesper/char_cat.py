"""The cat character: the friendly slate-blue tabby, now in the shared character
framework with big cute eyes, a swishing tail, ear twitches, a breathing body and
fur that bristles when startled/excited.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK, _STRIPE = "#5b8fb0", "#3f6a86", "#33566d"
_MUZZLE, _CHEST, _INNER, _NOSE = "#cfe6f2", "#bcdcec", "#caa0b4", "#e7a6b0"


class Cat(B.Character):
    name = "Cat"

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
        self._bristle(p, cx, cy, R, a)
        # head
        g = QRadialGradient(cx, cy - R * 0.12, R * 1.25)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.22)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.08, R)
        self._forehead(p, cx, cy, R)
        my = cy + R * 0.26
        p.setBrush(B.qc(_MUZZLE, 0.92))
        p.drawEllipse(QPointF(cx, my + R * 0.08), R * 0.64, R * 0.5)
        B.blush(p, cx, my - R * 0.02, R, R * 0.62, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.06, R * 0.34, R * 0.46, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        self._whiskers(p, cx, cy, R, a, my)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _tail(self, p, cx, cy, R, a):
        bx = cx + R * 1.0
        by = cy + R * 1.35
        ang = 0.6 + a.tail                                   # swishes
        ex = bx + math.cos(ang) * R * 1.5
        ey = by - math.sin(ang) * R * 1.5
        mx = bx + math.cos(ang - 0.5) * R * 0.9
        my = by - math.sin(ang - 0.5) * R * 0.9 + R * 0.2
        B.pen(p, B.qc(_FUR_DK), R * 0.28)
        path = QPointF
        p.drawPolyline(B.poly((bx, by), (mx, my), (ex, ey)))
        p.setPen(B.NOPEN)
        p.setBrush(B.qc(_FUR_DK))
        p.drawEllipse(path(ex, ey), R * 0.16, R * 0.16)      # rounded tip

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.3 * (0.95 + 0.10 * a.breath)
        bh = R * 1.7 * (1.0 + a.squash)
        by = cy + R * 0.45 - R * 0.05 * a.breath
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_CHEST, 0.5))
        p.drawEllipse(QPointF(cx, by + bh * 0.5), bw * 0.22, bh * 0.42)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.12 + a.mouth * 0.1) * R
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.62, cy - R * 0.56
            tip = (ex + s * R * 0.16, ey - R * 0.82 - perk)
            b1 = (ex - R * 0.34, ey + R * 0.02)
            b2 = (ex + R * 0.32, ey - R * 0.06)
            p.setBrush(B.qc(_FUR))
            p.drawPolygon(B.poly(tip, b1, b2))
            p.setBrush(B.qc(_INNER, 0.88))
            p.drawPolygon(B.poly((tip[0], tip[1] + R * 0.2),
                                 (ex * 0.6 + b1[0] * 0.4, ey * 0.55 + b1[1] * 0.45),
                                 (ex * 0.6 + b2[0] * 0.4, ey * 0.55 + b2[1] * 0.45)))

    def _bristle(self, p, cx, cy, R, a):
        if a.bristle < 0.05:
            return
        p.setBrush(B.qc(_FUR, 0.9))
        n = 18
        for i in range(n):
            ang = math.pi + i / (n - 1) * math.pi            # over the top rim
            rx, ry = math.cos(ang), math.sin(ang)
            base = (cx + rx * R * 1.02, cy + ry * R * 0.96)
            spk = R * (0.10 + 0.34 * a.bristle) * (0.6 + 0.4 * math.sin(i * 1.7))
            tip = (cx + rx * (R * 1.02 + spk), cy + ry * (R * 0.96 + spk))
            side = R * 0.05
            p.drawPolygon(B.poly((base[0] - ry * side, base[1] + rx * side),
                                 (base[0] + ry * side, base[1] - rx * side), tip))

    def _forehead(self, p, cx, cy, R):
        B.pen(p, B.qc(_STRIPE, 0.55), R * 0.05)
        top = cy - R * 0.62
        p.drawLine(QPointF(cx, top), QPointF(cx, top + R * 0.3))
        for s in (-1, 1):
            p.drawLine(QPointF(cx + s * R * 0.13, top),
                       QPointF(cx + s * R * 0.22, top + R * 0.27))
        p.setPen(B.NOPEN)

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my - R * 0.02
        p.setBrush(B.qc(_NOSE))
        p.drawPolygon(B.poly((cx - R * 0.1, ny), (cx + R * 0.1, ny),
                             (cx, ny + R * 0.13)))
        p.setBrush(B.qc("#ffffff", 0.55))
        p.drawEllipse(QPointF(cx - R * 0.03, ny + R * 0.02), R * 0.022, R * 0.018)
        my0 = ny + R * 0.13
        if a.mouth < 0.06:
            B.pen(p, B.qc(_FUR_DK), max(1.5, R * 0.03))
            p.drawLine(QPointF(cx, my0 - R * 0.04), QPointF(cx, my0))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.18
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.24, R * (0.05 + 0.26 * a.mouth)
            mcy = my0 + R * 0.04 + oh
            p.setBrush(B.qc("#241019"))
            p.drawEllipse(QPointF(cx, mcy), ow, oh)
            p.setBrush(B.qc(_NOSE, 0.95))
            p.drawEllipse(QPointF(cx, mcy + oh * 0.4), ow * 0.55, oh * 0.5)

    def _whiskers(self, p, cx, cy, R, a, my):
        B.pen(p, B.qc("#eaf4f8", 0.72), max(1.0, R * 0.013))
        lift = a.mouth * R * 0.06
        for s in (-1, 1):
            wx = cx + s * R * 0.26
            for k, (dy, ln, drop) in enumerate(
                    [(-0.02, 0.8, -0.05), (0.08, 0.88, 0.05), (0.18, 0.8, 0.14)]):
                sway = math.sin(a.t * 0.9 + k) * 0.015 + a.ear * 0.03
                y0 = my + R * dy - lift
                mid = (wx + s * R * ln * 0.5, y0 + R * (drop * 0.4 + sway))
                end = (wx + s * R * ln, y0 + R * (drop + sway))
                p.drawPolyline(B.poly((wx, y0), mid, end))
        p.setPen(B.NOPEN)
