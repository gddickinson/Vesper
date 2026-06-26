"""Jellyfish scene: slow translucent bells drifting and pulsing in dark water.

A deeply calm bed for Sleep / Relax: a deep blue-black sea, faintly lit from far
above, with a few soft, glowing jellyfish that rise slowly and pulse -- the bell
gently contracting and easing open, trailing wavy tentacles -- while dim plankton
motes drift up through the dark. Everything is low-contrast and slow. The glow and
pulse swell a touch on the inhale, so the screen keeps a quiet breath cue.

Deterministic: seeded jelly/mote params + anim-time motion, nothing spawned per
frame. It reads the per-frame ``t`` from the context, which the "Calm visuals"
toggle slows, so the drift eases automatically when reduce-motion is on. Its own
module to keep scenes.py small; registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QLinearGradient, QPainterPath, QPen, QRadialGradient

from . import theme
from .scenes import _overlay, _qc

# soft translucent hues over deep water (teal / lavender / pink), easy on the eyes
_HUES = ["#7fe3d6", "#b79ce0", "#e6a6c8", "#8fb8ef"]


class JellyfishScene:
    name = "jellyfish"

    def __init__(self):
        rng = np.random.default_rng(57)
        self.jellies = []
        for i in range(5):
            self.jellies.append(dict(
                x=0.12 + 0.76 * float(rng.random()),   # horizontal home
                y=float(rng.random()),                 # start depth (wraps)
                sz=0.10 + 0.07 * float(rng.random()),  # bell radius (frac of min dim)
                rate=0.30 + 0.35 * float(rng.random()),  # pulse speed (slow)
                rise=0.5 + 0.7 * float(rng.random()),  # upward drift speed
                sway=0.5 + 0.8 * float(rng.random()),  # tentacle sway speed
                dx=0.6 + 0.9 * float(rng.random()),    # gentle side-drift rate
                ph=float(rng.random()) * 6.2831,
                hue=_HUES[i % len(_HUES)]))
        self.motes = [dict(x=float(rng.random()), y=float(rng.random()),
                           sp=0.2 + 0.5 * float(rng.random()),
                           sz=0.4 + 1.0 * float(rng.random()),
                           ph=float(rng.random()) * 6.2831) for _ in range(46)]

    def _water(self, p, w, h, breath):
        sea = QLinearGradient(0.0, 0.0, 0.0, float(h))
        sea.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#14365a",
                                            0.40 + 0.14 * breath)))   # surface light
        sea.setColorAt(0.45, _qc(theme.blend(theme.NIGHT_BG, "#0a1c30", 0.5)))
        sea.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, "#01040a", 0.6)))  # the deep
        p.fillRect(0, 0, w, h, QBrush(sea))

    def _motes(self, p, w, h, t, breath):
        p.setPen(Qt.PenStyle.NoPen)
        for m in self.motes:
            y = (m["y"] - t * 0.006 * m["sp"]) % 1.06 - 0.03         # drift up + wrap
            x = (m["x"] + 0.01 * math.sin(t * 0.1 + m["ph"])) % 1.0
            a = (0.05 + 0.10 * (0.5 + 0.5 * math.sin(t * 0.4 + m["ph"]))) * breath
            p.setBrush(_qc(theme.blend("#bfe9ff", theme.STAR, 0.4), a))
            p.drawEllipse(QPointF(x * w, y * h), m["sz"], m["sz"])

    def _jelly(self, p, w, h, t, j, breath):
        pulse = 0.5 + 0.5 * math.sin(t * j["rate"] + j["ph"])        # 0..1 (1=contracted)
        cx = (j["x"] + 0.012 * math.sin(t * 0.07 * j["dx"] + j["ph"])) * w
        cy = ((j["y"] - t * j["rise"] * 0.012) % 1.18 - 0.09) * h - pulse * h * 0.012
        R = j["sz"] * min(w, h)
        bw = R * (1.0 - 0.16 * pulse)                  # bell narrows as it contracts
        bh = R * (0.60 + 0.18 * pulse)                 # ...and lifts/rounds
        hue = j["hue"]
        a = (0.10 + 0.06 * pulse) * (0.85 + 0.30 * breath)
        # soft bioluminescent glow behind the bell
        g = QRadialGradient(cx, cy, bw * 1.7)
        g.setColorAt(0.0, _qc(theme.blend(hue, "#ffffff", 0.25), a * 0.9))
        g.setColorAt(1.0, _qc(hue, 0.0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(cx, cy), bw * 1.7, bh * 1.7)
        # trailing tentacles, wavy and fading downward
        p.setPen(QPen(_qc(theme.blend(hue, "#ffffff", 0.15), a * 1.3), 1.4))
        nt = 5
        for k in range(nt):
            ox = (k / (nt - 1) - 0.5) * bw * 1.05
            path = QPainterPath()
            path.moveTo(cx + ox, cy)
            length = bh * (2.0 + 0.8 * (k % 2))
            steps = 6
            for s in range(1, steps + 1):
                f = s / steps
                yy = cy + length * f
                xx = cx + ox + math.sin(t * 0.8 * j["sway"] + s * 0.7
                                        + j["ph"] + k) * bw * 0.07 * f
                path.lineTo(xx, yy)
            p.drawPath(path)
        # the translucent bell (top dome), with a slightly brighter rim
        p.setPen(QPen(_qc(theme.blend(hue, "#ffffff", 0.35), a * 1.8), 1.6))
        p.setBrush(_qc(hue, a * 1.7))
        p.drawChord(QRectF(cx - bw, cy - bh, 2 * bw, 2 * bh), 0, 180 * 16)

    def draw(self, p, w, h, c):
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        breath = 0.80 + 0.30 * vol                     # glow swells on the inhale
        self._water(p, w, h, breath)
        self._motes(p, w, h, t, breath)
        # draw far (smaller) jellies first so nearer ones layer over them
        for j in sorted(self.jellies, key=lambda d: d["sz"]):
            self._jelly(p, w, h, t, j, breath)
        hue = theme.blend(_HUES[0], theme.ACCENT, 0.3)
        _overlay(p, w, w / 2, h * 0.60, h * 0.60 + 40, h * 0.60 + 78, h - 22, c, hue)
