"""The pig character: a round, sleepy pink piglet with a flat round snout, floppy
forward-folding ears, rosy cheeks and a little curly tail -- built on the shared
cute-character kit.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_PINK, _PINK_DK, _PINK_LT = "#f4a6c0", "#e07ea0", "#f8c2d4"
_SNOUT, _NOSTRIL = "#ec96b4", "#7a3a52"


class Pig(B.Character):
    name = "Pig"

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
        # head
        g = QRadialGradient(cx, cy - R * 0.12, R * 1.25)
        g.setColorAt(0.0, B.qc(theme.blend(_PINK, "#ffffff", 0.26)))
        g.setColorAt(1.0, B.qc(_PINK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.04, R)
        B.blush(p, cx, cy + R * 0.18, R, R * 0.62, amt=0.85 + 0.4 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.30, R * 0.44, a, iris=hue)
        self._snout(p, cx, cy, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _ears(self, p, cx, cy, R, a):
        # floppy triangular ears that fold/point forward, tips bending down a little
        perk = (a.ear * 0.12) * R
        for s in (-1, 1):
            bx, by = cx + s * R * 0.62, cy - R * 0.72 - perk
            # outer triangle (rounded via polygon), tip drooping forward + down
            tip = (bx + s * R * 0.34, by + R * 0.5)
            p.setBrush(B.qc(_PINK_DK))
            p.drawPolygon(B.poly(
                (bx - s * R * 0.34, by - R * 0.18),
                (bx + s * R * 0.16, by - R * 0.42),
                tip,
            ))
            # soft inner fold
            p.setBrush(B.qc(_PINK_LT, 0.85))
            p.drawPolygon(B.poly(
                (bx - s * R * 0.16, by - R * 0.12),
                (bx + s * R * 0.08, by - R * 0.28),
                (tip[0] - s * R * 0.06, tip[1] - R * 0.08),
            ))

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.05 * (0.95 + 0.10 * a.breath)
        bh = R * 1.55 * (1.0 + a.squash)
        by = cy + R * 0.5 - R * 0.05 * a.breath
        p.setBrush(B.qc(_PINK_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.75, R * 0.75)
        p.setBrush(B.qc(_PINK_LT, 0.4))
        p.drawEllipse(QPointF(cx, by + bh * 0.52), bw * 0.22, bh * 0.4)

    def _tail(self, p, cx, cy, R, a):
        # a small curly tail behind the body
        bx, by = cx + R * 1.02, cy + R * 1.45
        wiggle = a.tail * 0.5 + math.sin(a.t * 0.9) * 0.2
        pts = [(bx, by)]
        for k in range(1, 8):
            ang = wiggle + k * 1.5
            rad = R * (0.18 + 0.05 * k)
            pts.append((bx + math.cos(ang) * rad * 0.6 + k * R * 0.04,
                        by - math.sin(ang) * rad * 0.55 - k * R * 0.03))
        B.pen(p, B.qc(_PINK_DK), R * 0.12)
        p.drawPolyline(B.poly(*pts))
        p.setPen(B.NOPEN)

    def _snout(self, p, cx, cy, R, a):
        # flat round snout, slightly darker pink, low on the face
        sy = cy + R * 0.28
        sw, sh = R * 0.5, R * 0.36
        g = QRadialGradient(cx, sy - sh * 0.4, sw * 1.4)
        g.setColorAt(0.0, B.qc(theme.blend(_SNOUT, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_SNOUT))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, sy), sw, sh)
        # two dark nostril dots
        p.setBrush(B.qc(_NOSTRIL))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.16, sy), R * 0.058, R * 0.085)
        # small soft mouth arc just under the snout
        my0 = sy + sh + R * 0.06
        if a.mouth < 0.06:
            B.pen(p, B.qc(_PINK_DK), max(1.4, R * 0.03))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.16
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:
            ow, oh = R * 0.18, R * (0.05 + 0.22 * a.mouth)
            p.setBrush(B.qc("#7a2c40"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)
