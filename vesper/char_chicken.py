"""The chicken character: a plump cream hen with a red comb + wattle, a little
orange beak, stubby wings that flap when lively and a fan of tail feathers.
Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_BODY, _BODY_DK, _RED, _BEAK, _FEET = "#f3ead9", "#d8cbb0", "#e0565a", "#f2b03c", "#ef9a3a"


class Chicken(B.Character):
    name = "Chicken"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, scale=0.205, ypos=0.42)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy + R * 0.4, R, hue, a.breath)
        bcy = cy + R * 1.05
        bw = R * 1.5 * (0.96 + 0.08 * a.breath)
        bh = R * 1.7 * (1.0 + a.squash)
        self._tailfeathers(p, cx, bcy, R, a)
        p.setBrush(B.qc(_FEET))                               # feet
        for s in (-1, 1):
            B.pen(p, B.qc(_FEET), R * 0.05)
            fx = cx + s * R * 0.3
            p.drawPolyline(B.poly((fx, bcy + bh * 0.85), (fx, bcy + bh * 1.02)))
            for k in (-1, 0, 1):
                p.drawPolyline(B.poly((fx, bcy + bh * 1.02),
                                      (fx + k * R * 0.12, bcy + bh * 1.12)))
            p.setPen(B.NOPEN)
        self._wings(p, cx, bcy, R, bw, a)
        g = QRadialGradient(cx, bcy - bh * 0.2, bh * 1.2)     # body
        g.setColorAt(0.0, B.qc("#ffffff"))
        g.setColorAt(1.0, B.qc(_BODY_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, bcy), bw, bh)
        peck = R * 0.08 * max(0.0, math.sin(a.t * 1.1)) ** 5  # an occasional head-peck
        hy = cy + peck
        gg = QRadialGradient(cx, hy - R * 0.2, R * 1.3)       # head (bobs to peck)
        gg.setColorAt(0.0, B.qc("#ffffff")); gg.setColorAt(1.0, B.qc(_BODY))
        p.setBrush(QBrush(gg))
        p.drawEllipse(QPointF(cx, hy), R * 0.98, R)
        self._comb(p, cx, hy, R, a)
        B.blush(p, cx, hy + R * 0.18, R, R * 0.56, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, hy - R * 0.04, R * 0.27, R * 0.4, a, iris=hue)
        self._beak(p, cx, hy, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _comb(self, p, cx, cy, R, a):
        wob = math.sin(a.t * 2.0) * R * 0.03
        p.setBrush(B.qc(_RED))
        for k in (-1, 0, 1):
            p.drawEllipse(QPointF(cx + k * R * 0.22, cy - R * 0.92 + abs(k) * R * 0.08),
                          R * 0.16, R * (0.22 + 0.04 * (1 - abs(k))))
        # wattle under the beak
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.08, cy + R * 0.5 + wob),
                          R * 0.07, R * 0.13)

    def _beak(self, p, cx, cy, R, a):
        y = cy + R * 0.18
        p.setBrush(B.qc(_BEAK))
        p.drawPolygon(B.poly((cx - R * 0.16, y), (cx + R * 0.16, y),
                             (cx, y + R * 0.2)))
        if a.mouth > 0.06:
            p.setBrush(B.qc(theme.blend(_BEAK, "#000000", 0.25)))
            p.drawPolygon(B.poly((cx - R * 0.12, y + R * 0.02),
                                 (cx + R * 0.12, y + R * 0.02),
                                 (cx, y + R * (0.2 + 0.28 * a.mouth))))

    def _wings(self, p, cx, bcy, R, bw, a):
        flap = (0.3 + 1.3 * a.excite) * math.sin(a.t * (2.2 + 6.0 * a.excite))
        p.setBrush(B.qc(_BODY_DK, 0.9))
        for s in (-1, 1):
            p.save()
            p.translate(cx + s * bw * 0.86, bcy - R * 0.1)
            p.rotate(s * (18 + 24 * flap * s))
            p.drawEllipse(QRectF(-R * 0.2, -R * 0.28, R * 0.5, R * 1.0))
            p.restore()

    def _tailfeathers(self, p, cx, bcy, R, a):
        sway = a.tail * 0.4
        for i, (ang, ln, col) in enumerate([(2.2, 1.1, _BODY_DK), (2.5, 1.35, _BODY),
                                            (2.8, 1.1, _BODY_DK)]):
            an = ang + sway
            ex = cx - R * 1.1 + math.cos(an) * R * ln
            ey = bcy - R * 0.2 - math.sin(an) * R * ln
            B.pen(p, B.qc(col), R * 0.16)
            p.drawPolyline(B.poly((cx - R * 0.9, bcy), (ex, ey)))
            p.setPen(B.NOPEN)
