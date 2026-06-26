"""The monkey character: a soft brown monkey with big round side ears, a pale tan
heart-shaped face, a gentle muzzle with little nostrils and an endearing smile --
built on the shared cute-character kit.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK, _FUR_LT = "#b07a44", "#8a5c2e", "#c89860"
_FACE, _INNER, _MUZZLE = "#f0d8b0", "#e6cb98", "#f6e6cc"
_NOSE, _NOSTRIL = "#6e4a2a", "#46301c"


class Monkey(B.Character):
    name = "Monkey"

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
        # head (radial gradient -> lighter toward the top)
        g = QRadialGradient(cx, cy - R * 0.14, R * 1.25)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.22)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.04, R)
        self._face_patch(p, cx, cy, R, a)
        my = cy + R * 0.3
        p.setBrush(B.qc(_MUZZLE, 0.95))
        p.drawEllipse(QPointF(cx, my + R * 0.04), R * 0.42, R * 0.34)
        B.blush(p, cx, my - R * 0.04, R, R * 0.5, amt=0.5 + 0.5 * a.smile)
        B.cute_eyes(p, cx, cy - R * 0.04, R * 0.33, R * 0.44, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, my, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _ears(self, p, cx, cy, R, a):
        perk = (a.ear * 0.06) * R
        for s in (-1, 1):
            ex, ey = cx + s * (R * 1.02 + perk), cy - R * 0.05
            p.setBrush(B.qc(_FUR))
            p.drawEllipse(QPointF(ex, ey), R * 0.5, R * 0.5)
            p.setBrush(B.qc(_FUR_LT, 0.85))
            p.drawEllipse(QPointF(ex, ey), R * 0.4, R * 0.4)
            p.setBrush(B.qc(_INNER, 0.95))
            p.drawEllipse(QPointF(ex, ey), R * 0.3, R * 0.32)

    def _body(self, p, cx, cy, R, a):
        bw = R * 1.9 * (0.95 + 0.10 * a.breath)
        bh = R * 1.55 * (1.0 + a.squash)
        by = cy + R * 0.52 - R * 0.05 * a.breath
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_FACE, 0.5))                          # soft tummy
        p.drawEllipse(QPointF(cx, by + bh * 0.5), bw * 0.26, bh * 0.42)

    def _face_patch(self, p, cx, cy, R, a):
        """A pale tan heart shape over the lower-middle face that the eyes +
        muzzle sit on: two rounded top lobes above a soft chin point."""
        p.setBrush(B.qc(_FACE, 0.96))
        ly = cy - R * 0.02
        for s in (-1, 1):                                    # rounded top lobes
            p.drawEllipse(QPointF(cx + s * R * 0.33, ly), R * 0.48, R * 0.48)
        p.drawPolygon(B.poly((cx - R * 0.78, ly),            # soft chin point
                             (cx + R * 0.78, ly),
                             (cx, cy + R * 0.7)))

    def _nose_mouth(self, p, cx, cy, R, my, a):
        ny = my - R * 0.02
        p.setBrush(B.qc(_NOSE, 0.85))                        # small nose
        p.drawEllipse(QPointF(cx, ny), R * 0.13, R * 0.09)
        p.setBrush(B.qc(_NOSTRIL))                           # two nostril dots
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.06, ny + R * 0.01),
                          R * 0.028, R * 0.034)
        my0 = ny + R * 0.2
        if a.mouth < 0.06:                                   # gentle closed smile
            B.pen(p, B.qc(_FUR_DK), max(1.4, R * 0.028))
            span = int((150 + 40 * a.smile) * 16)
            r2 = R * 0.16
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(B.NOPEN)
        else:                                                # small open oval
            ow, oh = R * 0.2, R * (0.05 + 0.24 * a.mouth)
            p.setBrush(B.qc("#3a1d12"))
            p.drawEllipse(QPointF(cx, my0 + R * 0.04 + oh), ow, oh)
