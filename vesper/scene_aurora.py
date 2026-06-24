"""Aurora scene: slow northern-lights curtains over a starry night.

Soft vertical drapes of green (with teal and a little violet) wave and shimmer
slowly across the upper sky, brightening and fading, over a faint star field and a
dark horizon. Each curtain is drawn as overlapping vertical-gradient columns whose
top edge undulates and whose brightness drifts in slow patches; the whole curtain
also drifts sideways on layered, near-coprime sines, so it never repeats. The glow
swells gently with the breath. Slow, dim, low-blue/green (calming).

Deterministic (seeded params + anim-time motion, nothing spawned per frame). A
separate module (scenes.py is large); registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QLinearGradient, QPolygonF

from . import scene_fx, theme
from .scenes import _overlay, _qc

_GREEN = "#4cc88a"
_TEAL = "#3fb6cf"
_VIOLET = "#9a7fd0"


class AuroraScene:
    name = "aurora"
    COLS = 44

    def __init__(self):
        rng = np.random.default_rng(27)
        self.stars = [dict(nx=float(rng.random()), ny=float(rng.random()) * 0.7,
                           ph=float(rng.random()) * 6.28,
                           sp=0.2 + float(rng.random()) * 0.6) for _ in range(70)]
        # (x span, top band, height, colour, drift amps, alpha, wave no., speed, phase)
        self.curtains = [
            dict(x0=0.05, x1=0.55, top=0.12, h=0.42, col=_GREEN, d1=0.05,
                 d2=0.018, a=0.17, k=2.2, ks=0.5, ph=0.0),
            dict(x0=0.30, x1=0.85, top=0.16, h=0.40, col=_TEAL, d1=0.04,
                 d2=0.025, a=0.13, k=2.8, ks=0.42, ph=2.0),
            dict(x0=0.45, x1=0.98, top=0.10, h=0.46, col=_GREEN, d1=0.06,
                 d2=0.02, a=0.15, k=1.8, ks=0.58, ph=4.0),
            dict(x0=0.15, x1=0.70, top=0.20, h=0.34, col=_VIOLET, d1=0.045,
                 d2=0.03, a=0.08, k=3.2, ks=0.36, ph=1.0),
        ]

    def _curtain(self, p, w, h, t, cu, breath):
        span = (cu["x1"] - cu["x0"]) * w
        x0 = cu["x0"] * w
        drift = (cu["d1"] * math.sin(t * cu["ks"] + cu["ph"])
                 + cu["d2"] * math.sin(t * cu["ks"] * 1.7 + cu["ph"] * 0.5)) * w
        colw = span / self.COLS
        for i in range(self.COLS):
            fx = i / (self.COLS - 1)
            x = x0 + fx * span + drift
            top = (cu["top"] + 0.05 * math.sin(fx * cu["k"] * 6.28
                   + t * cu["ks"] * 1.3 + cu["ph"])) * h
            bot = top + cu["h"] * h * (0.8 + 0.3 * math.sin(fx * 1.7 + t * 0.2))
            sh = 0.45 + 0.55 * math.sin(fx * 5.0 - t * 0.7 + cu["ph"] * 1.3)
            a = cu["a"] * max(0.0, sh) * breath
            if a <= 0.004:
                continue
            grad = QLinearGradient(0.0, top, 0.0, bot)
            grad.setColorAt(0.0, _qc(cu["col"], 0.0))
            grad.setColorAt(0.28, _qc(cu["col"], a))
            grad.setColorAt(1.0, _qc(cu["col"], 0.0))
            p.setBrush(QBrush(grad))
            p.drawRect(QRectF(x, top, colw * 1.4, bot - top))

    def _horizon(self, p, w, h):
        base = h * 0.86
        poly = QPolygonF([QPointF(0, h), QPointF(0, base)])
        x = 0
        while x <= w:
            poly.append(QPointF(x, base + 10 * math.sin(x / w * 6.28 * 1.5)))
            x += 24
        poly.append(QPointF(w, base))
        poly.append(QPointF(w, h))
        p.setBrush(_qc("#04070d"))
        p.drawPolygon(poly)

    def draw(self, p, w, h, c):
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        breath = 0.7 + 0.5 * vol
        sky = QLinearGradient(0.0, 0.0, 0.0, float(h))
        sky.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#01040a", 0.5)))
        sky.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, "#08121f", 0.8)))
        p.fillRect(0, 0, w, h, QBrush(sky))
        scene_fx.starfield(p, w, h, self.stars, t, theme.NIGHT_BG, theme.STAR,
                           y_max=0.72)
        p.setPen(Qt.PenStyle.NoPen)
        for cu in self.curtains:
            self._curtain(p, w, h, t, cu, breath)
        self._horizon(p, w, h)
        hue = theme.blend(_GREEN, theme.STAR, 0.4)
        _overlay(p, w, w / 2, h * 0.30, h * 0.30 + 40, h * 0.30 + 78, h - 22, c, hue)
