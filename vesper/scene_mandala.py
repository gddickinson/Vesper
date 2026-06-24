"""Breathing mandala scene: a slow, symmetric focal pattern that breathes.

Concentric rings of repeated geometry in radial symmetry (6- and 12-fold) that
**expand on the inhale and contract on the exhale** (the radius follows the breath
volume), rotate very slowly over time with neighbouring rings counter-rotating, and
glow from a soft centre. The colour is the per-phase breath hue, so the four phases
read at a glance. Slow and low-contrast - a steady thing to rest the eye on for
focused-attention meditation. Deterministic (anim-time motion, nothing per frame).

A separate module (scenes.py is large); registered at the bottom of scenes.py.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QPen, QRadialGradient

from . import theme
from .scenes import _overlay, _qc

# (n-fold symmetry, base radius frac, motif, rotation speed, alpha, petal size frac)
_RINGS = [
    dict(n=6, rad=0.16, motif="petal", spin=0.05, a=0.5, sz=0.10),
    dict(n=12, rad=0.27, motif="dot", spin=-0.035, a=0.42, sz=0.030),
    dict(n=12, rad=0.38, motif="petal", spin=0.026, a=0.38, sz=0.085),
    dict(n=24, rad=0.48, motif="dot", spin=-0.02, a=0.30, sz=0.022),
    dict(n=6, rad=0.57, motif="arc", spin=0.016, a=0.26, sz=0.12),
]


class MandalaScene:
    name = "mandala"

    def draw(self, p, w, h, c):
        p.fillRect(0, 0, w, h, _qc(theme.BG))
        cx, cy = w / 2.0, h * 0.46
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        hue = theme.phase_hue(c["phase"]) if running else theme.ACCENT
        glow = theme.glow(hue, 0.4)
        rmax = min(w, h) * 0.5
        breath = 0.82 + 0.30 * vol                      # expand in / contract out

        # soft central glow that pulses with the breath
        gr = rmax * 0.5 * breath
        rg = QRadialGradient(cx, cy, gr)
        rg.setColorAt(0.0, _qc(glow, 0.34 + 0.22 * vol))
        rg.setColorAt(0.5, _qc(hue, 0.12 + 0.10 * vol))
        rg.setColorAt(1.0, _qc(hue, 0.0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(rg))
        p.drawEllipse(QPointF(cx, cy), gr, gr)

        for ring in _RINGS:
            self._ring(p, cx, cy, rmax, t, ring, hue, glow, breath)

        # a faint bounding circle + a bright breathing core
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(_qc(theme.blend(theme.BG, hue, 0.45)), 1))
        p.drawEllipse(QPointF(cx, cy), rmax * 0.66 * breath, rmax * 0.66 * breath)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_qc(glow, 0.5 + 0.3 * vol))
        p.drawEllipse(QPointF(cx, cy), rmax * 0.035 * breath, rmax * 0.035 * breath)

        _overlay(p, w, cx, cy + rmax * 0.62, cy + rmax * 0.62 + 36,
                 cy + rmax * 0.62 + 74, h - 22, c, hue)

    def _ring(self, p, cx, cy, rmax, t, ring, hue, glow, breath):
        n = ring["n"]
        rad = rmax * ring["rad"] * breath
        ang0 = t * ring["spin"]
        col = _qc(glow, ring["a"])
        sz = rmax * ring["sz"] * breath
        motif = ring["motif"]
        if motif == "arc":
            p.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(col)
            pen.setWidthF(2.0)
            p.setPen(pen)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(col)
        for i in range(n):
            a = ang0 + i * (2 * math.pi / n)
            x, y = cx + rad * math.cos(a), cy + rad * math.sin(a)
            if motif == "dot":
                p.drawEllipse(QPointF(x, y), sz, sz)
            elif motif == "petal":
                p.save()
                p.translate(x, y)
                p.rotate(math.degrees(a) + 90)          # point outward
                p.drawEllipse(QRectF(-sz * 0.42, -sz, sz * 0.84, sz * 2.0))
                p.restore()
            else:                                       # arc: a small bowed line
                rr = QRectF(x - sz, y - sz, sz * 2, sz * 2)
                mid = math.degrees(a)
                p.drawArc(rr, int((mid + 200) * 16), int(-40 * 16))
