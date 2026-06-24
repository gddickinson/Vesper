"""The owl character: a round, wide-eyed slate owl with a pale facial disc, little
ear tufts, a hooked beak, feathered wings and talons. Its enormous eyes make it
the cutest blinker of the cast. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_BODY, _BODY_DK, _DISC, _BEAK, _FEET = "#6f7d9c", "#54607a", "#cdd8ea", "#f2b03c", "#efb24a"


class Owl(B.Character):
    name = "Owl"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, scale=0.225)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 9.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy + R * 0.25, R, hue, a.breath)
        bcy = cy + R * 0.95
        bw = R * 1.35 * (0.96 + 0.08 * a.breath)
        bh = R * 1.55 * (1.0 + a.squash)
        p.setBrush(B.qc(_FEET))                               # talons
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.36, bcy + bh * 0.9), R * 0.18, R * 0.1)
        self._wings(p, cx, bcy, R, bw, a)
        g = QRadialGradient(cx, bcy - bh * 0.2, bh * 1.2)     # body
        g.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.16)))
        g.setColorAt(1.0, B.qc(_BODY_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, bcy), bw, bh)
        p.setBrush(B.qc(_DISC, 0.35))                         # belly speckle patch
        p.drawEllipse(QPointF(cx, bcy + bh * 0.12), bw * 0.6, bh * 0.66)
        self._tufts(p, cx, cy, R, a)                          # ear tufts (behind head)
        gg = QRadialGradient(cx, cy - R * 0.2, R * 1.3)       # head
        gg.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.16)))
        gg.setColorAt(1.0, B.qc(_BODY))
        p.setBrush(QBrush(gg))
        p.drawEllipse(QPointF(cx, cy), R * 1.05, R)
        # facial disc: two big pale circles around the eyes
        p.setBrush(B.qc(_DISC, 0.95))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.42, cy - R * 0.02), R * 0.5, R * 0.56)
        B.cute_eyes(p, cx, cy - R * 0.02, R * 0.4, R * 0.42, a, iris=hue)  # huge eyes
        self._beak(p, cx, cy, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _tufts(self, p, cx, cy, R, a):
        lift = a.ear * R * 0.12 + a.bristle * R * 0.2
        p.setBrush(B.qc(_BODY))
        for s in (-1, 1):
            bx = cx + s * R * 0.55
            p.drawPolygon(B.poly((bx, cy - R * 0.7),
                                 (bx + s * R * 0.22, cy - R * 0.6),
                                 (bx + s * R * 0.05, cy - R * 1.0 - lift)))

    def _beak(self, p, cx, cy, R, a):
        y = cy + R * 0.16
        p.setBrush(B.qc(_BEAK))
        if a.mouth > 0.06:
            p.drawPolygon(B.poly((cx - R * 0.12, y), (cx + R * 0.12, y),
                                 (cx, y + R * (0.22 + 0.3 * a.mouth))))
        else:
            p.drawPolygon(B.poly((cx - R * 0.11, y), (cx + R * 0.11, y),
                                 (cx, y + R * 0.24)))

    def _wings(self, p, cx, bcy, R, bw, a):
        flap = (0.25 + 1.0 * a.excite) * math.sin(a.t * (2.0 + 5.0 * a.excite))
        p.setBrush(B.qc(_BODY_DK))
        for s in (-1, 1):
            p.save()
            p.translate(cx + s * bw * 0.82, bcy - R * 0.05)
            p.rotate(s * (10 + 18 * flap * s))
            p.drawEllipse(QRectF(-R * 0.26, -R * 0.4, R * 0.55, R * 1.3))
            p.restore()
