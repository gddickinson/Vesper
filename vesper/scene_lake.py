"""Starlit Lake scene: a calm dark lake at night, with the stars and moon
shimmering in reflection on the still water.

A deeply serene bed for Sleep / Relax. The upper sky holds a soft starfield and a
low moon; below the horizon the dark water mirrors them -- each star a fainter,
gently-trembling twin, and a long vertical *moonglade* of glittering dashes
running down from the moon. A faint mist hangs on the horizon. Everything is
low-contrast and almost still; the moon's halo, its glade and the water's shimmer
swell a touch on the inhale, so the screen keeps a quiet breath cue.

Deterministic: a seeded starfield + anim-time motion, nothing spawned per frame.
It reads the per-frame ``t`` from the context, which the "Calm visuals" toggle
slows, so the shimmer eases automatically when reduce-motion is on. Its own module
to keep scenes.py small; registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QLinearGradient, QPen, QRadialGradient

from . import theme
from .scenes import _overlay, _qc

_HZ = 0.56                                          # horizon, as a fraction of height


class StarlitLake:
    name = "lake"

    def __init__(self):
        rng = np.random.default_rng(29)
        # stars live in the sky band (ny in 0..1 -> mapped above the horizon)
        self.stars = [dict(nx=float(rng.random()), ny=float(rng.random()),
                           ph=float(rng.random()) * 6.2831,
                           sp=0.2 + 0.6 * float(rng.random()),
                           br=0.4 + 0.6 * float(rng.random())) for _ in range(60)]

    def _sky(self, p, w, h):
        grad = QLinearGradient(0.0, 0.0, 0.0, float(h) * _HZ)
        grad.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#000007", 0.55)))
        grad.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, "#0b1430", 0.25)))
        p.fillRect(0, 0, w, int(h * _HZ) + 1, QBrush(grad))

    def _water(self, p, w, h, breath):
        hz = int(h * _HZ)
        wat = QLinearGradient(0.0, float(hz), 0.0, float(h))
        wat.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#16294a",
                                            0.30 + 0.10 * breath)))   # lit near shore
        wat.setColorAt(0.5, _qc(theme.blend(theme.NIGHT_BG, "#070f1f", 0.5)))
        wat.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, "#01040a", 0.6)))  # the deep
        p.fillRect(0, hz, w, h - hz, QBrush(wat))

    def _mist(self, p, w, h):
        hz = h * _HZ
        band = int(h * 0.06)
        mist = QLinearGradient(0.0, hz - band, 0.0, hz + band)
        col = theme.blend(theme.NIGHT_BG, theme.MOON, 0.5)
        mist.setColorAt(0.0, _qc(col, 0.0))
        mist.setColorAt(0.5, _qc(col, 0.10))
        mist.setColorAt(1.0, _qc(col, 0.0))
        p.fillRect(0, int(hz - band), w, 2 * band, QBrush(mist))

    def _stars(self, p, w, h, t, breath):
        hz = h * _HZ
        p.setPen(Qt.PenStyle.NoPen)
        for s in self.stars:
            sx = s["nx"] * w
            sy = (s["ny"] * 0.92) * hz                       # within the sky band
            tw = 0.5 + 0.5 * math.sin(t * 0.7 * s["sp"] + s["ph"])
            a = (0.25 + 0.7 * tw) * s["br"]
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, theme.STAR, a)))
            r = 0.5 + 1.5 * tw * s["br"]
            p.drawEllipse(QPointF(sx, sy), r, r)
            # the trembling reflection below the horizon (foreshortened + shimmered)
            ry = hz + (hz - sy) * 0.85
            if ry < h - 2:
                shim = math.sin(t * 1.1 * s["sp"] + s["ph"] * 2.0) * w * 0.006
                p.setBrush(_qc(theme.blend(theme.NIGHT_BG, theme.STAR,
                                           a * (0.30 + 0.18 * tw))))
                p.drawEllipse(QPointF(sx + shim, ry), r * 0.9, r * 0.6)

    def _moon(self, p, w, h, t, breath):
        mx, my, mr = w * 0.70, h * 0.20, min(w, h) * 0.07
        halo_r = mr * (2.3 + 1.0 * (breath - 0.8) / 0.3)
        halo = QRadialGradient(mx, my, halo_r)
        halo.setColorAt(0.0, _qc(theme.MOON, 0.16 + 0.12 * (breath - 0.8) / 0.3))
        halo.setColorAt(1.0, _qc(theme.MOON, 0.0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(mx, my), halo_r, halo_r)
        p.setBrush(_qc(theme.MOON))
        p.drawEllipse(QPointF(mx, my), mr, mr)
        off = (0.40 + 0.10 * math.sin(t * 0.01)) * mr        # slow crescent terminator
        p.setBrush(_qc(theme.blend(theme.NIGHT_BG, "#000007", 0.28)))
        p.drawEllipse(QPointF(mx + off, my - off * 0.3), mr * 1.05, mr * 1.05)
        self._moonglade(p, w, h, t, mx, breath)

    def _moonglade(self, p, w, h, t, mx, breath):
        """A vertical column of glittering dashes from the horizon down -- the
        moon's long reflection trembling on the water."""
        hz = h * _HZ
        n = 22
        for i in range(n):
            f = i / (n - 1)                                   # 0 near horizon .. 1 deep
            y = hz + f * (h - hz)
            spread = w * (0.02 + 0.12 * f)                    # widens toward the viewer
            wob = math.sin(t * 1.3 + i * 0.9) * spread * 0.5
            length = spread * (0.5 + 0.5 * abs(math.sin(t * 0.9 + i * 0.7)))
            a = (0.16 + 0.16 * math.sin(t * 1.6 + i * 1.1)) * breath * (1.0 - 0.5 * f)
            p.setPen(QPen(_qc(theme.blend(theme.MOON, "#ffffff", 0.2), max(0.0, a)),
                          1.0 + 1.4 * (1.0 - f)))
            cx = mx + wob
            p.drawLine(QPointF(cx - length, y), QPointF(cx + length, y))

    def draw(self, p, w, h, c):
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        breath = 0.80 + 0.30 * vol                           # glow swells on the inhale
        self._sky(p, w, h)
        self._water(p, w, h, breath)
        self._stars(p, w, h, t, breath)
        self._moon(p, w, h, t, breath)
        self._mist(p, w, h)
        hue = theme.blend(theme.STAR, theme.MOON, 0.4)
        _overlay(p, w, w / 2, h * 0.64, h * 0.64 + 40, h * 0.64 + 78, h - 22, c, hue)
