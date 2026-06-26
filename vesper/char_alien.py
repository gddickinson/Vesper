"""The alien character: a cute, friendly little extraterrestrial -- the classic
"grey", reimagined in soothing mint-green. A smooth inverted-teardrop head with a
soft radial sheen, two big slanted almond eyes that blink + glow on the in-breath,
a tiny nose, a content little mouth and two slender antennae whose tips pulse and
sway with the breath. Calm, low-contrast and adorable for a bedtime app.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QPainterPath, QRadialGradient

from . import char_base as B
from . import theme

_SKIN, _SKIN_DK, _EYE, _MOUTH = "#8fd9a8", "#5fae7e", "#0a141c", "#2a3b44"


class Alien(B.Character):
    name = "Alien"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 5.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._antennae(p, cx, cy, R, a, hue)
        self._head(p, cx, cy, R, hue)
        self._eyes(p, cx, cy, R, a, hue)
        self._nose_mouth(p, cx, cy, R, a)
        B.blush(p, cx, cy + R * 0.42, R, R * 0.62,
                color="#7fe0bb", amt=0.45 + 0.4 * a.smile)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.65)          # crown above the antennae

    def _head(self, p, cx, cy, R, hue):
        skin = theme.blend(_SKIN, hue, 0.12)
        skin_dk = theme.blend(_SKIN_DK, hue, 0.10)
        # inverted-teardrop: broad rounded crown narrowing to a small soft chin
        path = QPainterPath(QPointF(cx, cy - R * 1.05))
        path.cubicTo(QPointF(cx + R * 1.18, cy - R * 0.95),
                     QPointF(cx + R * 0.92, cy + R * 0.55),
                     QPointF(cx, cy + R * 1.12))
        path.cubicTo(QPointF(cx - R * 0.92, cy + R * 0.55),
                     QPointF(cx - R * 1.18, cy - R * 0.95),
                     QPointF(cx, cy - R * 1.05))
        g = QRadialGradient(cx - R * 0.35, cy - R * 0.55, R * 1.95)
        g.setColorAt(0.0, B.qc(theme.blend(skin, "#ffffff", 0.40)))
        g.setColorAt(0.62, B.qc(skin))
        g.setColorAt(1.0, B.qc(skin_dk))
        p.setBrush(QBrush(g)); p.setPen(B.NOPEN)
        p.drawPath(path)
        p.setBrush(B.qc("#ffffff", 0.12))                 # soft top-left sheen
        p.drawEllipse(QPointF(cx - R * 0.36, cy - R * 0.5), R * 0.3, R * 0.42)

    def _antennae(self, p, cx, cy, R, a, hue):
        skin_dk = theme.blend(_SKIN_DK, hue, 0.10)
        for s in (-1, 1):
            bx, by = cx + s * R * 0.3, cy - R * 0.92
            wobble = math.sin(a.t * 1.3 + s) * R * 0.07 * (1 + 2 * a.excite)
            tipx = cx + s * R * 0.52 + wobble + a.sway * R * 0.6
            tipy = cy - R * 1.5 - R * 0.06 * a.breath
            B.pen(p, B.qc(skin_dk), R * 0.055)             # slender stalk
            stalk = QPainterPath(QPointF(bx, by))
            stalk.quadTo(QPointF(bx + s * R * 0.12, cy - R * 1.28),
                         QPointF(tipx, tipy))
            p.drawPath(stalk)
            p.setPen(B.NOPEN)
            rad = R * (0.12 + 0.06 * a.breath)             # glowing pulsing bulb
            gl = QRadialGradient(tipx, tipy, rad * 2.4)
            gl.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.5), 0.9))
            gl.setColorAt(0.5, B.qc(hue, 0.45 + 0.4 * a.breath))
            gl.setColorAt(1.0, B.qc(hue, 0.0))
            p.setBrush(QBrush(gl))
            p.drawEllipse(QPointF(tipx, tipy), rad * 2.4, rad * 2.4)
            p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.6), 0.92))
            p.drawEllipse(QPointF(tipx, tipy), rad, rad)

    def _eyes(self, p, cx, cy, R, a, hue):
        open_amt = 1.0 - a.blink
        eyey = cy - R * 0.04
        gx, gy = a.gaze
        for s in (-1, 1):
            ex = cx + s * R * 0.46
            ew = R * 0.33
            eh = R * 0.6 * (0.05 + 0.95 * open_amt)        # blink squashes height
            p.save()
            p.translate(ex, eyey); p.rotate(s * 18)        # iconic outward slant
            p.setPen(B.NOPEN)
            gl = QRadialGradient(0, 0, ew * 2.0)           # inhale glow
            gl.setColorAt(0.0, B.qc(hue, 0.14 + 0.3 * a.breath))
            gl.setColorAt(1.0, B.qc(hue, 0.0))
            p.setBrush(QBrush(gl))
            p.drawEllipse(QPointF(0, 0), ew * 2.0, ew * 2.0)
            p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.2), 0.55))   # faint rim
            p.drawEllipse(QPointF(0, 0), ew * 1.12, eh * 1.08)
            p.setBrush(B.qc(_EYE))                         # almost-black almond
            p.drawEllipse(QPointF(0, 0), ew, eh)
            p.restore()
            if open_amt > 0.2:                             # catchlights drift w/ gaze
                lx = ex + gx * ew * 0.7 - s * ew * 0.28
                ly = eyey + gy * eh * 0.6 - eh * 0.26
                p.setBrush(B.qc("#ffffff", 0.92))
                p.drawEllipse(QPointF(lx, ly), ew * 0.22, ew * 0.26)
                p.setBrush(B.qc("#ffffff", 0.55))          # small secondary sparkle
                p.drawEllipse(QPointF(lx + ew * 0.3, ly + eh * 0.45),
                              ew * 0.1, ew * 0.1)

    def _nose_mouth(self, p, cx, cy, R, a):
        p.setPen(B.NOPEN)
        p.setBrush(B.qc(_SKIN_DK, 0.85))                   # two tiny nostril dots
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.09, cy + R * 0.4),
                          R * 0.032, R * 0.026)
        my = cy + R * 0.64
        if a.mouth > 0.06:                                 # opens a little speaking
            p.setBrush(B.qc(_MOUTH))
            p.drawEllipse(QPointF(cx, my), R * 0.15, R * (0.04 + 0.18 * a.mouth))
            p.setBrush(B.qc("#7fe0bb", 0.5))
            p.drawEllipse(QPointF(cx, my + R * 0.04), R * 0.08, R * 0.04)
        else:                                              # content upward curve
            B.pen(p, B.qc(_MOUTH, 0.85), R * 0.05)
            ww = R * (0.2 + 0.12 * a.smile)
            dip = R * (0.05 + 0.14 * a.smile)
            p.drawArc(QRectF(cx - ww, my - dip, ww * 2, dip * 2), 200 * 16, 140 * 16)
            p.setPen(B.NOPEN)
