"""An optional, gentle 'weather' overlay drawn on top of any scene.

Snow drifting down, leaves tumbling, bubbles rising, or fireflies twinkling - a
thin, low-contrast layer that never gets busy. All motion is derived from anim
time + seeded per-particle parameters (deterministic; nothing per frame is
random), so it stays smooth and calm over any backdrop. Held by ``VizWidget``.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QRadialGradient

from . import theme

KINDS = ["off", "snow", "leaves", "bubbles", "fireflies"]
_N = {"snow": 56, "leaves": 22, "bubbles": 34, "fireflies": 28}
_LEAF = ["#b5732e", "#9c5a2a", "#c98a3a", "#7d8c3a"]


def _qc(hexstr, a=1.0):
    c = QColor(hexstr)
    c.setAlphaF(max(0.0, min(1.0, a)))
    return c


class ParticleLayer:
    def __init__(self):
        self.kind = "off"
        self._p = []
        self._for = None

    def set_kind(self, kind):
        self.kind = kind if kind in KINDS else "off"

    def _build(self):
        rng = np.random.default_rng(33)
        self._p = [dict(x=float(rng.random()), y=float(rng.random()),
                        sp=0.3 + float(rng.random()) * 0.8,
                        ph=float(rng.random()) * 6.2831,
                        sz=float(rng.random())) for _ in range(_N.get(self.kind, 0))]
        self._for = self.kind

    def draw(self, p, w, h, t, vol=0.5):
        if self.kind == "off":
            return
        if self._for != self.kind:
            self._build()
        getattr(self, "_" + self.kind)(p, w, h, t)

    def _snow(self, p, w, h, t):
        p.setPen(Qt.PenStyle.NoPen)
        col = theme.blend(theme.BG, "#ffffff", 0.85)
        for d in self._p:
            y = (d["y"] + (0.02 + 0.03 * d["sp"]) * t) % 1.05
            x = (d["x"] + 0.012 * math.sin(t * 0.5 * d["sp"] + d["ph"])) % 1.0
            r = 1.0 + 2.0 * d["sz"]
            p.setBrush(_qc(col, 0.25 + 0.4 * d["sz"]))
            p.drawEllipse(QPointF(x * w, y * h), r, r)

    def _leaves(self, p, w, h, t):
        p.setPen(Qt.PenStyle.NoPen)
        for i, d in enumerate(self._p):
            y = (d["y"] + (0.015 + 0.02 * d["sp"]) * t) % 1.1
            x = (d["x"] + 0.05 * math.sin(t * 0.4 * d["sp"] + d["ph"])) % 1.0
            p.save()
            p.translate(x * w, y * h)
            p.rotate((t * 36 * d["sp"] + d["ph"] * 57) % 360)
            p.setBrush(_qc(theme.blend(theme.BG, _LEAF[i % 4], 0.7), 0.5))
            s = 3.0 + 3.0 * d["sz"]
            p.drawEllipse(QRectF(-s * 0.5, -s, s, s * 2))
            p.restore()

    def _bubbles(self, p, w, h, t):
        col = theme.blend(theme.BG, theme.ACCENT, 0.7)
        for d in self._p:
            y = (d["y"] - (0.02 + 0.03 * d["sp"]) * t) % 1.05      # rise
            x = (d["x"] + 0.02 * math.sin(t * 0.7 * d["sp"] + d["ph"])) % 1.0
            r = 1.5 + 4.0 * d["sz"]
            pen = QPen(_qc(col, 0.22 + 0.25 * d["sz"]))
            pen.setWidthF(1.2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(x * w, y * h), r, r)
        p.setPen(Qt.PenStyle.NoPen)

    def _fireflies(self, p, w, h, t):
        p.setPen(Qt.PenStyle.NoPen)
        col = "#cfe89a"
        for d in self._p:
            x = (d["x"] + 0.015 * math.sin(t * 0.3 * d["sp"] + d["ph"])) % 1.0
            y = (d["y"] + 0.012 * math.cos(t * 0.25 * d["sp"] + d["ph"] * 1.3)) % 1.0
            tw = 0.5 + 0.5 * math.sin(t * 1.1 * d["sp"] + d["ph"])
            a = 0.08 + 0.6 * max(0.0, tw) ** 2
            r = 1.2 + 1.6 * d["sz"]
            cx, cy = x * w, y * h
            g = QRadialGradient(cx, cy, r * 4)
            g.setColorAt(0.0, _qc(col, a * 0.6))
            g.setColorAt(1.0, _qc(col, 0.0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(cx, cy), r * 4, r * 4)
            p.setBrush(_qc(theme.blend(col, "#ffffff", 0.4), a))
            p.drawEllipse(QPointF(cx, cy), r, r)
