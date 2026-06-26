"""The penguin character: a round, cuddly slate penguin with a pale belly, a little
orange beak + feet, flippers that flap when it's lively, and a head crest that ruffles
up when startled. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_BODY, _BODY_DK, _BELLY = "#3a5172", "#28374f", "#eaf2f8"
_BEAK, _FEET = "#f2a43c", "#ef9a3a"


class Penguin(B.Character):
    name = "Penguin"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, scale=0.205, ypos=0.40)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        waddle = math.sin(a.t * 1.05) * 2.3                  # a gentle side-to-side waddle
        p.translate(cx, cy + R * 1.9)                        # rock about the feet
        p.rotate(a.tilt * 6.0 + waddle)
        p.translate(-cx, -(cy + R * 1.9))
        B.aura(p, cx, cy + R * 0.4, R, hue, a.breath)
        bcy = cy + R * 1.05                                  # body centre
        bw = R * 1.55 * (0.96 + 0.08 * a.breath)
        bh = R * 1.85 * (1.0 + a.squash)
        # feet
        p.setBrush(B.qc(_FEET))
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.42, bcy + bh * 0.92),
                          R * 0.34, R * 0.16)
        self._flippers(p, cx, bcy, R, bw, a)
        # body (dark) + pale belly
        g = QRadialGradient(cx, bcy - bh * 0.2, bh * 1.2)
        g.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_BODY_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, bcy), bw, bh)
        p.setBrush(B.qc(_BELLY, 0.97))
        p.drawEllipse(QPointF(cx, bcy + bh * 0.08), bw * 0.66, bh * 0.78)
        # head
        gg = QRadialGradient(cx, cy - R * 0.2, R * 1.3)
        gg.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.18)))
        gg.setColorAt(1.0, B.qc(_BODY))
        p.setBrush(QBrush(gg))
        p.drawEllipse(QPointF(cx, cy), R * 1.02, R)
        self._crest(p, cx, cy, R, a)
        p.setBrush(B.qc(_BELLY, 0.96))                       # pale face patch
        p.drawEllipse(QPointF(cx, cy + R * 0.12), R * 0.74, R * 0.82)
        B.blush(p, cx, cy + R * 0.2, R, R * 0.58, amt=0.4 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.02, R * 0.3, R * 0.4, a, iris=hue)
        self._beak(p, cx, cy, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _flippers(self, p, cx, bcy, R, bw, a):
        flap = (0.3 + 1.4 * a.excite) * math.sin(a.t * (2.0 + 6.0 * a.excite))
        p.setBrush(B.qc(_BODY_DK))
        for s in (-1, 1):
            p.save()
            p.translate(cx + s * bw * 0.92, bcy - R * 0.2)
            p.rotate(s * (28 + 26 * flap * s))
            p.drawEllipse(QRectF(-R * 0.22, -R * 0.1, R * 0.44, R * 1.5))
            p.restore()

    def _crest(self, p, cx, cy, R, a):
        if a.bristle < 0.05:
            return
        p.setBrush(B.qc(_BODY_DK, 0.95))
        for i in range(5):
            fx = cx + (i - 2) * R * 0.14
            up = R * (0.12 + 0.4 * a.bristle) * (0.7 + 0.3 * math.sin(i))
            p.drawPolygon(B.poly((fx - R * 0.05, cy - R * 0.9),
                                 (fx + R * 0.05, cy - R * 0.9),
                                 (fx, cy - R * 0.9 - up)))

    def _beak(self, p, cx, cy, R, a):
        y = cy + R * 0.16
        open_amt = a.mouth
        p.setBrush(B.qc(_BEAK))
        p.drawPolygon(B.poly((cx - R * 0.18, y), (cx + R * 0.18, y),
                             (cx, y + R * 0.26)))
        if open_amt > 0.06:                                  # lower beak drops on talk
            p.setBrush(B.qc(theme.blend(_BEAK, "#000000", 0.2)))
            p.drawPolygon(B.poly((cx - R * 0.14, y + R * 0.02),
                                 (cx + R * 0.14, y + R * 0.02),
                                 (cx, y + R * (0.26 + 0.3 * open_amt))))
