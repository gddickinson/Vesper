"""Small, calm visual-effect helpers shared by the ambient scenes.

Each is a tiny stateful object a scene holds across frames and calls from its
``draw``. Everything here is deliberately slow, dim and low-contrast — motes
that barely drift, clouds that ooze, a shooting star that is rare and faint — so
the additions soothe rather than distract. Pure QPainter + a seeded RNG.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QRadialGradient


def qc(hexstr, alpha=1.0):
    c = QColor(hexstr)
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    return c


class Motes:
    """A scatter of dim particles drifting slowly upward (dust caught in light)."""

    def __init__(self, n=16, seed=5):
        rng = np.random.default_rng(seed)
        self.p = [dict(x=float(rng.random()), y=float(rng.random()),
                       r=0.6 + float(rng.random()) * 1.6,
                       sx=(float(rng.random()) - 0.5) * 0.006,
                       sy=-(0.004 + float(rng.random()) * 0.010),
                       ph=float(rng.random()) * 6.2831,
                       sp=0.3 + float(rng.random()) * 0.6) for _ in range(n)]

    def draw(self, p, w, h, t, hue, alpha=0.5):
        p.setPen(Qt.PenStyle.NoPen)
        for m in self.p:
            x = (m["x"] + m["sx"] * t) % 1.0
            y = (m["y"] + m["sy"] * t) % 1.0
            tw = 0.5 + 0.5 * math.sin(t * m["sp"] + m["ph"])
            p.setBrush(qc(hue, alpha * (0.15 + 0.6 * tw)))
            r = m["r"] * (0.7 + 0.5 * tw)
            p.drawEllipse(QPointF(x * w, y * h), r, r)


class Clouds:
    """A few soft translucent bands oozing across the sky."""

    def __init__(self, n=4, seed=7):
        rng = np.random.default_rng(seed)
        self.c = [dict(y=0.08 + float(rng.random()) * 0.42,
                       x=float(rng.random()),
                       rw=0.26 + float(rng.random()) * 0.26,
                       rh=0.05 + float(rng.random()) * 0.05,
                       sp=0.004 + float(rng.random()) * 0.008) for _ in range(n)]

    def draw(self, p, w, h, t, col):
        p.setPen(Qt.PenStyle.NoPen)
        for c in self.c:
            x = ((c["x"] + c["sp"] * t) % 1.3 - 0.15) * w
            cy, rw, rh = c["y"] * h, c["rw"] * w, c["rh"] * h
            grad = QRadialGradient(x, cy, rw)
            grad.setColorAt(0.0, col)
            grad.setColorAt(1.0, qc(col.name(), 0.0))
            p.setBrush(QBrush(grad))
            p.save()
            p.translate(x, cy)
            p.scale(1.0, rh / rw)
            p.drawEllipse(QPointF(0, 0), rw, rw)
            p.restore()


class ShootingStar:
    """A rare, slow, faint streak across the upper sky."""

    def __init__(self, seed=9, period=(14.0, 34.0)):
        self.rng = np.random.default_rng(seed)
        self.period = period
        self.next_t = None
        self.active = None

    def _schedule(self, t):
        self.next_t = t + float(self.rng.uniform(*self.period))

    def draw(self, p, w, h, t, col):
        if self.next_t is None:
            self._schedule(t)
            return
        if self.active is None:
            if t >= self.next_t:
                y0 = float(self.rng.uniform(0.05, 0.4))
                x0 = float(self.rng.uniform(0.1, 0.6))
                ang = float(self.rng.uniform(0.15, 0.45))   # gentle downslope
                self.active = dict(t0=t, dur=1.8, x0=x0, y0=y0, ang=ang,
                                   length=0.16 + float(self.rng.random()) * 0.1)
            return
        age = (t - self.active["t0"]) / self.active["dur"]
        if age >= 1.0:
            self.active = None
            self._schedule(t)
            return
        a = self.active
        fade = math.sin(math.pi * age)                      # in then out
        hx = (a["x0"] + age * a["length"] * 1.4) * w
        hy = (a["y0"] + age * a["length"] * a["ang"] * 1.4) * h
        tx = hx - math.cos(a["ang"]) * a["length"] * w * 0.5
        ty = hy - math.sin(a["ang"]) * a["length"] * h * 0.5
        from PySide6.QtGui import QPen
        pen = QPen(qc(col, 0.7 * fade))
        pen.setWidthF(1.4)
        p.setPen(pen)
        p.drawLine(QPointF(tx, ty), QPointF(hx, hy))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qc(col, 0.8 * fade))
        p.drawEllipse(QPointF(hx, hy), 1.8, 1.8)


def starfield(p, w, h, stars, t, bg, star_col, y_max=1.0):
    """Draw a list of twinkling stars (dicts nx/ny/ph/sp) within y < y_max*h."""
    p.setPen(Qt.PenStyle.NoPen)
    for s in stars:
        if s["ny"] > y_max:
            continue
        tw = 0.5 + 0.5 * math.sin(t * 0.8 * s["sp"] + s["ph"])
        p.setBrush(qc(_blend(bg, star_col, 0.2 + 0.7 * tw)))
        r = 0.5 + 1.4 * tw
        p.drawEllipse(QPointF(s["nx"] * w, s["ny"] * h), r, r)


def _blend(a, b, f):
    ca, cb = QColor(a), QColor(b)
    f = max(0.0, min(1.0, f))
    return QColor(int(ca.red() + (cb.red() - ca.red()) * f),
                  int(ca.green() + (cb.green() - ca.green()) * f),
                  int(ca.blue() + (cb.blue() - ca.blue()) * f)).name()
