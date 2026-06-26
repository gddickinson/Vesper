"""The koala character: a soft grey koala with big fuzzy round ears and a large
dark nose -- and, sleeping some twenty hours a day, the ideal sleep-app companion.
Pale grey fur, a paler face and chest, the signature spoon-shaped nose and a calm
content smile. Shares the cute eyes + breathing animation; especially sweet
nodding off (its motion signature yawns often and moves slowly)."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_FUR, _FUR_DK = "#9aa6b0", "#7b8792"          # soft blue-grey fur
_FACE = "#e9eef2"                             # pale face + chest
_EARFLUFF = "#f2dfe4"                         # pink-white inner-ear fluff
_NOSE = "#2b2b30"


class Koala(B.Character):
    name = "Koala"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        bw = R * 1.95 * (0.95 + 0.1 * a.breath)               # round fluffy body
        bh = R * 1.5 * (1.0 + a.squash)
        p.setBrush(B.qc(_FUR_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, cy + R * 0.55, bw, bh), R * 0.8, R * 0.8)
        p.setBrush(B.qc(_FACE, 0.5))                          # paler chest
        p.drawEllipse(QPointF(cx, cy + R * 1.12), bw * 0.3, bh * 0.42)
        for s in (-1, 1):                                     # big fuzzy round ears
            exx, eyy = cx + s * R * 0.92, cy - R * 0.62
            p.setBrush(B.qc(_FUR_DK))
            p.drawEllipse(QPointF(exx, eyy), R * 0.58, R * 0.58)
            p.setBrush(B.qc(_EARFLUFF, 0.9))                  # inner-ear fluff
            p.drawEllipse(QPointF(exx, eyy), R * 0.34, R * 0.34)
            p.setBrush(B.qc(theme.blend(_FUR, "#ffffff", 0.2)))
            p.drawEllipse(QPointF(exx, eyy), R * 0.2, R * 0.2)
        g = QRadialGradient(cx, cy - R * 0.12, R * 1.4)       # head
        g.setColorAt(0.0, B.qc(theme.blend(_FUR, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(_FUR))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 1.16, R * 1.06)
        p.setBrush(B.qc(_FACE, 0.9))                          # pale face
        p.drawEllipse(QPointF(cx, cy + R * 0.16), R * 0.86, R * 0.8)
        eyey, ew, sp = cy - R * 0.04, R * 0.29, R * 0.44
        B.cute_eyes(p, cx, eyey, ew, sp, a, iris=hue)
        ny = cy + R * 0.4                                     # the big spoon nose
        p.setBrush(B.qc(_NOSE))
        p.drawRoundedRect(QRectF(cx - R * 0.27, ny - R * 0.26, R * 0.54, R * 0.62),
                          R * 0.27, R * 0.3)
        p.setBrush(B.qc("#ffffff", 0.4))                     # nose sheen
        p.drawEllipse(QPointF(cx - R * 0.08, ny - R * 0.1), R * 0.07, R * 0.05)
        if a.mouth > 0.06:                                    # a soft yawn / speak
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, ny + R * 0.46), R * 0.14,
                          R * (0.05 + 0.2 * a.mouth))
        else:                                                 # content koala smile
            B.pen(p, B.qc(_FUR_DK), R * 0.05)
            r2 = R * 0.4
            span = int((150 + 30 * a.smile) * 16)
            p.drawArc(QRectF(cx - r2, ny + R * 0.3, r2, r2 * 0.7), 200 * 16, span)
            p.drawArc(QRectF(cx, ny + R * 0.3, r2, r2 * 0.7), (340 * 16) - span, span)
            p.setPen(B.NOPEN)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.16)
