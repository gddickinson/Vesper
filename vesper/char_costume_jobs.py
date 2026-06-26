"""'Jobs' costumes -- profession head-wear drawn ON TOP of any 2D character,
positioned from the character's :class:`~vesper.char_base.Head` anchor (centre +
radius + crown) so the same hat fits the cat, penguin or dog. A small glowing
accent keeps them on-theme without spoiling the read of the real object.

Each costume is ``fn(p, hd, a, hue)``; the module exports ``COSTUMES`` (display
name -> function), merged into the app's costume registry. Pure QPainter.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme


# --- shared little helpers --------------------------------------------------

def _glow(p, x, y, r, hue, amt=0.7):
    """A soft radial glow disc -- the shared accent so the costumes fit the app."""
    g = QRadialGradient(x, y, r)
    g.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.45), max(0.0, min(1.0, amt))))
    g.setColorAt(1.0, B.qc(hue, 0.0))
    p.setPen(B.NOPEN)
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(x, y), r, r)


def _cross(p, x, y, s, color):
    """A small medical cross centred at (x, y) with arm half-length *s*."""
    p.setPen(B.NOPEN)
    p.setBrush(color)
    p.drawRect(QRectF(x - s * 0.34, y - s, s * 0.68, s * 2))
    p.drawRect(QRectF(x - s, y - s * 0.34, s * 2, s * 0.68))


def _shield(p, x, y, s, color):
    """A tiny badge shield centred at (x, y), half-width *s*."""
    p.setPen(B.NOPEN)
    p.setBrush(color)
    p.drawPolygon(B.poly((x - s, y - s), (x + s, y - s), (x + s, y + s * 0.25),
                         (x, y + s), (x - s, y + s * 0.25)))


# --- costumes ---------------------------------------------------------------

def _police(p, hd, a, hue):                       # navy peaked police cap
    cx, R, top = hd.cx, hd.R, hd.top
    sway = a.sway * R
    navy = theme.blend(hue, "#1b2c48", 0.78)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc("#0e141d"))                                   # short flat peak
    p.drawChord(QRectF(cx - R * 0.74, top + R * 0.06, R * 1.48, R * 0.44),
                180 * 16, 180 * 16)
    p.setBrush(B.qc(navy))                                        # rounded crown
    p.drawChord(QRectF(cx - R * 0.92, top - R * 0.6, R * 1.84, R * 1.28),
                6 * 16, 168 * 16)
    p.setBrush(B.qc(theme.blend(navy, "#000000", 0.45)))          # hat-band
    p.drawRoundedRect(QRectF(cx - R * 0.92, top + R * 0.0, R * 1.84, R * 0.2),
                      R * 0.05, R * 0.05)
    bx, by = cx + sway, top - R * 0.12                            # glowing badge
    _glow(p, bx, by, R * 0.22, hue, 0.5 + 0.4 * a.breath)
    _shield(p, bx, by, R * 0.14, B.qc(theme.blend(hue, "#ffe27a", 0.55)))


def _fire(p, hd, a, hue):                         # firefighter's helmet
    cx, R, top = hd.cx, hd.R, hd.top
    sx = cx + a.sway * R
    red = theme.blend(hue, "#bf2f2f", 0.74)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(red, "#000000", 0.5)))            # rear brim, lower
    p.drawChord(QRectF(cx - R * 1.08, top - R * 0.28, R * 2.16, R * 1.0),
                184 * 16, 172 * 16)
    p.setBrush(B.qc(theme.blend(red, "#000000", 0.22)))           # front brim
    p.drawChord(QRectF(cx - R * 0.96, top - R * 0.02, R * 1.92, R * 0.5),
                180 * 16, 180 * 16)
    p.setBrush(B.qc(red))                                         # domed helmet
    p.drawChord(QRectF(cx - R * 0.84, top - R * 0.62, R * 1.68, R * 1.24),
                8 * 16, 164 * 16)
    B.pen(p, B.qc(theme.blend(red, "#ffffff", 0.28), 0.7), R * 0.07)  # crown ridge
    p.drawArc(QRectF(cx - R * 0.48, top - R * 0.5, R * 0.96, R * 0.9), 22 * 16, 136 * 16)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend("#f2c14e", hue, 0.18)))           # tall front crest
    p.drawPolygon(B.poly((sx - R * 0.28, top + R * 0.14), (sx + R * 0.28, top + R * 0.14),
                         (sx + R * 0.22, top - R * 0.46), (sx, top - R * 0.62),
                         (sx - R * 0.22, top - R * 0.46)))
    _glow(p, sx, top - R * 0.14, R * 0.16, hue, 0.55 + 0.4 * a.breath)   # emblem
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.5)))
    p.drawEllipse(QPointF(sx, top - R * 0.14), R * 0.06, R * 0.06)


def _nurse(p, hd, a, hue):                        # small folded nurse's cap
    cx, R, top = hd.cx, hd.R, hd.top
    sway = a.sway * R
    white = theme.blend(hue, "#ffffff", 0.9)
    _glow(p, cx + sway, top - R * 0.12, R * 0.42, hue, 0.16 + 0.2 * a.breath)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(white))                                       # folded cap body
    p.drawPolygon(B.poly((cx - R * 0.46 + sway, top + R * 0.22),
                         (cx + R * 0.46 + sway, top + R * 0.22),
                         (cx + R * 0.6, top - R * 0.3), (cx, top - R * 0.42),
                         (cx - R * 0.6, top - R * 0.3)))
    p.setBrush(B.qc(theme.blend(white, "#dbe5f0", 0.5)))          # front band
    p.drawRoundedRect(QRectF(cx - R * 0.5 + sway, top + R * 0.06, R * 1.0, R * 0.22),
                      R * 0.06, R * 0.06)
    _cross(p, cx + sway, top + R * 0.17, R * 0.1, B.qc("#d83a3a"))   # red cross


def _headmirror(p, hd, a, hue):                   # doctor's head mirror
    cx, cy, R = hd.cx, hd.cy, hd.R
    y = cy - R * 0.5
    dx = cx + a.sway * R
    B.pen(p, B.qc(theme.blend(hue, "#1c2c3a", 0.45)), R * 0.1)    # thin headband
    p.drawArc(QRectF(cx - R * 0.86, y - R * 0.2, R * 1.72, R * 0.72), 14 * 16, 152 * 16)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc("#0d1722"))                                  # reflector rim
    p.drawEllipse(QPointF(dx, y), R * 0.34, R * 0.34)
    g = QRadialGradient(dx - R * 0.11, y - R * 0.11, R * 0.52)    # concave glint
    g.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.75), 0.7 + 0.3 * a.breath))
    g.setColorAt(0.5, B.qc(theme.blend(hue, "#9fc7d6", 0.4), 0.7))
    g.setColorAt(1.0, B.qc("#0d1722", 0.92))
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(dx, y), R * 0.28, R * 0.28)
    p.setBrush(B.qc("#06101a"))                                  # tiny centre hole
    p.drawEllipse(QPointF(dx, y), R * 0.05, R * 0.05)


def _chef(p, hd, a, hue):                         # tall pleated chef's toque
    cx, R, top = hd.cx, hd.R, hd.top
    sway = a.sway * R
    white = theme.blend(hue, "#ffffff", 0.9)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(white))                                       # gathered body
    p.drawRoundedRect(QRectF(cx - R * 0.5, top - R * 0.55, R * 1.0, R * 0.7),
                      R * 0.1, R * 0.1)
    for dx, dy, s in ((-0.42, -0.66, 0.4), (0.42, -0.66, 0.4), (0.0, -0.92, 0.5),
                      (-0.16, -0.5, 0.42), (0.16, -0.5, 0.42)):  # puffy cloud top
        p.drawEllipse(QPointF(cx + dx * R + sway * (1 - dy), top + dy * R), R * s, R * s)
    p.setBrush(B.qc(theme.blend(white, "#dce6f0", 0.45)))        # short band
    p.drawRoundedRect(QRectF(cx - R * 0.54, top - R * 0.06, R * 1.08, R * 0.24),
                      R * 0.1, R * 0.1)
    B.pen(p, B.qc(theme.blend(hue, "#cdd8e4", 0.35), 0.5), R * 0.03)  # pleats
    for k in (-1, 0, 1):
        p.drawLine(QPointF(cx + k * R * 0.28, top - R * 0.02),
                   QPointF(cx + k * R * 0.28 + sway * 0.4, top - R * 0.5))
    p.setPen(B.NOPEN)
    _glow(p, cx - R * 0.18, top - R * 0.55, R * 0.3, hue, 0.18 + 0.2 * a.breath)


def _hardhat(p, hd, a, hue):                      # construction hard hat
    cx, R, top = hd.cx, hd.R, hd.top
    amber = theme.blend(hue, "#f0b429", 0.72)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(amber, "#000000", 0.2)))         # short front brim
    p.drawChord(QRectF(cx - R * 0.84, top - R * 0.0, R * 1.68, R * 0.46),
                180 * 16, 180 * 16)
    p.setBrush(B.qc(amber))                                       # smooth dome
    p.drawChord(QRectF(cx - R * 0.86, top - R * 0.64, R * 1.72, R * 1.26),
                6 * 16, 168 * 16)
    B.pen(p, B.qc(theme.blend(amber, "#7a5410", 0.55), 0.85), R * 0.06)  # ridges
    for dx in (-0.34, 0.0, 0.34):
        p.drawLine(QPointF(cx + dx * R * 1.05, top + R * 0.04),
                   QPointF(cx + dx * R * 0.34, top - R * 0.56))
    p.setPen(B.NOPEN)
    _glow(p, cx - R * 0.2, top - R * 0.28, R * 0.3, hue, 0.22 + 0.25 * a.breath)


def _grad(p, hd, a, hue):                         # mortarboard + swaying tassel
    cx, R, top = hd.cx, hd.R, hd.top
    by = top - R * 0.06
    dark = theme.blend(hue, "#171b2f", 0.72)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(dark, "#000000", 0.15)))         # small skull-cap
    p.drawChord(QRectF(cx - R * 0.5, top - R * 0.16, R * 1.0, R * 0.7), 0, 180 * 16)
    pa = (cx - R * 0.92, by - R * 0.04); pb = (cx + R * 0.2, by - R * 0.34)
    pcc = (cx + R * 0.92, by + R * 0.04); pd = (cx - R * 0.2, by + R * 0.34)
    p.setBrush(B.qc(dark))                                        # tilted board
    p.drawPolygon(B.poly(pa, pb, pcc, pd))
    p.setBrush(B.qc(theme.blend(hue, "#ffd86b", 0.5)))           # centre button
    p.drawEllipse(QPointF(cx, by), R * 0.07, R * 0.05)
    swing = math.sin(a.t * 1.1) * R * 0.16                        # tassel sway
    hx, hy = pcc[0] - R * 0.05, pcc[1]
    B.pen(p, B.qc(theme.blend(hue, "#ffd86b", 0.45)), R * 0.04)
    p.drawLine(QPointF(cx, by), QPointF(hx, hy))                  # cord to corner
    for k in (-1, 0, 1):                                          # hanging strands
        p.drawLine(QPointF(hx, hy), QPointF(hx + swing + k * R * 0.05, hy + R * 0.66))
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(hue, "#ffd86b", 0.55)))          # tassel knob
    p.drawEllipse(QPointF(hx + swing * 0.4, hy + R * 0.18), R * 0.05, R * 0.07)


COSTUMES = {
    "Police Cap": _police, "Fire Helmet": _fire, "Nurse Cap": _nurse,
    "Head Mirror": _headmirror, "Chef Hat": _chef, "Hard Hat": _hardhat,
    "Graduation Cap": _grad,
}
