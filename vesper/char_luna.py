"""Luna, the Moon: a serene, sleeping moon-companion whose crescent shows the
**real phase of the moon tonight**.

A pale-gold disc with soft seas, a warm glow and a gently sleeping face (closed
eyes, a small content smile). Its terminator -- the soft shadow across the disc --
is drawn from `breathsim.moonphase` for the current date and waxing/waning
direction, so the Luna you see matches the moon in the sky. The face always shows
over the shadow, so even a new moon stays a cosy, smiling companion. Shares the
breathing animation; the glow swells gently on the inhale.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QPainterPath, QRadialGradient

from breathsim import moonphase

from . import char_base as B
from . import theme

_MOON_HI, _MOON, _MOON_DK = "#fff6d4", "#f3e6ad", "#d8c984"
_SEA = "#cabf86"
_FACE = "#9a8a4a"
_SEAS = [(-0.34, -0.18, 0.22), (0.30, 0.30, 0.16),     # fixed soft "craters"
         (0.10, -0.40, 0.12), (-0.16, 0.38, 0.10)]
_STARS = [(-1.45, -0.9), (1.5, -0.6), (-1.3, 0.7), (1.35, 0.95),
          (0.1, -1.45), (-0.05, 1.5)]


class Luna(B.Character):
    name = "Luna"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, scale=0.24)
        Rm = R * 1.12
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:
            p.translate(cx, cy); p.rotate(a.tilt * 4.0); p.translate(-cx, -cy)
        self._stars(p, cx, cy, Rm, a)
        B.aura(p, cx, cy, R, "#ffe9a8", a.breath)          # warm moon glow
        g = QRadialGradient(cx - Rm * 0.25, cy - Rm * 0.3, Rm * 1.7)
        g.setColorAt(0.0, B.qc(_MOON_HI)); g.setColorAt(1.0, B.qc(_MOON_DK))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), Rm, Rm)
        for ox, oy, r in _SEAS:                            # soft seas / craters
            p.setBrush(B.qc(_SEA, 0.5))
            p.drawEllipse(QPointF(cx + ox * Rm, cy + oy * Rm), r * Rm, r * Rm)
        self._terminator(p, cx, cy, Rm)
        self._face(p, cx, cy, Rm, a)
        p.restore()
        return B.Head(cx, cy, R, cy - Rm)

    def _terminator(self, p, cx, cy, Rm):
        """The soft shadow showing tonight's real phase -- a dark disc offset to
        carve the crescent/gibbous, clipped to the moon so it never darkens the sky."""
        illum = moonphase.illumination()
        off = illum * 2.0 * Rm                             # 0 (new) -> 2R (full, off)
        sx = cx - off if moonphase.waxing() else cx + off  # lit side: right when waxing
        clip = QPainterPath(); clip.addEllipse(QPointF(cx, cy), Rm, Rm)
        p.save(); p.setClipPath(clip)
        dark = theme.blend(theme.NIGHT_BG, "#000010", 0.4)
        sh = QRadialGradient(sx, cy, Rm * 1.05)
        sh.setColorAt(0.0, B.qc(dark, 0.6))
        sh.setColorAt(0.85, B.qc(dark, 0.6))
        sh.setColorAt(1.0, B.qc(dark, 0.0))                # soft terminator edge
        p.setBrush(QBrush(sh))
        p.drawEllipse(QPointF(sx, cy), Rm, Rm)
        p.restore()

    def _face(self, p, cx, cy, Rm, a):
        eyey, sp, ew = cy - Rm * 0.06, Rm * 0.34, Rm * 0.2
        B.pen(p, B.qc(_FACE), Rm * 0.05)
        for s in (-1, 1):                                  # gently closed, content eyes
            p.drawArc(QRectF(cx + s * sp - ew, eyey - ew * 0.3, ew * 2, ew * 0.9),
                      200 * 16, 140 * 16)
        p.setPen(B.NOPEN)
        B.blush(p, cx, cy + Rm * 0.06, Rm, Rm * 0.52, color="#eab9a0", amt=0.45)
        my = cy + Rm * 0.34
        if a.mouth > 0.06:                                 # a soft "oh" when speaking
            p.setBrush(B.qc("#6a5326"))
            p.drawEllipse(QPointF(cx, my), Rm * 0.11, Rm * (0.05 + 0.18 * a.mouth))
        else:                                              # a small content smile
            B.pen(p, B.qc(_FACE), Rm * 0.045)
            r2 = Rm * 0.3
            span = int((150 + 30 * a.smile) * 16)
            p.drawArc(QRectF(cx - r2, my - r2 * 0.2, r2, r2 * 0.7), 200 * 16, span)
            p.drawArc(QRectF(cx, my - r2 * 0.2, r2, r2 * 0.7), (340 * 16) - span, span)
            p.setPen(B.NOPEN)

    def _stars(self, p, cx, cy, Rm, a):
        p.setPen(B.NOPEN)
        for i, (ox, oy) in enumerate(_STARS):
            tw = 0.5 + 0.5 * math.sin(a.t * 0.8 + i * 1.3)
            p.setBrush(B.qc(theme.blend(theme.NIGHT_BG, "#fff3c8", 0.4 + 0.6 * tw)))
            r = Rm * (0.03 + 0.03 * tw)
            p.drawEllipse(QPointF(cx + ox * Rm, cy + oy * Rm), r, r)
