"""The red panda character: a russet, fluffy red panda with a white face mask,
dark tear-marks beneath the eyes, pointed white-edged ears and a big bushy ringed
tail curled cosily round the side. Warm ginger fur over a dark belly, a small
black nose and a gentle smile. Shares the cute eyes + breathing animation; its
motion signature is a swishy tail and quick, perky ear twitches."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK = "#c4622d", "#9e4a1f"          # russet fur
_BELLY = "#3a2418"                            # dark brown chest / legs
_FACE = "#f3ece0"                             # white face mask
_TEAR = "#7a4326"                             # rusty tear-marks
_NOSE = "#241a16"


class RedPanda(B.Character):
    name = "Red Panda"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        # bushy ringed tail, curled up on one side (sways gently with the tail signal)
        tx, ty = cx + R * 1.05, cy + R * 1.05
        p.save()
        p.translate(tx, ty); p.rotate(18.0 + a.tail * 26.0)
        for i in range(5):
            p.setBrush(B.qc(_FUR_DK if i % 2 else _FUR))      # alternating rings
            p.drawEllipse(QPointF(0, i * R * 0.34), R * 0.32 - i * R * 0.02,
                          R * 0.27)
        p.restore()
        bw = R * 1.85 * (0.95 + 0.1 * a.breath)               # body
        bh = R * 1.5 * (1.0 + a.squash)
        p.setBrush(B.qc(_BELLY, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, cy + R * 0.55, bw, bh), R * 0.7, R * 0.7)
        p.setBrush(B.qc(_FUR))                                # ginger shoulders
        p.drawEllipse(QPointF(cx, cy + R * 0.7), bw * 0.5, bh * 0.3)
        for s in (-1, 1):                                     # pointed white-edged ears
            p.save()
            p.translate(cx + s * R * 0.82, cy - R * 0.78); p.rotate(s * 12.0)
            p.setBrush(B.qc(_FUR_DK))
            p.drawEllipse(QPointF(0, 0), R * 0.36, R * 0.42)
            p.setBrush(B.qc(_FACE, 0.95))
            p.drawEllipse(QPointF(0, R * 0.04), R * 0.2, R * 0.24)
            p.restore()
        g = QRadialGradient(cx, cy - R * 0.12, R * 1.4)       # head
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffd9a8", 0.25)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.16, R * 1.04)
        p.setBrush(B.qc(_FACE, 0.96))                         # white face mask
        p.drawEllipse(QPointF(cx, cy + R * 0.2), R * 0.62, R * 0.66)
        for s in (-1, 1):                                     # white cheek patches
            p.drawEllipse(QPointF(cx + s * R * 0.6, cy + R * 0.18), R * 0.3, R * 0.4)
        eyey, ew, sp = cy - R * 0.02, R * 0.28, R * 0.42
        for s in (-1, 1):                                     # rusty tear-marks
            p.setBrush(B.qc(_TEAR, 0.85))
            p.drawEllipse(QPointF(cx + s * sp, eyey + R * 0.34), R * 0.12, R * 0.26)
        B.cute_eyes(p, cx, eyey, ew, sp, a, iris=hue)
        ny = cy + R * 0.5
        p.setBrush(B.qc(_NOSE))                               # small nose
        p.drawEllipse(QPointF(cx, ny), R * 0.12, R * 0.1)
        p.setBrush(B.qc("#ffffff", 0.4))
        p.drawEllipse(QPointF(cx - R * 0.04, ny - R * 0.03), R * 0.03, R * 0.025)
        if a.mouth > 0.06:                                    # a soft yawn / speak
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, ny + R * 0.26), R * 0.12,
                          R * (0.05 + 0.2 * a.mouth))
        else:                                                 # gentle smile
            B.pen(p, B.qc(_NOSE), R * 0.045)
            r2 = R * 0.34
            span = int((150 + 30 * a.smile) * 16)
            p.drawArc(QRectF(cx - r2, ny + R * 0.04, r2, r2 * 0.7), 200 * 16, span)
            p.drawArc(QRectF(cx, ny + R * 0.04, r2, r2 * 0.7), (340 * 16) - span, span)
            p.setPen(B.NOPEN)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.16)
