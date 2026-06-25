"""Drifting scene: soft cloud bands easing across a quiet twilight sky.

Low, slow, low-contrast: a handful of blurred grey-violet cloud puffs drift
sideways at gentle, differing speeds across a dusk gradient (deep indigo above
easing to a muted mauve horizon), with a faint moon glow low in the sky and a
hint of stars peeking through the high gaps. Everything is breathed up a touch by
the lung volume, so the sky brightens softly on the inhale. A calm bed for Relax
or Sleep.

Deterministic (seeded puff params + anim-time motion, nothing spawned per
frame). It reads the per-frame ``t`` from the context, which the "Calm visuals"
toggle slows, so its drift eases automatically when reduce-motion is on. Its own
module to keep scenes.py small; registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QLinearGradient, QRadialGradient

from . import theme
from .scenes import _overlay, _qc

_CLOUD = "#6a6580"          # soft grey-violet body
_EDGE = "#8d88a6"           # a slightly lighter rim


class DriftScene:
    name = "drift"

    def __init__(self):
        rng = np.random.default_rng(19)
        # four loose height bands; a few soft puffs each, varied size/speed/phase.
        self.puffs = []
        for band, cy in enumerate((0.30, 0.46, 0.62, 0.78)):
            for _ in range(5):
                self.puffs.append(dict(
                    x=float(rng.random()),
                    y=cy + float(rng.random() - 0.5) * 0.07,
                    sz=0.10 + float(rng.random()) * 0.12 + band * 0.015,
                    sp=0.006 + float(rng.random()) * 0.010 + band * 0.004,
                    a=0.07 + float(rng.random()) * 0.06,
                    ph=float(rng.random()) * 6.28))
        self.puffs.sort(key=lambda d: d["y"])        # far (high) drawn first
        self.stars = [dict(nx=float(rng.random()), ny=float(rng.random()) * 0.34,
                           ph=float(rng.random()) * 6.28,
                           sp=0.2 + float(rng.random()) * 0.5) for _ in range(34)]

    def _sky(self, p, w, h):
        sky = QLinearGradient(0.0, 0.0, 0.0, float(h))
        sky.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#0b0e22", 0.55)))
        sky.setColorAt(0.62, _qc(theme.blend(theme.NIGHT_BG, "#241f3a", 0.55)))
        sky.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, "#3a2c3e", 0.6)))
        p.fillRect(0, 0, w, h, QBrush(sky))

    def _stars(self, p, w, h, t, breath):
        p.setPen(Qt.PenStyle.NoPen)
        for s in self.stars:
            tw = 0.5 + 0.5 * math.sin(t * 0.5 * s["sp"] + s["ph"])
            a = (0.10 + 0.4 * tw) * breath
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, theme.STAR, a), a))
            r = 0.5 + 0.9 * tw
            p.drawEllipse(QPointF(s["nx"] * w, s["ny"] * h), r, r)

    def _moon(self, p, w, h, breath):
        mx, my, mr = w * 0.26, h * 0.30, min(w, h) * 0.06
        halo = QRadialGradient(mx, my, mr * 3.2)
        halo.setColorAt(0.0, _qc(theme.MOON, 0.16 * breath))
        halo.setColorAt(1.0, _qc(theme.MOON, 0.0))
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(mx, my), mr * 3.2, mr * 3.2)
        p.setBrush(_qc(theme.blend(theme.NIGHT_BG, theme.MOON, 0.7), 0.7))
        p.drawEllipse(QPointF(mx, my), mr, mr)

    def _puff(self, p, w, h, cx, cy, rx, a):
        ry = rx * 0.42                               # flattened, cloud-like
        p.save()
        p.translate(cx, cy)
        p.scale(1.0, ry / rx)
        g = QRadialGradient(0.0, 0.0, rx)
        g.setColorAt(0.0, _qc(_EDGE, a))
        g.setColorAt(0.5, _qc(_CLOUD, a * 0.8))
        g.setColorAt(1.0, _qc(_CLOUD, 0.0))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(0.0, 0.0), rx, rx)
        p.restore()

    def draw(self, p, w, h, c):
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        breath = 0.78 + 0.30 * vol                   # sky/clouds brighten on inhale
        self._sky(p, w, h)
        self._stars(p, w, h, t, breath)
        self._moon(p, w, h, breath)
        p.setPen(Qt.PenStyle.NoPen)
        for d in self.puffs:
            x = ((d["x"] + t * d["sp"]) % 1.3) - 0.15   # drift + wrap off-screen
            cx, cy = x * w, d["y"] * h
            rx = d["sz"] * w
            bob = math.sin(t * 0.12 + d["ph"]) * h * 0.006   # the gentlest vertical sway
            self._puff(p, w, h, cx, cy + bob, rx, d["a"] * breath)
        hue = theme.blend(_EDGE, theme.STAR, 0.4)
        _overlay(p, w, w / 2, h * 0.30, h * 0.30 + 40, h * 0.30 + 78, h - 22, c, hue)
