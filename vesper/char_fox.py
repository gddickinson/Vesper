"""The fox character: a bright orange fox with big pointed ears, a white cheek
ruff + muzzle, a little dark nose, a sly cute smile and a bushy white-tipped tail
that swishes. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK, _RUFF, _INNER, _NOSE = "#e8833a", "#c96a28", "#f6efe6", "#f3c4a2", "#2b2330"


class Fox(B.Character):
    name = "Fox"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 8.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._tail(p, cx, cy, R, a)
        self._body(p, cx, cy, R, a)
        self._ears(p, cx, cy, R, a)
        g = QRadialGradient(cx, cy - R * 0.14, R * 1.3)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.04, R)
        # white cheek ruff + muzzle (a soft chevron of white over the lower face)
        p.setBrush(B.qc(_RUFF, 0.97))
        p.drawPolygon(B.poly((cx - R * 0.9, cy + R * 0.05), (cx, cy - R * 0.1),
                             (cx + R * 0.9, cy + R * 0.05),
                             (cx + R * 0.5, cy + R * 0.95), (cx, cy + R * 0.7),
                             (cx - R * 0.5, cy + R * 0.95)))
        B.blush(p, cx, cy + R * 0.2, R, R * 0.66, amt=0.4 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.08, R * 0.32, R * 0.46, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _tail(self, p, cx, cy, R, a):
        bx, by = cx + R * 0.9, cy + R * 1.25
        ang = 0.5 + a.tail
        ex = bx + math.cos(ang) * R * 1.7
        ey = by - math.sin(ang) * R * 1.7
        B.pen(p, B.qc(_FUR_DK), R * 0.42)                     # bushy
        p.drawPolyline(B.poly((bx, by), ((bx + ex) / 2 + R * 0.2,
                                         (by + ey) / 2), (ex, ey)))
        p.setPen(B.NOPEN)
        p.setBrush(B.qc(_RUFF))                               # white tip
        p.drawEllipse(QPointF(ex, ey), R * 0.22, R * 0.22)

    def _body(self, p, cx, cy, R, a):
        bw = R * 2.0 * (0.95 + 0.1 * a.breath)
        bh = R * 1.55 * (1.0 + a.squash)
        by = cy + R * 0.5
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.6, R * 0.6)
        p.setBrush(B.qc(_RUFF, 0.5))
        p.drawEllipse(QPointF(cx, by + bh * 0.55), bw * 0.24, bh * 0.42)

    def _ears(self, p, cx, cy, R, a):
        perk = a.ear * R * 0.1
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.66, cy - R * 0.5
            tip = (ex + s * R * 0.2, ey - R * 0.95 - perk)
            p.setBrush(B.qc(_FUR))
            p.drawPolygon(B.poly(tip, (ex - R * 0.3, ey), (ex + R * 0.34, ey - R * 0.05)))
            p.setBrush(B.qc(_NOSE, 0.9))                      # dark ear tips
            p.drawPolygon(B.poly(tip, (tip[0] - s * R * 0.1, tip[1] + R * 0.22),
                                 (tip[0] + s * R * 0.06, tip[1] + R * 0.24)))
            p.setBrush(B.qc(_INNER, 0.9))
            p.drawPolygon(B.poly((tip[0], tip[1] + R * 0.28),
                                 (ex - R * 0.12, ey - R * 0.02),
                                 (ex + R * 0.16, ey - R * 0.04)))

    def _nose_mouth(self, p, cx, cy, R, a):
        ny = cy + R * 0.34
        p.setBrush(B.qc(_NOSE))
        p.drawPolygon(B.poly((cx - R * 0.09, ny), (cx + R * 0.09, ny),
                             (cx, ny + R * 0.12)))
        p.setBrush(B.qc("#ffffff", 0.5))
        p.drawEllipse(QPointF(cx - R * 0.03, ny + R * 0.01), R * 0.02, R * 0.016)
        my = ny + R * 0.12
        B.pen(p, B.qc(_FUR_DK), max(1.4, R * 0.026))
        if a.mouth > 0.06:
            p.setPen(B.NOPEN)
            p.setBrush(B.qc("#3a1f28"))
            p.drawEllipse(QPointF(cx, my + R * 0.12), R * 0.16, R * (0.06 + 0.22 * a.mouth))
        else:
            r2 = R * 0.2
            span = int((150 + 50 * a.smile) * 16)
            p.drawArc(QRectF(cx - r2, my - r2 * 0.1, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my - r2 * 0.1, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
