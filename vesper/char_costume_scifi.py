"""Sci-fi head costumes drawn ON TOP of any 2D character (space helmet, HUD
visor, alien antennae, robot aerial). Each ``fn(p, hd, a, hue)`` paints over the
:class:`~vesper.char_base.Head` anchor (``hd.cx/cy/R/top``) with soft, soothing
glows for the bedtime app. Pure QPainter, no assets.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme


def _bezier(p0, p1, p2, n=12):
    """Sample a quadratic curve p0->p2 (control p1) into a list of points."""
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def _orb(p, x, y, r, hue, glow):
    """A soft glowing orb (radial halo + bright core)."""
    gl = QRadialGradient(x, y, r * 1.9)
    gl.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.55), 0.65 + 0.3 * glow))
    gl.setColorAt(0.5, B.qc(hue, 0.4 + 0.35 * glow))
    gl.setColorAt(1.0, B.qc(hue, 0.0))
    p.setPen(B.NOPEN)
    p.setBrush(QBrush(gl))
    p.drawEllipse(QPointF(x, y), r * 1.9, r * 1.9)
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.55), 0.9))
    p.drawEllipse(QPointF(x, y), r * 0.5, r * 0.5)


def _spacehelmet(p, hd, a, hue):                  # translucent bubble dome + collar
    cx, cy, R = hd.cx, hd.cy, hd.R
    Rr = R * 1.28
    p.setPen(B.NOPEN)
    g = QRadialGradient(cx - Rr * 0.32, cy - Rr * 0.36, Rr * 1.7)   # sheen + wash
    g.setColorAt(0.0, B.qc("#ffffff", 0.13 + 0.06 * a.breath))
    g.setColorAt(0.45, B.qc("#bfe4ff", 0.10))
    g.setColorAt(1.0, B.qc("#bfe4ff", 0.04))
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(cx, cy), Rr, Rr)
    B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.5), 0.85), R * 0.05)   # bright rim
    p.drawArc(QRectF(cx - Rr, cy - Rr, Rr * 2, Rr * 2), 0, 360 * 16)
    B.pen(p, B.qc("#ffffff", 0.32), R * 0.07)                         # specular glint
    p.drawArc(QRectF(cx - Rr * 0.74, cy - Rr * 0.8, Rr * 1.1, Rr * 1.1),
              66 * 16, 74 * 16)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(hue, "#2a3340", 0.35)))               # neck collar
    p.drawRoundedRect(QRectF(cx - R * 0.92, cy + R * 0.94, R * 1.84, R * 0.34),
                      R * 0.16, R * 0.16)
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.45), 0.5))          # metallic band
    p.drawRoundedRect(QRectF(cx - R * 0.92, cy + R * 0.97, R * 1.84, R * 0.08),
                      R * 0.04, R * 0.04)
    _orb(p, cx + Rr * 0.86, cy - R * 0.34, R * 0.1, hue, a.breath)    # status light


def _visor(p, hd, a, hue):                        # cyber HUD band over the brow
    cx, cy, R = hd.cx, hd.cy, hd.R
    y = cy - R * 0.1
    p.setPen(B.NOPEN)
    p.setBrush(B.qc("#0c1620"))                                      # dark glossy band
    p.drawRoundedRect(QRectF(cx - R * 0.92, y - R * 0.28, R * 1.84, R * 0.56),
                      R * 0.22, R * 0.28)
    p.setBrush(B.qc("#ffffff", 0.06))                               # top gloss sheen
    p.drawRoundedRect(QRectF(cx - R * 0.84, y - R * 0.21, R * 1.68, R * 0.15),
                      R * 0.08, R * 0.08)
    neon = theme.blend(hue, "#ffffff", 0.45)
    g = QRadialGradient(cx, y + R * 0.04, R * 0.95)                  # scan-line glow
    g.setColorAt(0.0, B.qc(neon, 0.45 + 0.3 * a.breath))
    g.setColorAt(1.0, B.qc(neon, 0.0))
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(cx, y + R * 0.04), R * 0.85, R * 0.12)
    B.pen(p, B.qc(neon, 0.9), R * 0.04)                             # bright scan-line
    p.drawLine(QPointF(cx - R * 0.78, y + R * 0.04),
               QPointF(cx + R * 0.78, y + R * 0.04))
    p.setPen(B.NOPEN)
    for k in range(3):                                              # pulsing data ticks
        al = 0.3 + 0.6 * a.breath * (1.0 if k == 1 else 0.65)
        p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.6), al))
        p.drawEllipse(QPointF(cx - R * 0.64 + k * R * 0.13, y - R * 0.02),
                      R * 0.035, R * 0.035)


def _antennae(p, hd, a, hue):                     # two springy glowing feelers
    cx, R, top = hd.cx, hd.R, hd.top
    for s in (-1, 1):
        bob = math.sin(a.t * 1.6 + s * 0.7) * R * 0.12
        base = (cx + s * R * 0.32, top + R * 0.06)
        ctrl = (cx + s * R * 0.66, top - R * 0.4)
        tip = (cx + s * R * 0.52 + a.sway * R * 1.6, top - R * 0.82 + bob)
        B.pen(p, B.qc(theme.blend(hue, "#1a2a38", 0.25), 0.9), R * 0.05)
        p.drawPolyline(B.poly(*_bezier(base, ctrl, tip)))
        p.setPen(B.NOPEN)
        _orb(p, tip[0], tip[1], R * 0.15, hue, a.breath)


def _aerial(p, hd, a, hue):                       # satellite dish + signal rings
    cx, R, top = hd.cx, hd.R, hd.top
    sx = cx + a.sway * R * 0.5
    base_y, tip_y = top + R * 0.04, top - R * 0.46
    B.pen(p, B.qc(theme.blend(hue, "#2a3340", 0.3), 0.95), R * 0.07)   # stalk
    p.drawLine(QPointF(sx, base_y), QPointF(sx, tip_y))
    p.setPen(B.NOPEN)
    dish = QRectF(sx - R * 0.34, tip_y - R * 0.2, R * 0.68, R * 0.36)
    p.setBrush(B.qc(theme.blend(hue, "#3a4452", 0.4)))                 # dish bowl
    p.drawChord(dish, 0, 180 * 16)
    B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.4), 0.8), R * 0.04)    # dish rim
    p.drawArc(dish, 0, 180 * 16)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.55), 0.9))          # feed point
    p.drawEllipse(QPointF(sx, tip_y - R * 0.02), R * 0.045, R * 0.045)
    ry = tip_y - R * 0.06
    for k in range(3):                                                # signal rings
        phase = (a.t * 0.55 + k / 3.0) % 1.0
        rr = R * (0.16 + 0.46 * phase)
        al = (1.0 - phase) * (0.32 + 0.4 * a.breath)
        B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.35), al), R * 0.035)
        p.drawArc(QRectF(sx - rr, ry - rr * 0.78, rr * 2, rr * 1.4),
                  25 * 16, 130 * 16)
    p.setPen(B.NOPEN)


COSTUMES = {
    "Space Helmet": _spacehelmet,
    "Sci-fi Visor": _visor,
    "Alien Antennae": _antennae,
    "Robot Aerial": _aerial,
}
