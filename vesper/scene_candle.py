"""Candle scene: a single still flame to rest the gaze on (trataka).

A traditional focused-attention practice is to gaze softly at a candle flame
(*trataka*): a single, steady point of light gathers a wandering mind. This scene
draws one warm candle in the dark — a pale wax body, a soft pool of light it casts,
an ambient room glow that **breathes with you**, and a layered teardrop flame that
sways and flickers very gently (low amplitude, no strobing) and grows a touch on the
inhale. Deterministic: all motion comes from the anim clock, nothing per frame.

A separate module (scenes.py is large); registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QLinearGradient, QPainterPath, QPen,
                           QRadialGradient)

from . import theme
from .scenes import _overlay, _qc

_BG_TOP, _BG_BOT = "#070605", "#15100b"        # near-black, a hint of warmth low
_GLOW = "#e8842c"                              # ambient orange room glow
_OUTER, _MID, _INNER, _CORE = "#e0741f", "#f3a838", "#f7d653", "#fff3cf"
_BLUE = "#5d6bd0"                              # the cool base of a real flame
_WAX = "#efe6cf"                               # pale candle body


def _teardrop(cx, tip_y, base_y, half_w):
    """A flame teardrop: pointed at the top (tip), rounded at the base."""
    span = base_y - tip_y
    path = QPainterPath()
    path.moveTo(cx, tip_y)
    path.cubicTo(cx + half_w * 0.55, tip_y + span * 0.34,
                 cx + half_w, base_y - span * 0.28, cx, base_y)
    path.cubicTo(cx - half_w, base_y - span * 0.28,
                 cx - half_w * 0.55, tip_y + span * 0.34, cx, tip_y)
    return path


class CandleScene:
    name = "candle"

    def __init__(self):
        rng = np.random.default_rng(17)
        # a few faint rising specks of light (slow, dim — like warmed air glinting)
        self.specks = [dict(x0=(float(rng.random()) * 2 - 1) * 0.05,
                            sp=0.5 + float(rng.random()) * 0.7,
                            ph=float(rng.random()),
                            dr=float(rng.random()) * 6.28,
                            sz=0.7 + float(rng.random()) * 1.1) for _ in range(7)]

    def draw(self, p, w, h, c):
        grad = QLinearGradient(0.0, 0.0, 0.0, float(h))
        grad.setColorAt(0.0, _qc(_BG_TOP))
        grad.setColorAt(1.0, _qc(_BG_BOT))
        p.fillRect(0, 0, w, h, QBrush(grad))
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        cx = w * 0.5
        top = h * 0.60                                  # candle top (wick sits here)
        breath = 0.88 + 0.24 * vol                      # flame grows on the inhale
        # very gentle sway + slow flicker (low amplitude => calm, never strobing)
        sway = math.sin(t * 0.55) * w * 0.006 + math.sin(t * 0.9 + 1.3) * w * 0.003
        flick = 0.93 + 0.07 * math.sin(t * 1.6) + 0.03 * math.sin(t * 2.7 + 0.6)
        p.setPen(Qt.PenStyle.NoPen)

        # ambient room glow around the flame, breathing with the breath
        gr = min(w, h) * (0.42 + 0.06 * vol)
        glow = QRadialGradient(cx, top - h * 0.06, gr)
        glow.setColorAt(0.0, _qc(_GLOW, 0.16 + 0.12 * vol))
        glow.setColorAt(0.5, _qc(_OUTER, 0.06 + 0.05 * vol))
        glow.setColorAt(1.0, _qc(_OUTER, 0.0))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, top - h * 0.06), gr, gr)

        # the warm pool of light the candle casts on the surface it rests on
        pr = w * 0.20 * (0.9 + 0.2 * vol)
        pool = QRadialGradient(cx, top + h * 0.30, pr)
        pool.setColorAt(0.0, _qc(_GLOW, 0.13 + 0.07 * vol))
        pool.setColorAt(1.0, _qc(_GLOW, 0.0))
        p.setBrush(QBrush(pool))
        p.drawEllipse(QPointF(cx, top + h * 0.30), pr, pr * 0.34)

        self._candle(p, w, h, cx, top)
        self._flame(p, w, h, cx, top, breath, flick, sway, vol)

        for s in self.specks:                           # faint rising glints
            cyc = (t * 0.07 * s["sp"] + s["ph"]) % 1.0
            ey = top - h * 0.10 - cyc * h * 0.30
            ex = cx + s["x0"] * w + math.sin(t * 0.5 + s["dr"]) * w * 0.012
            a = max(0.0, 1.0 - cyc) * 0.35
            p.setBrush(_qc(theme.blend(_CORE, "#ffffff", 0.2), a))
            p.drawEllipse(QPointF(ex, ey), s["sz"], s["sz"])

        _overlay(p, w, cx, h * 0.20, h * 0.20 + 38, h * 0.20 + 74, h - 22, c, _MID)

    def _candle(self, p, w, h, cx, top):
        cw, ch = w * 0.085, h * 0.22                    # a calm, slightly tapered body
        left, right = cx - cw / 2, cx + cw / 2
        body = QLinearGradient(left, 0.0, right, 0.0)
        body.setColorAt(0.0, _qc(theme.blend(_WAX, _BG_BOT, 0.45)))
        body.setColorAt(0.5, _qc(_WAX))
        body.setColorAt(1.0, _qc(theme.blend(_WAX, _BG_BOT, 0.55)))
        p.setBrush(QBrush(body))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(left, top + 4, cw, ch), cw * 0.28, cw * 0.28)
        # a soft warm rim where the flame lights the wax top
        rim = QRadialGradient(cx, top + 6, cw * 0.7)
        rim.setColorAt(0.0, _qc(_GLOW, 0.5))
        rim.setColorAt(1.0, _qc(_GLOW, 0.0))
        p.setBrush(QBrush(rim))
        p.drawEllipse(QPointF(cx, top + 6), cw * 0.62, cw * 0.20)
        # the dark little wick
        p.setBrush(_qc("#241a12"))
        p.drawRoundedRect(QRectF(cx - 1.2, top - h * 0.018, 2.4, h * 0.024), 1, 1)

    def _flame(self, p, w, h, cx, top, breath, flick, sway, vol):
        fh = h * 0.165 * breath * flick                 # flame height
        fw = w * 0.030 * breath                         # half-width at the base
        base_y = top - h * 0.014                         # just above the wick
        # layered teardrops, outer (soft, wide) -> core (small, bright). The tip
        # leans with the gentle sway; lower layers barely move (rooted at the wick).
        layers = [(_OUTER, 1.30, 1.18, 0.16 + 0.10 * vol),
                  (_MID,   1.00, 1.00, 0.34 + 0.14 * vol),
                  (_INNER, 0.66, 0.80, 0.55 + 0.16 * vol),
                  (_CORE,  0.34, 0.55, 0.85)]
        p.setPen(Qt.PenStyle.NoPen)
        for col, wf, hf, a in layers:
            tip_y = base_y - fh * hf
            half_w = fw * wf
            path = _teardrop(cx + sway, tip_y, base_y, half_w)
            g = QRadialGradient(cx, base_y - fh * hf * 0.45, fh * hf * 0.8)
            g.setColorAt(0.0, _qc(theme.blend(col, "#ffffff", 0.15), a))
            g.setColorAt(0.7, _qc(col, a * 0.85))
            g.setColorAt(1.0, _qc(col, 0.0))
            p.setBrush(QBrush(g))
            p.drawPath(path)
        # the cool blue heart at the very base of a real flame
        bb = QRadialGradient(cx, base_y - fh * 0.12, fw * 1.1)
        bb.setColorAt(0.0, _qc(_BLUE, 0.40))
        bb.setColorAt(1.0, _qc(_BLUE, 0.0))
        p.setBrush(QBrush(bb))
        p.drawEllipse(QPointF(cx, base_y - fh * 0.12), fw * 1.1, fh * 0.22)
