"""The snowman character: two stacked snowballs with coal eyes, a carrot nose, a
coal-button smile, twig arms, a cosy knit cap and a red scarf -- with a few soft
snowflakes drifting down around him. The perfect wintry companion for snow scenes
and snowy stories. Shares the cute eyes + breathing animation (his scarf-end sways
and the snow drifts on the per-frame anim time, easing under reduce-motion)."""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme

_SNOW, _SNOW_DK = "#eef4fb", "#cdddec"
_COAL = "#2b2f38"
_CARROT, _CARROT_DK = "#e8842c", "#c96a1c"
_SCARF, _SCARF_DK = "#cf5b57", "#a8413e"
_STICK = "#6b4a32"
_CAP, _CAP_DK = "#3f7d86", "#2f5f66"


class Snowman(B.Character):
    name = "Snowman"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, scale=0.21, ypos=0.42)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 4.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy + R * 0.5, R, hue, a.breath)
        bcy = cy + R * 1.5                                    # lower (body) snowball
        bw = R * 1.45 * (0.97 + 0.06 * a.breath)
        bh = R * 1.35 * (1.0 + a.squash)
        self._arms(p, cx, bcy, R, bw, a)
        self._ball(p, cx, bcy, bw, bh)                        # body
        p.setBrush(B.qc(_COAL))                               # coal buttons
        for k in (-1, 0, 1):
            p.drawEllipse(QPointF(cx, bcy + k * bh * 0.34), R * 0.06, R * 0.06)
        self._ball(p, cx, cy, R * 1.04, R * 0.98)             # head
        self._scarf(p, cx, cy, R, a)
        self._cap(p, cx, cy, R)
        B.blush(p, cx, cy + R * 0.18, R, R * 0.6, color="#bcd6ea", amt=0.5)
        B.cute_eyes(p, cx, cy - R * 0.1, R * 0.22, R * 0.36, a,
                    iris="#39444f", glow=False)               # coal eyes
        self._nose(p, cx, cy, R)
        self._smile(p, cx, cy, R, a)
        self._snow(p, cx, cy, R, a)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.04)

    def _ball(self, p, cx, cyy, bw, bh):
        g = QRadialGradient(cx - bw * 0.25, cyy - bh * 0.3, bw * 1.6)
        g.setColorAt(0.0, B.qc("#ffffff"))
        g.setColorAt(1.0, B.qc(_SNOW_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cyy), bw, bh)

    def _arms(self, p, cx, bcy, R, bw, a):
        wave = math.sin(a.t * 0.9) * 0.12 + a.ear * 0.2       # a gentle twig sway
        for s in (-1, 1):
            B.pen(p, B.qc(_STICK), R * 0.06)
            x0, y0 = cx + s * bw * 0.7, bcy - R * 0.2
            x1, y1 = x0 + s * R * 0.8, y0 - R * (0.5 + wave * s)
            p.drawPolyline(B.poly((x0, y0), (x1, y1)))
            p.drawPolyline(B.poly((x1, y1), (x1 + s * R * 0.22, y1 - R * 0.22)))
            p.drawPolyline(B.poly((x1, y1), (x1 + s * R * 0.26, y1 + R * 0.1)))
            p.setPen(B.NOPEN)

    def _scarf(self, p, cx, cy, R, a):
        ny = cy + R * 0.78
        p.setBrush(B.qc(_SCARF))                              # band around the neck
        p.drawRoundedRect(QRectF(cx - R * 0.72, ny - R * 0.14, R * 1.44, R * 0.34),
                          R * 0.14, R * 0.14)
        swing = math.sin(a.t * 1.4) * R * 0.16                # the hanging end sways
        p.setBrush(B.qc(_SCARF_DK))
        p.drawPolygon(B.poly((cx + R * 0.36, ny - R * 0.05),
                             (cx + R * 0.62, ny - R * 0.05),
                             (cx + R * 0.58 + swing, ny + R * 0.7),
                             (cx + R * 0.34 + swing, ny + R * 0.7)))

    def _cap(self, p, cx, cy, R):
        ty = cy - R * 0.92
        p.setBrush(B.qc(_CAP_DK))                             # folded brim
        p.drawRoundedRect(QRectF(cx - R * 0.78, ty - R * 0.04, R * 1.56, R * 0.3),
                          R * 0.12, R * 0.12)
        p.setBrush(B.qc(_CAP))                                # cap dome
        p.drawChord(QRectF(cx - R * 0.7, ty - R * 0.78, R * 1.4, R * 1.2),
                    0, 180 * 16)
        p.setBrush(B.qc("#f4f8fc"))                           # pompom
        p.drawEllipse(QPointF(cx, ty - R * 0.62), R * 0.16, R * 0.16)

    def _nose(self, p, cx, cy, R):
        ny = cy + R * 0.16
        p.setBrush(B.qc(_CARROT))                             # carrot juts to the side
        p.drawPolygon(B.poly((cx - R * 0.04, ny - R * 0.1),
                             (cx - R * 0.04, ny + R * 0.1),
                             (cx + R * 0.5, ny + R * 0.02)))
        B.pen(p, B.qc(_CARROT_DK), R * 0.02)                  # ridge lines
        for f in (0.3, 0.6):
            p.drawPolyline(B.poly((cx - R * 0.04 + R * 0.5 * f, ny - R * 0.06 * (1 - f)),
                                  (cx - R * 0.04 + R * 0.5 * f, ny + R * 0.07 * (1 - f))))
        p.setPen(B.NOPEN)

    def _smile(self, p, cx, cy, R, a):
        my = cy + R * 0.5
        if a.mouth > 0.06:                                    # an open "oh"
            p.setBrush(B.qc("#3a2230"))
            p.drawEllipse(QPointF(cx, my + R * 0.05), R * 0.13,
                          R * (0.05 + 0.2 * a.mouth))
            return
        p.setBrush(B.qc(_COAL))                               # a curve of coal dots
        for k in range(-2, 3):
            f = k / 2.0
            p.drawEllipse(QPointF(cx + f * R * 0.34,
                                  my + abs(f) * R * 0.12 - R * 0.04 * a.smile),
                          R * 0.045, R * 0.045)

    def _snow(self, p, cx, cy, R, a):
        p.setPen(B.NOPEN)
        for i in range(7):                                   # soft flakes drifting down
            fx = cx + (((i * 0.37) % 1.0) - 0.5) * R * 3.0
            drift = ((i * 0.19 + a.t * (0.03 + 0.01 * (i % 3))) % 1.0)
            fy = cy - R * 1.3 + drift * R * 4.2
            fx += math.sin(a.t * 0.5 + i) * R * 0.12
            al = 0.18 + 0.16 * math.sin(a.t * 0.7 + i * 1.3)
            p.setBrush(B.qc("#ffffff", max(0.05, al)))
            p.drawEllipse(QPointF(fx, fy), R * 0.05, R * 0.05)
