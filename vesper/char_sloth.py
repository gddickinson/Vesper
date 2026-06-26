"""The sloth character: a slow, sleepy, perpetually-smiling sloth -- the perfect
mascot for a sleep app. Pale grey-tan fur, the signature dark eye patches, a soft
content smile and long arms hugging close. Shares the cute eyes + breathing
animation, and looks especially charming nodding off (the drowsy gestures).
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK = "#9d8c6e", "#7c6c50"          # warm grey-tan fur
_FACE, _STRIPE = "#e7dcc4", "#5a4b38"         # pale face mask + dark eye patches
_NOSE = "#4a3a2c"


class Sloth(B.Character):
    name = "Sloth"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        bw = R * 2.0 * (0.95 + 0.1 * a.breath)                # round body
        bh = R * 1.55 * (1.0 + a.squash)
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, cy + R * 0.52, bw, bh), R * 0.8, R * 0.8)
        p.setBrush(B.qc(theme.blend(_FACE, _FUR, 0.4), 0.55))  # paler belly
        p.drawEllipse(QPointF(cx, cy + R * 1.12), bw * 0.3, bh * 0.42)
        for s in (-1, 1):                                     # long arms hugging close
            p.setBrush(B.qc(_FUR))
            p.drawRoundedRect(QRectF(cx + s * bw * 0.30 - R * 0.16, cy + R * 0.7,
                                     R * 0.34, bh * 0.78), R * 0.17, R * 0.17)
        for s in (-1, 1):                                     # small tucked round ears
            p.setBrush(B.qc(_FUR_DK))
            p.drawEllipse(QPointF(cx + s * R * 0.78, cy - R * 0.5), R * 0.2, R * 0.2)
        g = QRadialGradient(cx, cy - R * 0.12, R * 1.35)      # head (a touch wide)
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.16)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.12, R * 1.02)
        p.setBrush(B.qc(_FACE, 0.96))                         # pale face mask
        p.drawEllipse(QPointF(cx, cy + R * 0.12), R * 0.84, R * 0.78)
        eyey, ew, sp = cy - R * 0.06, R * 0.3, R * 0.42
        for s in (-1, 1):                                     # dark eye patches (the
            p.save()                                          # signature sloth mask)
            p.translate(cx + s * sp, eyey)
            p.rotate(s * 22.0)
            p.setBrush(B.qc(_STRIPE, 0.92))
            p.drawEllipse(QPointF(0, R * 0.06), ew * 0.92, ew * 1.5)
            p.restore()
        B.cute_eyes(p, cx, eyey, ew, sp, a, iris=hue)
        ny = cy + R * 0.42
        p.setBrush(B.qc(_NOSE))                               # small soft nose
        p.drawEllipse(QPointF(cx, ny), R * 0.13, R * 0.1)
        p.setBrush(B.qc("#ffffff", 0.45))
        p.drawEllipse(QPointF(cx - R * 0.045, ny - R * 0.03), R * 0.035, R * 0.028)
        if a.mouth > 0.06:                                    # a soft yawn/speak
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, ny + R * 0.3), R * 0.13,
                          R * (0.05 + 0.2 * a.mouth))
        else:                                                 # the content sloth smile
            B.pen(p, B.qc(_FUR_DK), R * 0.05)
            r2 = R * 0.42
            span = int((150 + 30 * a.smile) * 16)
            p.drawArc(QRectF(cx - r2, ny + R * 0.02, r2, r2 * 0.7), 200 * 16, span)
            p.drawArc(QRectF(cx, ny + R * 0.02, r2, r2 * 0.7), (340 * 16) - span, span)
            p.setPen(B.NOPEN)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.12)
