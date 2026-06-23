"""Animated backgrounds painted behind the 3D face.

The GPU face renders on a transparent background, so the FaceWidget paints one of
these effects first, then composites the head over it. All are calm, low-contrast
and tinted by the current breath-phase ``hue`` so they breathe with the session.
Each painter has ``draw(p, w, h, t, breath, hue)``. ``make(name)``/``names()``.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (QColor, QLinearGradient, QPolygonF, QRadialGradient)

from . import theme


def _qc(hexstr, alpha=1.0):
    c = QColor(hexstr)
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    return c


def warm_overlay(p, w, h, amount):
    """A warm, low-blue dimming wash for the Sleep wind-down. Over-blending this
    dark amber both darkens the view and pulls the blue down — gentler on melatonin
    than a cool screen. ``amount`` 0..1 grows as the session winds toward sleep."""
    if amount <= 0.0:
        return
    p.fillRect(0, 0, w, h, _qc("#2a1305", min(0.6, amount)))


class _None:
    name = "None"

    def draw(self, p, w, h, t, breath, hue):
        pass


class Gradient:
    """A soft vertical wash from the phase hue (top) to night (bottom)."""
    name = "Gradient"

    def draw(self, p, w, h, t, breath, hue):
        g = QLinearGradient(0, 0, 0, h)
        amt = 0.10 + 0.06 * breath
        g.setColorAt(0.0, _qc(theme.blend(theme.BG, hue, amt)))
        g.setColorAt(0.55, _qc(theme.BG))
        g.setColorAt(1.0, _qc(theme.blend(theme.BG, "#000000", 0.4)))
        p.fillRect(0, 0, w, h, g)


class Stars:
    """Deep-space starfield — drifting, twinkling; matches the starry eyes."""
    name = "Stars"

    def __init__(self):
        rng = np.random.default_rng(7)
        self.stars = [dict(nx=float(rng.random()), ny=float(rng.random()),
                           ph=float(rng.random()) * 6.28,
                           sp=0.2 + float(rng.random()) * 0.7,
                           sz=0.6 + float(rng.random()) * 1.7) for _ in range(120)]

    def draw(self, p, w, h, t, breath, hue):
        p.fillRect(0, 0, w, h, _qc(theme.NIGHT_BG))
        p.setPen(Qt.PenStyle.NoPen)
        col = theme.blend(theme.STAR, hue, 0.25)
        for s in self.stars:
            y = (s["ny"] + t * 0.006 * s["sp"]) % 1.0
            tw = 0.5 + 0.5 * math.sin(t * 0.8 * s["sp"] + s["ph"])
            p.setBrush(_qc(col, 0.15 + 0.65 * tw))
            r = s["sz"] * (0.7 + 0.4 * breath)
            p.drawEllipse(QPointF(s["nx"] * w, y * h), r, r)


class Aurora:
    """Slow drifting veils of soft colour — northern-lights calm."""
    name = "Aurora"

    def draw(self, p, w, h, t, breath, hue):
        p.fillRect(0, 0, w, h, _qc(theme.NIGHT_BG))
        p.setPen(Qt.PenStyle.NoPen)
        comp = theme.ACCENT_WARM if hue != theme.ACCENT_WARM else theme.ACCENT
        blobs = [(0.30, 0.35, hue, 0.13, 0.07, 0.55),
                 (0.70, 0.45, comp, 0.10, 0.05, 0.62),
                 (0.50, 0.72, hue, 0.09, 0.03, 0.7)]
        for i, (bx, by, c, a, sa, sr) in enumerate(blobs):
            cx = (bx + 0.08 * math.sin(t * 0.07 + i)) * w
            cy = (by + 0.05 * math.cos(t * 0.05 + i * 1.7)) * h
            rad = min(w, h) * (sr + 0.06 * breath)
            grad = QRadialGradient(cx, cy, rad)
            grad.setColorAt(0.0, _qc(c, (a + sa * math.sin(t * 0.3 + i))))
            grad.setColorAt(1.0, _qc(c, 0.0))
            p.setBrush(grad)
            p.drawEllipse(QPointF(cx, cy), rad, rad)


class Nebula:
    """Layered translucent clouds — a deeper, richer space."""
    name = "Nebula"

    def __init__(self):
        rng = np.random.default_rng(13)
        self.cl = [(float(rng.random()), float(rng.random()),
                    0.4 + float(rng.random()) * 0.5, float(rng.random()) * 6.28)
                   for _ in range(6)]
        self.stars = Stars()

    def draw(self, p, w, h, t, breath, hue):
        p.fillRect(0, 0, w, h, _qc("#04060d"))
        p.setPen(Qt.PenStyle.NoPen)
        comp = theme.ACCENT_WARM
        for i, (bx, by, sr, ph) in enumerate(self.cl):
            c = hue if i % 2 == 0 else comp
            cx = (bx + 0.05 * math.sin(t * 0.04 + ph)) * w
            cy = (by + 0.04 * math.cos(t * 0.03 + ph)) * h
            rad = min(w, h) * sr
            grad = QRadialGradient(cx, cy, rad)
            grad.setColorAt(0.0, _qc(c, 0.06 + 0.03 * math.sin(t * 0.2 + ph)))
            grad.setColorAt(1.0, _qc(c, 0.0))
            p.setBrush(grad)
            p.drawEllipse(QPointF(cx, cy), rad, rad)
        self.stars.draw_overlay = True
        # faint stars over the clouds
        op = p.opacity()
        p.setOpacity(0.6)
        for s in self.stars.stars[::2]:
            tw = 0.5 + 0.5 * math.sin(t * 0.8 * s["sp"] + s["ph"])
            p.setBrush(_qc(theme.STAR, 0.1 + 0.5 * tw))
            p.drawEllipse(QPointF(s["nx"] * w, ((s["ny"] + t * 0.004) % 1.0) * h),
                          s["sz"], s["sz"])
        p.setOpacity(op)


class Underwater:
    """Calm blue-green depths — swaying light rays from the surface + slow bubbles.
    Pairs with the Relax wave scene."""
    name = "Underwater"

    def __init__(self):
        rng = np.random.default_rng(21)
        self.bub = [dict(x=float(rng.random()), ph=float(rng.random()) * 6.28,
                         sp=0.04 + float(rng.random()) * 0.08,
                         sz=1.0 + float(rng.random()) * 2.4) for _ in range(20)]

    def draw(self, p, w, h, t, breath, hue):
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0.0, _qc(theme.blend("#0b303a", theme.ACCENT, 0.12)))
        g.setColorAt(1.0, _qc("#04141a"))
        p.fillRect(0, 0, w, h, g)
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(4):                       # swaying light shafts
            x = (0.18 + 0.21 * i) * w + 0.03 * w * math.sin(t * 0.18 + i)
            beam = QPolygonF([QPointF(x, 0), QPointF(x + 0.05 * w, 0),
                              QPointF(x + 0.12 * w + 0.04 * w * math.sin(t * 0.13 + i),
                                      h), QPointF(x + 0.06 * w, h)])
            p.setBrush(_qc(theme.glow(theme.ACCENT, 0.5), 0.06 + 0.02 * breath))
            p.drawPolygon(beam)
        for b in self.bub:                       # slow rising bubbles
            prog = (t * b["sp"] + b["ph"]) % 1.0
            y = (1.0 - prog) * h
            x = (b["x"] + 0.012 * math.sin(t * 0.5 + b["ph"])) * w
            p.setBrush(_qc(theme.glow(theme.ACCENT, 0.6), 0.16))
            p.drawEllipse(QPointF(x, y), b["sz"], b["sz"])


class Embers:
    """A warm dark hearth — a low glow that breathes, with rising sparks. Cozy."""
    name = "Embers"

    def __init__(self):
        rng = np.random.default_rng(29)
        self.sp = [dict(x=float(rng.random()), ph=float(rng.random()) * 6.28,
                        sp=0.05 + float(rng.random()) * 0.10,
                        sz=0.8 + float(rng.random()) * 1.6,
                        drift=float(rng.random()) - 0.5) for _ in range(44)]

    def draw(self, p, w, h, t, breath, hue):
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0.0, _qc("#1a0d06"))
        g.setColorAt(1.0, _qc("#080402"))
        p.fillRect(0, 0, w, h, g)
        p.setPen(Qt.PenStyle.NoPen)
        glow = QRadialGradient(w * 0.5, h * 1.05, h * 0.75)
        amt = 0.16 + 0.06 * breath + 0.03 * math.sin(t * 1.3)   # the fire breathes
        glow.setColorAt(0.0, _qc("#ff7a2e", max(0.0, amt)))
        glow.setColorAt(1.0, _qc("#ff7a2e", 0.0))
        p.setBrush(glow)
        p.drawRect(0, 0, w, h)
        for s in self.sp:                        # rising, fading sparks
            prog = (t * s["sp"] + s["ph"]) % 1.0
            y = h * (1.0 - prog)
            x = (s["x"] + 0.06 * s["drift"] * prog
                 + 0.01 * math.sin(t * 2 + s["ph"])) * w
            tw = 0.5 + 0.5 * math.sin(t * 4 + s["ph"])
            p.setBrush(_qc(theme.blend("#ffb066", "#ff5a1e", tw), 0.5 * (1.0 - prog)))
            p.drawEllipse(QPointF(x, y), s["sz"], s["sz"])


_CLASSES = {"None": _None, "Stars": Stars, "Aurora": Aurora, "Nebula": Nebula,
            "Gradient": Gradient, "Underwater": Underwater, "Embers": Embers}


def make(name):
    return _CLASSES.get(name, Stars)()


def names():
    return list(_CLASSES.keys())
