"""Snowfall scene: slow, soft snow drifting down through a hushed winter night.

A quiet, low-motion bed for sleep: a dark, muted blue-grey sky deepening overhead
and warming to a faint snow-glow at the horizon, with two parallax layers of soft
snowflakes drifting gently down and swaying on a slow wind, and a scatter of dim
high stars. The snow softens and brightens a touch on the inhale, so the screen
keeps a calm breath cue. The flakes are a warm-grey white (not a cold blue), to
stay easy on the eyes late at night.

Deterministic (seeded flake params + anim-time motion, nothing spawned per
frame). It reads the per-frame ``t`` from the context, which the "Calm visuals"
toggle slows, so the drift eases automatically when reduce-motion is on. Its own
module to keep scenes.py small; registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QLinearGradient

from . import theme
from .scenes import _overlay, _qc

_SNOW = "#ece9e3"           # soft warm-grey white (not a cold blue)
_GLOW = "#20304a"           # the faint snow-lit horizon


class SnowScene:
    name = "snow"

    def __init__(self):
        rng = np.random.default_rng(41)
        # near layer: larger, a touch faster, brighter; far layer: small, slow, dim.
        self.near = [dict(x=float(rng.random()), y=float(rng.random()),
                          sp=0.6 + float(rng.random()) * 0.7,
                          sz=1.4 + float(rng.random()) * 1.8,
                          ph=float(rng.random()) * 6.28,
                          sw=0.4 + float(rng.random()) * 0.8) for _ in range(60)]
        self.far = [dict(x=float(rng.random()), y=float(rng.random()),
                         sp=0.25 + float(rng.random()) * 0.35,
                         sz=0.6 + float(rng.random()) * 0.9,
                         ph=float(rng.random()) * 6.28,
                         sw=0.2 + float(rng.random()) * 0.5) for _ in range(90)]
        self.stars = [dict(nx=float(rng.random()), ny=float(rng.random()) * 0.4,
                           ph=float(rng.random()) * 6.28,
                           sp=0.2 + float(rng.random()) * 0.4) for _ in range(30)]

    def _sky(self, p, w, h, breath):
        sky = QLinearGradient(0.0, 0.0, 0.0, float(h))
        sky.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#070b14", 0.5)))
        sky.setColorAt(0.7, _qc(theme.blend(theme.NIGHT_BG, "#0e1626", 0.5)))
        sky.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, _GLOW,
                                            0.45 + 0.18 * breath)))
        p.fillRect(0, 0, w, h, QBrush(sky))

    def _stars(self, p, w, h, t, breath):
        for s in self.stars:
            tw = 0.5 + 0.5 * math.sin(t * 0.5 * s["sp"] + s["ph"])
            a = (0.08 + 0.22 * tw) * breath
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, theme.STAR, a), a))
            r = 0.4 + 0.6 * tw
            p.drawEllipse(QPointF(s["nx"] * w, s["ny"] * h), r, r)

    def _flakes(self, p, w, h, t, layer, fall, base_a, breath):
        a = base_a * breath
        p.setBrush(_qc(_SNOW, a))
        for d in layer:
            y = (d["y"] + t * fall * d["sp"]) % 1.06 - 0.03   # drift down + wrap
            sway = math.sin(t * 0.18 * d["sw"] + d["ph"]) * w * 0.012
            r = d["sz"] * (0.9 + 0.15 * breath)
            p.drawEllipse(QPointF(d["x"] * w + sway, y * h), r, r)

    def draw(self, p, w, h, c):
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        breath = 0.78 + 0.30 * vol                  # snow softens on the inhale
        self._sky(p, w, h, breath)
        p.setPen(Qt.PenStyle.NoPen)
        self._stars(p, w, h, t, breath)
        self._flakes(p, w, h, t, self.far, 0.010, 0.34, breath)   # far: slow + dim
        self._flakes(p, w, h, t, self.near, 0.020, 0.62, breath)  # near: brighter
        hue = theme.blend(_SNOW, theme.ACCENT, 0.25)
        _overlay(p, w, w / 2, h * 0.60, h * 0.60 + 40, h * 0.60 + 78, h - 22, c, hue)
