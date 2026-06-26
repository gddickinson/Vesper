"""Winter Cabin scene: a small warm-lit cabin nestled in deep snow on a starry
winter night, with snow falling softly and smoke curling from the chimney.

A cosy Sleep / Relax bed -- the warm amber windows are the one point of light in a
hushed blue-white world: dark snow-tipped pines behind, a soft snow mound below, a
gentle fall of flakes, and a thin ribbon of woodsmoke rising and drifting away. The
window glow swells a touch on the inhale, so the screen keeps a quiet breath cue.

Deterministic: seeded stars + flakes + anim-time motion, nothing spawned per frame.
It reads the per-frame ``t`` from the context, which the "Calm visuals" toggle
slows, so the snow eases automatically when reduce-motion is on. Its own module to
keep scenes.py small; registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QLinearGradient, QPen, QPolygonF

from . import theme
from .scenes import _overlay, _qc

_SNOW = "#e7eef6"
_WOOD, _WOOD_DK = "#4a3322", "#33241a"
_WARM = "#ffcf86"                                   # the glow of the windows


class WinterCabin:
    name = "cabin"

    def __init__(self):
        rng = np.random.default_rng(41)
        self.stars = [dict(x=float(rng.random()), y=0.5 * float(rng.random()),
                           ph=float(rng.random()) * 6.2831) for _ in range(34)]
        self.flakes = [dict(x=float(rng.random()), y=float(rng.random()),
                            sp=0.4 + 0.7 * float(rng.random()),
                            sz=0.6 + 1.4 * float(rng.random()),
                            ph=float(rng.random()) * 6.2831) for _ in range(54)]

    def _sky(self, p, w, h, t):
        grad = QLinearGradient(0.0, 0.0, 0.0, float(h))
        grad.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#000010", 0.5)))
        grad.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, "#1a2740", 0.4)))
        p.fillRect(0, 0, w, h, QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        for s in self.stars:
            tw = 0.5 + 0.5 * math.sin(t * 0.6 + s["ph"])
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, theme.STAR, 0.2 + 0.6 * tw)))
            p.drawEllipse(QPointF(s["x"] * w, s["y"] * h), 0.6 + tw, 0.6 + tw)

    def _pines(self, p, w, h):
        base = h * 0.66
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(7):
            px = w * (0.06 + 0.14 * i)
            ph = h * (0.18 + 0.04 * ((i * 3) % 4))
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, "#16203a", 0.7)))
            p.drawPolygon(QPolygonF([QPointF(px, base - ph),
                                     QPointF(px - ph * 0.45, base),
                                     QPointF(px + ph * 0.45, base)]))
            p.setBrush(_qc(_SNOW, 0.55))                    # snow cap on the tip
            p.drawPolygon(QPolygonF([QPointF(px, base - ph),
                                     QPointF(px - ph * 0.16, base - ph * 0.6),
                                     QPointF(px + ph * 0.16, base - ph * 0.6)]))

    def _ground(self, p, w, h):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_qc(theme.blend(_SNOW, "#9fb6d0", 0.35)))
        p.drawRoundedRect(QRectF(-w * 0.1, h * 0.7, w * 1.2, h * 0.6), h * 0.18, h * 0.18)
        p.setBrush(_qc(_SNOW, 0.85))
        p.drawRoundedRect(QRectF(-w * 0.1, h * 0.78, w * 1.2, h * 0.6), h * 0.16, h * 0.16)

    def _cabin(self, p, w, h, t, breath):
        cx, by = w * 0.56, h * 0.78
        cw, ch = w * 0.26, h * 0.2
        p.setPen(Qt.PenStyle.NoPen)
        # smoke from the chimney: soft puffs rising + drifting, fading
        for i in range(6):
            f = (i / 6.0 + (t * 0.05) % 1.0) % 1.0
            sx = cx + cw * 0.34 + math.sin(t * 0.5 + i) * w * 0.02 + f * w * 0.05
            sy = by - ch - h * 0.04 - f * h * 0.22
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, "#c9d4e4", 0.5),
                           0.16 * (1.0 - f)))
            p.drawEllipse(QPointF(sx, sy), w * (0.018 + 0.03 * f), w * (0.018 + 0.03 * f))
        p.setBrush(_qc(_WOOD_DK))                           # chimney
        p.drawRect(QRectF(cx + cw * 0.26, by - ch - h * 0.05, cw * 0.16, h * 0.07))
        p.setBrush(_qc(_WOOD))                              # cabin body
        p.drawRect(QRectF(cx - cw / 2, by - ch, cw, ch))
        for k in range(1, 4):                               # log lines
            p.setPen(QPen(_qc(_WOOD_DK, 0.5), 1.0))
            p.drawLine(QPointF(cx - cw / 2, by - ch + k * ch / 4),
                       QPointF(cx + cw / 2, by - ch + k * ch / 4))
            p.setPen(Qt.PenStyle.NoPen)
        a = 0.65 + 0.35 * (breath - 0.8) / 0.3              # windows glow with the breath
        for s in (-1, 1):                                   # two warm windows
            wx = cx + s * cw * 0.24
            p.setBrush(_qc(theme.blend(_WARM, "#fff4d8", 0.3), a))
            p.drawRect(QRectF(wx - cw * 0.1, by - ch * 0.74, cw * 0.2, ch * 0.34))
            p.setPen(QPen(_qc(_WOOD_DK, 0.7), 1.2))         # window cross
            p.drawLine(QPointF(wx, by - ch * 0.74), QPointF(wx, by - ch * 0.4))
            p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_qc(theme.blend(_WOOD_DK, "#000000", 0.3)))   # door
        p.drawRoundedRect(QRectF(cx - cw * 0.08, by - ch * 0.42, cw * 0.16, ch * 0.42),
                          cw * 0.05, cw * 0.05)
        p.setBrush(_qc(_SNOW))                              # snow-laden roof
        p.drawPolygon(QPolygonF([QPointF(cx - cw * 0.62, by - ch),
                                 QPointF(cx + cw * 0.62, by - ch),
                                 QPointF(cx, by - ch - h * 0.1)]))
        # the warm glow spills softly onto the snow below the windows
        glow = QLinearGradient(0.0, by - ch * 0.4, 0.0, by + h * 0.06)
        glow.setColorAt(0.0, _qc(_WARM, 0.12 * a))
        glow.setColorAt(1.0, _qc(_WARM, 0.0))
        p.fillRect(QRectF(cx - cw * 0.7, by - ch * 0.4, cw * 1.4, ch + h * 0.06),
                   QBrush(glow))

    def _snowfall(self, p, w, h, t):
        p.setPen(Qt.PenStyle.NoPen)
        for f in self.flakes:
            y = (f["y"] + t * 0.012 * f["sp"]) % 1.06 - 0.03
            x = (f["x"] + 0.012 * math.sin(t * 0.3 + f["ph"])) % 1.0
            p.setBrush(_qc("#ffffff", 0.18 + 0.2 * (0.5 + 0.5 * math.sin(f["ph"]))))
            p.drawEllipse(QPointF(x * w, y * h), f["sz"], f["sz"])

    def draw(self, p, w, h, c):
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        breath = 0.80 + 0.30 * vol
        self._sky(p, w, h, t)
        self._pines(p, w, h)
        self._ground(p, w, h)
        self._cabin(p, w, h, t, breath)
        self._snowfall(p, w, h, t)
        hue = theme.blend(_WARM, theme.STAR, 0.4)
        _overlay(p, w, w / 2, h * 0.16, h * 0.16 + 38, h * 0.16 + 72, h - 22, c, hue)
