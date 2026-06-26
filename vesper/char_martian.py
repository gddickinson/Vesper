"""The Martian character: a cheerful little ONE-EYED (cyclops) alien in warm
purple/magenta -- clearly not a grey two-eyed alien and not a metal robot. A soft
egg-shaped head with a radial sheen and a few freckles, one big glossy central eye
that blinks, follows the gaze and dilates with the breath, a wide friendly smile,
soft blushing cheeks, and two short stubby antennae whose glowing tips pulse with
the breath and sway gently. Slow, low-contrast and cute -- made for bedtime.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QPainterPath, QRadialGradient

from . import char_base as B
from . import theme

_BASE, _SHADE, _FRECK = "#b98cff", "#8a5cd6", "#6f49b0"
_FRECKLES = ((-0.34, 0.46), (0.40, 0.40), (0.30, 0.60), (-0.46, 0.30))


class Martian(B.Character):
    name = "Martian"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        base = theme.blend(_BASE, hue, 0.16)            # gently tint toward the hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 5.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._antennae(p, cx, cy, R, a, hue)

        rx, ry = R * 0.92, R * 1.02                     # soft egg-shaped head
        g = QRadialGradient(cx - R * 0.32, cy - R * 0.42, R * 1.9)
        g.setColorAt(0.0, B.qc(theme.blend(base, "#ffffff", 0.34)))
        g.setColorAt(0.6, B.qc(base))
        g.setColorAt(1.0, B.qc(_SHADE))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), rx, ry)
        p.setBrush(B.qc(theme.blend(base, "#ffffff", 0.5), 0.18))   # top sheen
        p.drawEllipse(QPointF(cx - R * 0.22, cy - R * 0.5), R * 0.42, R * 0.26)
        for fx, fy in _FRECKLES:                        # charm freckles
            p.setBrush(B.qc(_FRECK, 0.4))
            p.drawEllipse(QPointF(cx + fx * R, cy + fy * R), R * 0.045, R * 0.045)

        B.blush(p, cx, cy + R * 0.42, R, R * 0.62,
                theme.blend("#ff9ad5", hue, 0.2), 0.55 + 0.3 * a.breath)
        self._eye(p, cx, cy - R * 0.06, R, a, hue)
        self._mouth(p, cx, cy + R * 0.6, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.45)         # crown above the antennae

    def _antennae(self, p, cx, cy, R, a, hue):
        for s in (-1, 1):
            basex = cx + s * R * 0.34
            basey = cy - R * 0.82
            wob = math.sin(a.t * 1.3 + s * 1.7) * R * 0.07 * (1 + 2 * a.excite)
            tipx = basex + s * R * 0.16 + wob + a.sway * R * 0.4
            tipy = basey - R * 0.5
            B.pen(p, B.qc(_SHADE), R * 0.07)            # short stubby stalk
            p.drawLine(QPointF(basex, basey + R * 0.1), QPointF(tipx, tipy))
            p.setPen(B.NOPEN)
            tip = theme.blend(hue, "#ffffff", 0.45)
            gl = QRadialGradient(tipx, tipy, R * 0.3)   # glowing pulsing tip
            gl.setColorAt(0.0, B.qc(tip, 0.7 + 0.3 * a.breath))
            gl.setColorAt(1.0, B.qc(hue, 0.0))
            p.setBrush(QBrush(gl))
            rad = R * (0.13 + 0.05 * a.breath)
            p.drawEllipse(QPointF(tipx, tipy), rad, rad)
            p.setBrush(B.qc(tip, 0.95))
            p.drawEllipse(QPointF(tipx, tipy), R * 0.06, R * 0.06)

    def _eye(self, p, ex, ey, R, a, hue):
        open_amt = max(0.04, 1.0 - a.blink)
        rx = R * 0.5
        ry = R * 0.54 * open_amt                        # blink scales the height
        gx, gy = a.gaze
        p.setPen(B.NOPEN)
        gl = QRadialGradient(ex, ey, rx * 2.0)          # faint rim glow (breath)
        gl.setColorAt(0.0, B.qc(hue, 0.16 + 0.26 * a.breath))
        gl.setColorAt(1.0, B.qc(hue, 0.0))
        p.setBrush(QBrush(gl))
        p.drawEllipse(QPointF(ex, ey), rx * 1.7, rx * 1.7)
        p.setBrush(B.qc("#0c1622"))                     # big dark base
        p.drawEllipse(QPointF(ex, ey), rx, ry)
        if open_amt < 0.16:                             # nearly shut -> happy lash
            B.pen(p, B.qc("#0c1622"), R * 0.05)
            p.drawArc(QRectF(ex - rx, ey - rx * 0.4, rx * 2, rx * 0.8),
                      0, 180 * 16)
            p.setPen(B.NOPEN)
            return
        iris = theme.blend(hue, "#7fe9ff", 0.35)
        p.setBrush(B.qc(iris))                          # bright iris
        p.drawEllipse(QPointF(ex, ey), rx * 0.82, ry * 0.86)
        pw = rx * (0.4 + 0.2 * a.breath)               # pupil dilates inhaling
        px = ex + gx * rx * 0.55
        py = ey + gy * ry * 0.55
        p.setBrush(B.qc("#06101a"))
        p.drawEllipse(QPointF(px, py), pw, pw * (ry / rx))
        p.setBrush(B.qc("#ffffff", 0.95))               # big catchlight
        p.drawEllipse(QPointF(px - rx * 0.28, py - ry * 0.3), rx * 0.22, rx * 0.22)
        p.setBrush(B.qc("#ffffff", 0.6))                # tiny sparkle
        p.drawEllipse(QPointF(px + rx * 0.2, py + ry * 0.16), rx * 0.09, rx * 0.09)

    def _mouth(self, p, cx, my, R, a):
        mw = R * (0.34 + 0.26 * a.smile)                # widens with the smile
        dip = R * (0.16 + 0.34 * a.smile)               # curves up more, smiling
        gap = R * (0.04 + 0.42 * a.mouth)               # opens when talking
        path = QPainterPath(QPointF(cx - mw, my))       # upward smile arc
        path.quadTo(cx, my + dip, cx + mw, my)
        if gap > R * 0.07:                              # open mouth -> soft fill
            path.quadTo(cx, my + dip + gap, cx - mw, my)
            p.setPen(B.NOPEN)
            p.setBrush(B.qc(theme.blend("#5a2a4a", a.hue, 0.15), 0.85))
            p.drawPath(path)
        B.pen(p, B.qc(_SHADE), R * 0.06)
        p.drawPath(path)
        p.setPen(B.NOPEN)
