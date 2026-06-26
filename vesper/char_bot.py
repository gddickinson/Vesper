"""Bot, a round retro "dome" robot companion: a soft silver-blue ball head with a
single dark glossy visor band across the middle (the big cute eyes live inside it,
so it reads as a friendly screen face), a gentle glowing LED smile, a springy
antenna whose ball bobs + pulses with the breath, little round side-ear knobs and
a small breathing core button on a hint of a rounded body. Deliberately ROUND and
soft to contrast the app's other, angular square-screen robot. Shares the cute
eyes + breathing animation; everything is cool-toned and moves slowly for bedtime.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_BODY, _BODY_DK, _VISOR, _RIM = "#aebfd2", "#7c8da6", "#141e2a", "#dce6f2"


class Bot(B.Character):
    name = "Bot"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 4.5); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._body(p, cx, cy, R, a, hue)
        self._antenna(p, cx, cy, R, a, hue)
        self._ears(p, cx, cy, R, a, hue)
        self._dome(p, cx, cy, R)
        self._visor(p, cx, cy, R, hue)
        B.cute_eyes(p, cx, cy - R * 0.05, R * 0.25, R * 0.38, a,
                    iris=hue, dark="#0a131c")
        self._mouth(p, cx, cy, R, a, hue)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.55)        # crown above the antenna ball

    def _dome(self, p, cx, cy, R):
        g = QRadialGradient(cx - R * 0.32, cy - R * 0.4, R * 1.9)   # top-left light
        g.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.45)))
        g.setColorAt(0.55, B.qc(_BODY))
        g.setColorAt(1.0, B.qc(_BODY_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), R, R)
        B.pen(p, B.qc(_RIM, 0.55), R * 0.05)            # thin top-left rim light
        p.setBrush(B.qc(_RIM, 0.0))
        p.drawArc(QRectF(cx - R, cy - R, R * 2, R * 2), 60 * 16, 130 * 16)
        p.setPen(B.NOPEN)
        for ox, oy in ((-0.62, -0.5), (0.66, -0.42), (0.0, 0.78)):  # little rivets
            p.setBrush(B.qc(_BODY_DK, 0.7))
            p.drawEllipse(QPointF(cx + ox * R, cy + oy * R), R * 0.05, R * 0.05)
            p.setBrush(B.qc(_RIM, 0.5))
            p.drawEllipse(QPointF(cx + ox * R - R * 0.015, cy + oy * R - R * 0.015),
                          R * 0.02, R * 0.02)

    def _visor(self, p, cx, cy, R, hue):
        vw, vh = R * 1.52, R * 0.72
        rect = QRectF(cx - vw / 2, cy - R * 0.37, vw, vh)
        p.setBrush(B.qc(_VISOR))
        p.drawRoundedRect(rect, vh * 0.5, vh * 0.5)
        B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.4), 0.5), R * 0.03)  # neon glint
        p.setBrush(B.qc(_VISOR, 0.0))
        p.drawArc(QRectF(cx - vw * 0.42, cy - R * 0.31, vw * 0.84, vh * 0.7),
                  30 * 16, 120 * 16)
        p.setPen(B.NOPEN)

    def _mouth(self, p, cx, cy, R, a, hue):
        my = cy + R * 0.52
        glow = 0.4 + 0.5 * max(a.mouth, a.smile)
        n = 7
        for i in range(n):
            f = i / (n - 1)
            bx = cx + (f - 0.5) * R * 0.62
            dip = math.sin(f * math.pi) * R * (0.1 + 0.06 * a.smile)   # upturned smile
            wob = a.mouth * math.sin(a.t * 9 + i) * R * 0.04           # talk shimmer
            mx, myy = bx, my + dip + wob
            r = R * (0.035 + 0.02 * a.mouth)
            g = QRadialGradient(mx, myy, r * 3)
            g.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.3), glow))
            g.setColorAt(1.0, B.qc(hue, 0.0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(mx, myy), r * 3, r * 3)
            p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.25), 0.85))
            p.drawEllipse(QPointF(mx, myy), r, r)

    def _antenna(self, p, cx, cy, R, a, hue):
        basey = cy - R * 0.92
        sway = math.sin(a.t * 1.1) * R * 0.08 * (1 + 2 * a.excite)
        tipx, tipy = cx + sway, cy - R * 1.5
        pts = [(cx, basey)]                              # springy zig-zag coil
        coils = 4
        for i in range(1, coils + 1):
            f = i / coils
            y = basey + (tipy + R * 0.18 - basey) * f
            x = cx + sway * f + (R * 0.09 if i % 2 else -R * 0.09)
            pts.append((x, y))
        pts.append((tipx, tipy + R * 0.1))
        B.pen(p, B.qc(_BODY_DK), R * 0.045)
        p.setBrush(B.qc(_VISOR, 0.0))
        p.drawPolyline(B.poly(*pts))
        p.setPen(B.NOPEN)
        rr = R * (0.13 + 0.05 * a.breath)               # glowing, pulsing tip ball
        g = QRadialGradient(tipx, tipy, rr * 2.4)
        g.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.5), 0.8 + 0.2 * a.breath))
        g.setColorAt(1.0, B.qc(hue, 0.0))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(tipx, tipy), rr * 2.4, rr * 2.4)
        p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.3), 0.9))
        p.drawEllipse(QPointF(tipx, tipy), rr, rr)
        p.setBrush(B.qc("#ffffff", 0.8))
        p.drawEllipse(QPointF(tipx - rr * 0.3, tipy - rr * 0.3), rr * 0.3, rr * 0.3)

    def _ears(self, p, cx, cy, R, a, hue):
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.97, cy + R * 0.05
            g = QRadialGradient(ex, ey, R * 0.5)        # soft glow behind the knob
            g.setColorAt(0.0, B.qc(hue, 0.28 + 0.2 * a.breath))
            g.setColorAt(1.0, B.qc(hue, 0.0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(ex, ey), R * 0.5, R * 0.5)
            p.setBrush(B.qc(_BODY_DK))
            p.drawEllipse(QPointF(ex, ey), R * 0.2, R * 0.26)
            p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.4), 0.7 + 0.3 * a.breath))
            p.drawEllipse(QPointF(ex, ey), R * 0.09, R * 0.09)

    def _body(self, p, cx, cy, R, a, hue):
        bw = R * 1.5 * (0.97 + 0.05 * a.breath)
        bh = R * 0.95 * (1.0 + a.squash)
        by = cy + R * 0.78
        g = QRadialGradient(cx - R * 0.2, by, bw)       # round shoulders below head
        g.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.2)))
        g.setColorAt(1.0, B.qc(_BODY_DK))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh + R), R * 0.5, R * 0.5)
        ccy = by + R * 0.3                              # breathing core button
        rr = R * (0.15 + 0.04 * a.breath)
        gl = QRadialGradient(cx, ccy, rr * 2.4)
        gl.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.3), 0.6 + 0.4 * a.breath))
        gl.setColorAt(1.0, B.qc(hue, 0.0))
        p.setBrush(QBrush(gl))
        p.drawEllipse(QPointF(cx, ccy), rr * 2.4, rr * 2.4)
        p.setBrush(B.qc(_BODY_DK, 0.9))
        p.drawEllipse(QPointF(cx, ccy), rr, rr)
        p.setBrush(B.qc(hue, 0.85))
        p.drawEllipse(QPointF(cx, ccy), rr * 0.55, rr * 0.55)
