"""Lanterns scene: warm paper-lantern lights drifting slowly up through the dark.

A deliberately low-blue, low-motion bed for sleep: a near-black sky warming to a
deep ember glow at the horizon, with a handful of soft amber lanterns rising
gently and wrapping back below, each flickering a little out of step with the
others. They breathe with you -- glowing a touch brighter and larger on the
inhale -- so the screen keeps a calm breath cue without any cool/blue light. A
faint far layer of tiny embers adds depth.

Deterministic (seeded lantern params + anim-time motion, nothing spawned per
frame). It reads the per-frame ``t`` from the context, which the "Calm visuals"
toggle slows, so the drift eases automatically when reduce-motion is on. Its own
module to keep scenes.py small; registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QLinearGradient, QRadialGradient

from . import theme
from .scenes import _overlay, _qc

_CORE = "#f4c073"           # warm lantern core
_GLOW = "#e8954a"           # amber halo
_EMBER_BOTTOM = "#1a0f06"   # the deep, warm ember tone low in the sky


class LanternsScene:
    name = "lanterns"

    def __init__(self):
        rng = np.random.default_rng(29)
        # the lanterns: a base column, a rise speed, a size, a sway + flicker phase.
        self.lanterns = [dict(
            x=0.06 + float(rng.random()) * 0.88,
            y=float(rng.random()),
            sz=0.018 + float(rng.random()) * 0.026,
            sp=0.5 + float(rng.random()) * 0.9,
            a=0.5 + float(rng.random()) * 0.4,
            ph=float(rng.random()) * 6.28) for _ in range(13)]
        self.lanterns.sort(key=lambda d: d["sz"])     # small/far drawn first
        # a faint far layer of tiny embers for depth (slower, dimmer)
        self.embers = [dict(x=float(rng.random()), y=float(rng.random()),
                            sp=0.2 + float(rng.random()) * 0.5,
                            ph=float(rng.random()) * 6.28) for _ in range(40)]

    def _sky(self, p, w, h, breath):
        sky = QLinearGradient(0.0, 0.0, 0.0, float(h))
        sky.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#000005", 0.5)))
        sky.setColorAt(0.66, _qc(theme.NIGHT_BG))
        sky.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, _EMBER_BOTTOM,
                                            0.55 + 0.20 * breath)))
        p.fillRect(0, 0, w, h, QBrush(sky))

    def _embers(self, p, w, h, t, breath):
        p.setPen(Qt.PenStyle.NoPen)
        for e in self.embers:
            y = (e["y"] - t * 0.004 * e["sp"]) % 1.0
            tw = 0.5 + 0.5 * math.sin(t * 0.4 * e["sp"] + e["ph"])
            a = (0.06 + 0.20 * tw) * breath
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, _CORE, a), a))
            r = 0.4 + 0.7 * tw
            p.drawEllipse(QPointF(e["x"] * w, y * h), r, r)

    def _lantern(self, p, cx, cy, r, a, breath):
        halo = QRadialGradient(cx, cy, r * 6.0)
        halo.setColorAt(0.0, _qc(_GLOW, 0.30 * a * breath))
        halo.setColorAt(0.4, _qc(_GLOW, 0.12 * a * breath))
        halo.setColorAt(1.0, _qc(_GLOW, 0.0))
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(cx, cy), r * 6.0, r * 6.0)
        p.setBrush(_qc(_CORE, min(1.0, 0.85 * a)))    # the warm body
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.setBrush(_qc("#fff0d6", min(1.0, 0.6 * a)))  # a bright inner point
        p.drawEllipse(QPointF(cx, cy), r * 0.45, r * 0.45)

    def draw(self, p, w, h, c):
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        breath = 0.74 + 0.34 * vol                    # lanterns swell on the inhale
        self._sky(p, w, h, breath)
        self._embers(p, w, h, t, breath)
        p.setPen(Qt.PenStyle.NoPen)
        for d in self.lanterns:
            y = (d["y"] - t * 0.012 * d["sp"]) % 1.12 - 0.06   # rise + wrap below
            sway = math.sin(t * 0.14 * d["sp"] + d["ph"]) * w * 0.018
            flick = 0.82 + 0.18 * math.sin(t * 0.7 + d["ph"] * 2.0)
            cx, cy = d["x"] * w + sway, y * h
            r = d["sz"] * min(w, h) * (0.9 + 0.18 * breath)
            self._lantern(p, cx, cy, r, d["a"] * flick, breath)
        hue = theme.blend(_CORE, theme.TEXT, 0.45)
        _overlay(p, w, w / 2, h * 0.60, h * 0.60 + 40, h * 0.60 + 78, h - 22, c, hue)
