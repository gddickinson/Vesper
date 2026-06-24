"""Rain-on-window scene: droplets sliding down glass over a soft blurred glow.

A dark, cosy window at night: a warm streetlamp glow blurred beyond the pane (it
breathes gently with the breath), a faint fogged-glass haze with still
condensation beads, and many raindrops and slow rivulets running down the glass.
All motion is derived from anim time + seeded per-drop parameters, so it is smooth,
deterministic and spawns nothing per frame. Slow and low-contrast (soothing).

A separate module (kept out of the already-large scenes.py); registered there.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QLinearGradient, QRadialGradient

from . import theme
from .scenes import _overlay, _qc

_GLOW = "#d9a85a"          # warm lamp glow beyond the glass (warm, low-blue)
_DROP = "#b9c8df"          # pale, cool droplet


class RainScene:
    name = "rain"

    def __init__(self):
        rng = np.random.default_rng(24)
        self.drops = [dict(
            x=float(rng.random()), y0=float(rng.random()),
            sp=0.03 + float(rng.random()) * 0.10, ln=0.02 + float(rng.random()) * 0.05,
            wob=float(rng.random()) * 6.28, wsp=0.3 + float(rng.random()) * 0.5,
            wd=0.8 + float(rng.random()) * 1.3, lph=float(rng.random()) * 6.28)
            for _ in range(34)]
        self.rivs = [dict(                                   # slow long rivulets
            x=float(rng.random()), y0=float(rng.random()),
            sp=0.012 + float(rng.random()) * 0.03, ln=0.10 + float(rng.random()) * 0.12,
            wob=float(rng.random()) * 6.28, wd=1.4 + float(rng.random()) * 1.4)
            for _ in range(6)]
        self.beads = [dict(                                  # still condensation beads
            x=float(rng.random()), y=float(rng.random()),
            r=0.6 + float(rng.random()) * 1.4, ph=float(rng.random()) * 6.28)
            for _ in range(40)]

    def _streak(self, p, x, y, ln, wd, a):
        """A soft droplet: a faint translucent trail with a brighter rounded head."""
        p.setPen(Qt.PenStyle.NoPen)
        trail = QLinearGradient(x, y - ln, x, y)
        trail.setColorAt(0.0, _qc(_DROP, 0.0))
        trail.setColorAt(1.0, _qc(_DROP, a * 0.6))
        p.setBrush(QBrush(trail))
        p.drawRoundedRect(QRectF(x - wd * 0.5, y - ln, wd, ln), wd * 0.5, wd * 0.5)
        p.setBrush(_qc(theme.blend(_DROP, "#ffffff", 0.4), a))
        p.drawEllipse(QPointF(x, y), wd * 0.9, wd * 1.2)

    def draw(self, p, w, h, c):
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        grad = QLinearGradient(0.0, 0.0, 0.0, float(h))      # dark night-window
        grad.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#0c1422", 0.6)))
        grad.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, "#0e1a2a", 0.9)))
        p.fillRect(0, 0, w, h, QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        gx, gy, gr = w * 0.62, h * 0.40, min(w, h) * (0.42 + 0.05 * vol)
        glow = QRadialGradient(gx, gy, gr)                   # warm lamp, breathing
        glow.setColorAt(0.0, _qc(_GLOW, 0.22 + 0.12 * vol))
        glow.setColorAt(0.45, _qc(_GLOW, 0.08 + 0.05 * vol))
        glow.setColorAt(1.0, _qc(_GLOW, 0.0))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(gx, gy), gr, gr)
        g2r = min(w, h) * 0.4                                 # faint cool glow, depth
        g2 = QRadialGradient(w * 0.25, h * 0.72, g2r)
        g2.setColorAt(0.0, _qc(theme.blend(_GLOW, theme.STAR, 0.6), 0.06))
        g2.setColorAt(1.0, _qc(theme.STAR, 0.0))
        p.setBrush(QBrush(g2))
        p.drawEllipse(QPointF(w * 0.25, h * 0.72), g2r, g2r)
        p.fillRect(0, 0, w, h, _qc("#cfd9ea", 0.025))        # fogged-glass haze
        for b in self.beads:
            tw = 0.4 + 0.6 * math.sin(t * 0.5 + b["ph"])
            p.setBrush(_qc(theme.blend(_DROP, "#ffffff", 0.3),
                           0.06 + 0.10 * max(0.0, tw)))
            p.drawEllipse(QPointF(b["x"] * w, b["y"] * h), b["r"], b["r"])
        for r in self.rivs:                                  # long, slow rivulets
            y = ((r["y0"] + r["sp"] * t) % 1.18) - 0.09
            x = (r["x"] + 0.012 * math.sin(t * 0.4 + r["wob"])) * w
            self._streak(p, x, y * h, r["ln"] * h, r["wd"], 0.16)
        for d in self.drops:                                 # sliding drops
            y = ((d["y0"] + d["sp"] * t) % 1.12) - 0.06
            x = (d["x"] + 0.010 * math.sin(t * d["wsp"] + d["wob"])) * w
            ln = d["ln"] * (0.6 + 0.4 * math.sin(t * 0.3 + d["lph"]))   # merge/elongate
            self._streak(p, x, y * h, ln * h, d["wd"], 0.22)
        hue = theme.blend(_GLOW, theme.STAR, 0.4)
        _overlay(p, w, w / 2, h * 0.30, h * 0.30 + 40, h * 0.30 + 78, h - 22, c, hue)
