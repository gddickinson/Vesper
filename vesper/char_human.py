"""Human characters (a gentle chibi style): a soft rounded head, simple shoulders
in a coloured top, hair, brows and a kind smile -- sharing the cast's big cute eyes
and breathing animation. Two come ready: Woman and Man, with different hair, skin
tone and top. Head-anchored costumes (hats, glasses, scarf...) sit on them too.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme


class _Human(B.Character):
    SKIN = "#e6b894"
    SKIN_DK = "#caa074"
    HAIR = "#3a2c22"
    TOP = "#3a6e7a"
    LONG = False                       # long hair framing + behind the shoulders
    FRINGE = "center"                  # 'center' | 'side' | 'short'

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, scale=0.205, ypos=0.45)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 6.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        if self.LONG:                                       # hair behind the shoulders
            p.setBrush(B.qc(theme.blend(self.HAIR, "#000000", 0.12)))
            p.drawEllipse(QPointF(cx, cy + R * 0.65), R * 1.15, R * 1.35)
        self._shoulders(p, cx, cy, R, a)
        p.setBrush(B.qc(self.SKIN))                          # neck
        p.drawRoundedRect(QRectF(cx - R * 0.26, cy + R * 0.55, R * 0.52, R * 0.6),
                          R * 0.2, R * 0.2)
        g = QRadialGradient(cx - R * 0.2, cy - R * 0.25, R * 1.4)   # head
        g.setColorAt(0.0, B.qc(theme.blend(self.SKIN, "#ffffff", 0.18)))
        g.setColorAt(1.0, B.qc(self.SKIN_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R * 0.9, R)
        for s in (-1, 1):                                    # ears
            p.setBrush(B.qc(self.SKIN_DK))
            p.drawEllipse(QPointF(cx + s * R * 0.88, cy + R * 0.05), R * 0.13, R * 0.18)
        self._hair_front(p, cx, cy, R, a)
        self._brows(p, cx, cy, R, a)
        B.cute_eyes(p, cx, cy - R * 0.02, R * 0.26, R * 0.4, a, iris=hue)
        self._nose_mouth(p, cx, cy, R, a)
        B.blush(p, cx, cy + R * 0.26, R, R * 0.6, amt=0.4 + 0.5 * a.smile)
        p.restore()
        return B.Head(cx, cy, R, cy - R)

    def _shoulders(self, p, cx, cy, R, a):
        sw = R * 2.3 * (0.96 + 0.08 * a.breath)
        sy = cy + R * 1.05 - R * 0.04 * a.breath
        p.setBrush(B.qc(self.TOP))
        p.drawRoundedRect(QRectF(cx - sw / 2, sy, sw, R * 1.5), R * 0.7, R * 0.7)
        p.setBrush(B.qc(theme.blend(self.TOP, "#ffffff", 0.12), 0.6))   # collar hint
        p.drawEllipse(QPointF(cx, sy + R * 0.05), R * 0.34, R * 0.2)

    def _hair_front(self, p, cx, cy, R, a):
        lift = a.bristle * R * 0.12
        p.setBrush(B.qc(self.HAIR))
        if self.LONG:                                        # side framing locks
            for s in (-1, 1):
                p.drawEllipse(QPointF(cx + s * R * 0.78, cy - R * 0.05),
                              R * 0.3, R * 0.85)
        # crown / top hair as a chord cap over the head
        p.drawChord(QRectF(cx - R * 0.96, cy - R * 1.04 - lift, R * 1.92,
                           R * 1.5), 8 * 16, 164 * 16)
        if self.FRINGE == "center":
            p.drawEllipse(QPointF(cx, cy - R * 0.5), R * 0.5, R * 0.4)
            p.setBrush(B.qc(self.SKIN, 0.0))
        elif self.FRINGE == "side":                          # a swept side fringe
            p.drawPolygon(B.poly((cx - R * 0.85, cy - R * 0.62),
                                 (cx + R * 0.5, cy - R * 0.66),
                                 (cx + R * 0.2, cy - R * 0.2),
                                 (cx - R * 0.85, cy - R * 0.3)))
        else:                                                # short: small top tuft
            p.drawEllipse(QPointF(cx + R * 0.1, cy - R * 0.62), R * 0.4, R * 0.3)

    def _brows(self, p, cx, cy, R, a):
        lift = a.smile * R * 0.04 + a.bristle * R * 0.08
        B.pen(p, B.qc(theme.blend(self.HAIR, "#000000", 0.1)), R * 0.05)
        for s in (-1, 1):
            bx = cx + s * R * 0.4
            p.drawPolyline(B.poly((bx - R * 0.18, cy - R * 0.36 - lift),
                                  (bx + R * 0.16, cy - R * 0.4 - lift)))
        p.setPen(B.NOPEN)

    def _nose_mouth(self, p, cx, cy, R, a):
        B.pen(p, B.qc(self.SKIN_DK), R * 0.045)              # soft nose
        p.drawPolyline(B.poly((cx, cy + R * 0.12), (cx + R * 0.07, cy + R * 0.24),
                              (cx - R * 0.04, cy + R * 0.26)))
        p.setPen(B.NOPEN)
        my = cy + R * 0.46
        if a.mouth > 0.06:
            p.setBrush(B.qc("#7c3b46"))
            p.drawEllipse(QPointF(cx, my), R * 0.16, R * (0.06 + 0.22 * a.mouth))
            p.setBrush(B.qc("#e7889a", 0.9))
            p.drawEllipse(QPointF(cx, my + R * 0.04 * a.mouth), R * 0.1, R * 0.06)
        else:                                               # a soft, clean smile arc
            B.pen(p, B.qc("#b05968"), R * 0.055)
            ww = R * (0.26 + 0.12 * a.smile)
            p.drawArc(QRectF(cx - ww, my - R * 0.18, ww * 2, R * 0.34),
                      200 * 16, 140 * 16)
            p.setPen(B.NOPEN)


class Woman(_Human):
    name = "Woman"
    SKIN, SKIN_DK = "#ecc09a", "#d2a376"
    HAIR = "#5b3a26"
    TOP = "#3a6e7a"
    LONG = True
    FRINGE = "side"


class Man(_Human):
    name = "Man"
    SKIN, SKIN_DK = "#bd8458", "#9c6c45"
    HAIR = "#241c18"
    TOP = "#41506b"
    LONG = False
    FRINGE = "short"
