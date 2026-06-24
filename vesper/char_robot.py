"""The robot character: a friendly retro-cyber bot with a brushed-metal head, a
dark screen face, glowing eyes, an LED mouth that lights up when it talks, an
antenna whose tip pulses with the breath (and sparks when excited) and a glowing
chest core. Shares the cute eyes + breathing animation.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_BODY, _BODY_DK, _TRIM, _PANEL = "#9fb0c4", "#6e7d92", "#c7d2de", "#141e2a"


class Robot(B.Character):
    name = "Robot"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 5.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._antenna(p, cx, cy, R, a)
        self._body(p, cx, cy, R, a)
        for s in (-1, 1):                                     # ear panels + dials
            p.setBrush(B.qc(_BODY_DK))
            p.drawRoundedRect(QRectF(cx + s * R * 1.02 - R * 0.12, cy - R * 0.22,
                                     R * 0.24, R * 0.44), R * 0.06, R * 0.06)
            p.save(); p.translate(cx + s * R * 1.02, cy); p.rotate(a.t * 40.0 % 360)
            B.pen(p, B.qc(_TRIM), R * 0.04)
            p.drawLine(QPointF(-R * 0.07, 0), QPointF(R * 0.07, 0))
            p.setPen(B.NOPEN); p.restore()
        g = QRadialGradient(cx - R * 0.2, cy - R * 0.25, R * 1.5)   # metal head
        g.setColorAt(0.0, B.qc(theme.blend(_BODY, "#ffffff", 0.3)))
        g.setColorAt(1.0, B.qc(_BODY_DK))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(QRectF(cx - R * 0.95, cy - R * 0.95, R * 1.9, R * 1.9),
                          R * 0.34, R * 0.34)
        for sx in (-1, 1):                                    # corner bolts
            for sy in (-1, 1):
                p.setBrush(B.qc(_TRIM, 0.8))
                p.drawEllipse(QPointF(cx + sx * R * 0.78, cy + sy * R * 0.78),
                              R * 0.06, R * 0.06)
        p.setBrush(B.qc(_PANEL))                              # dark screen face
        p.drawRoundedRect(QRectF(cx - R * 0.72, cy - R * 0.62, R * 1.44, R * 1.3),
                          R * 0.22, R * 0.22)
        for s in (-1, 1):                                     # cheek status lights
            p.setBrush(B.qc(hue, 0.4 + 0.4 * a.breath))
            p.drawEllipse(QPointF(cx + s * R * 0.5, cy + R * 0.18), R * 0.06, R * 0.06)
        B.cute_eyes(p, cx, cy - R * 0.12, R * 0.27, R * 0.4, a, iris=hue, dark="#0a131c")
        self._mouth(p, cx, cy, R, a, hue)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.5)               # crown above the antenna

    def _antenna(self, p, cx, cy, R, a):
        tipx = cx + math.sin(a.t * 1.2) * R * 0.05 * (1 + 3 * a.excite)
        tipy = cy - R * 1.45
        B.pen(p, B.qc(_BODY_DK), R * 0.06)
        p.drawLine(QPointF(cx, cy - R * 0.9), QPointF(tipx, tipy + R * 0.12))
        p.setPen(B.NOPEN)
        gl = QRadialGradient(tipx, tipy, R * 0.3)            # glowing pulsing tip
        gl.setColorAt(0.0, B.qc(theme.blend(a.hue, "#ffffff", 0.4),
                                0.7 + 0.3 * a.breath))
        gl.setColorAt(1.0, B.qc(a.hue, 0.0))
        p.setBrush(QBrush(gl))
        p.drawEllipse(QPointF(tipx, tipy), R * (0.12 + 0.05 * a.breath),
                      R * (0.12 + 0.05 * a.breath))
        if a.excite > 0.3:                                   # sparks when excited
            B.pen(p, B.qc(theme.blend(a.hue, "#ffffff", 0.5), a.excite), R * 0.03)
            for k in range(4):
                an = a.t * 6 + k * 1.57
                p.drawLine(QPointF(tipx, tipy),
                           QPointF(tipx + math.cos(an) * R * 0.22,
                                   tipy + math.sin(an) * R * 0.22))
            p.setPen(B.NOPEN)

    def _body(self, p, cx, cy, R, a):
        bw = R * 1.9 * (0.97 + 0.06 * a.breath)
        bh = R * 1.4 * (1.0 + a.squash)
        by = cy + R * 0.6
        p.setBrush(B.qc(_BODY_DK, 0.97))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.3, R * 0.3)
        p.setBrush(B.qc(_PANEL))                              # chest plate
        p.drawRoundedRect(QRectF(cx - bw * 0.3, by + R * 0.2, bw * 0.6, bh * 0.6),
                          R * 0.14, R * 0.14)
        gl = QRadialGradient(cx, by + bh * 0.5, R * 0.5)     # glowing core (breathes)
        gl.setColorAt(0.0, B.qc(theme.blend(a.hue, "#ffffff", 0.3),
                                0.6 + 0.4 * a.breath))
        gl.setColorAt(1.0, B.qc(a.hue, 0.0))
        p.setBrush(QBrush(gl))
        p.drawEllipse(QPointF(cx, by + bh * 0.5), R * 0.34, R * 0.34)
        p.setBrush(B.qc(a.hue, 0.85))
        p.drawEllipse(QPointF(cx, by + bh * 0.5), R * 0.12, R * 0.12)

    def _mouth(self, p, cx, cy, R, a, hue):
        my = cy + R * 0.44
        n = 7
        p.setPen(B.NOPEN)
        if a.mouth > 0.06:                                   # LED bars react to speech
            for i in range(n):
                bx = cx + (i - (n - 1) / 2) * R * 0.16
                ph = 0.5 + 0.5 * math.sin(a.t * 9 + i)
                bh = R * (0.05 + 0.3 * a.mouth * ph)
                p.setBrush(B.qc(hue, 0.85))
                p.drawRoundedRect(QRectF(bx - R * 0.04, my - bh, R * 0.08, bh * 2),
                                  R * 0.03, R * 0.03)
        else:                                                # a gentle LED smile
            for i in range(n):
                f = i / (n - 1)
                bx = cx + (f - 0.5) * R * 0.9
                dip = math.sin(f * math.pi) * R * 0.1 * (0.4 + 0.8 * a.smile)
                p.setBrush(B.qc(hue, 0.5 + 0.4 * a.smile))
                p.drawEllipse(QPointF(bx, my + dip), R * 0.045, R * 0.045)
