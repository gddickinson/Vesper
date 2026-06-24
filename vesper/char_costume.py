"""Costumes drawn ON TOP of any character, positioned from the character's Head
anchor (centre + radius + crown), so the same hat fits the cat, penguin or dog.
A small futuristic twist (glowing accents) keeps them on-theme. Pure QPainter.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QRadialGradient

from . import char_base as B
from . import theme


def _none(p, hd, a, hue):
    pass


def _wizard(p, hd, a, hue):                       # tall starry cone + brim
    cx, R, top = hd.cx, hd.R, hd.top
    sway = a.sway * R * 1.5
    tip = (cx + sway, top - R * 1.5)
    base_y = top + R * 0.18
    p.setPen(B.NOPEN)
    p.setBrush(B.qc("#241a3a"))
    p.drawPolygon(B.poly(tip, (cx - R * 0.7, base_y), (cx + R * 0.7, base_y)))
    p.setBrush(B.qc(theme.blend(hue, "#241a3a", 0.4)))      # band
    p.drawPolygon(B.poly((cx - R * 0.62, base_y - R * 0.18),
                         (cx + R * 0.62, base_y - R * 0.18),
                         (cx + R * 0.5, base_y - R * 0.42),
                         (cx - R * 0.5, base_y - R * 0.42)))
    p.setBrush(B.qc("#2a1f44"))                             # brim
    p.drawEllipse(QPointF(cx, base_y), R * 0.95, R * 0.22)
    for i, (dx, dy, s) in enumerate([(-0.18, -0.7, 0.10), (0.1, -1.05, 0.13),
                                     (0.22, -0.4, 0.08)]):  # glowing stars
        sx, sy = cx + sway * (1 + dy * -0.4) + R * dx, top + R * dy
        _star(p, sx, sy, R * s, hue, 0.6 + 0.4 * math.sin(a.t * 3 + i))


def _party(p, hd, a, hue):                        # striped cone + pompom
    cx, R, top = hd.cx, hd.R, hd.top
    tip = (cx + a.sway * R, top - R * 1.25)
    base_y = top + R * 0.05
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.1)))
    p.drawPolygon(B.poly(tip, (cx - R * 0.6, base_y), (cx + R * 0.6, base_y)))
    p.setBrush(B.qc("#ffffff", 0.55))                       # diagonal stripes
    for k in range(1, 4):
        f = k / 4.0
        p.drawPolygon(B.poly(
            (cx - R * 0.6 + R * 1.2 * f, base_y),
            (cx - R * 0.6 + R * 1.2 * f + R * 0.12, base_y),
            (tip[0] + (cx - tip[0]) * (1 - f) * 0.0 + R * 0.06, top - R * (1.25 * (1 - f))),
            (tip[0] - R * 0.04, top - R * (1.25 * (1 - f)))))
    _pompom(p, tip[0], tip[1], R * 0.16, hue, a)


def _beanie(p, hd, a, hue):                       # snug cap + fold + pompom
    cx, cy, R, top = hd.cx, hd.cy, hd.R, hd.top
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(hue, "#13202c", 0.45)))
    p.drawChord(QRectF(cx - R * 0.98, top - R * 0.5, R * 1.96, R * 1.5),
                10 * 16, 160 * 16)
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.2)))      # fold band
    p.drawRoundedRect(QRectF(cx - R * 0.98, top + R * 0.18, R * 1.96, R * 0.26),
                      R * 0.13, R * 0.13)
    _pompom(p, cx + a.sway * R, top - R * 0.5, R * 0.2, hue, a)


def _headphones(p, hd, a, hue):                   # glowing band + ear cups
    cx, cy, R, top = hd.cx, hd.cy, hd.R, hd.top
    B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.2), 0.95), R * 0.13)
    p.drawArc(QRectF(cx - R * 0.95, top - R * 0.15, R * 1.9, R * 1.2),
              20 * 16, 140 * 16)
    p.setPen(B.NOPEN)
    for s in (-1, 1):
        ex = cx + s * R * 0.96
        gl = QRadialGradient(ex, cy, R * 0.4)
        gl.setColorAt(0.0, B.qc(hue, 0.5 + 0.4 * a.breath))
        gl.setColorAt(1.0, B.qc(hue, 0.0))
        p.setBrush(QBrush(gl)); p.drawEllipse(QPointF(ex, cy), R * 0.4, R * 0.4)
        p.setBrush(B.qc("#1b2a36")); p.drawEllipse(QPointF(ex, cy), R * 0.24, R * 0.3)
        p.setBrush(B.qc(hue, 0.8)); p.drawEllipse(QPointF(ex, cy), R * 0.1, R * 0.12)


def _shades(p, hd, a, hue):                       # cyber visor sunglasses
    cx, cy, R = hd.cx, hd.cy, hd.R
    ey = cy - R * 0.05
    B.pen(p, B.qc("#0c1620"), R * 0.06)
    p.drawLine(QPointF(cx - R * 0.16, ey), QPointF(cx + R * 0.16, ey))   # bridge
    p.setPen(B.NOPEN)
    for s in (-1, 1):
        lx = cx + s * R * 0.44
        p.setBrush(B.qc("#0c1620"))
        p.drawRoundedRect(QRectF(lx - R * 0.34, ey - R * 0.2, R * 0.62, R * 0.42),
                          R * 0.1, R * 0.1)
        gl = B.qc(theme.blend(hue, "#ffffff", 0.3), 0.7)    # neon glint
        B.pen(p, gl, R * 0.05)
        p.drawLine(QPointF(lx - R * 0.26, ey + R * 0.08),
                   QPointF(lx + R * 0.1, ey - R * 0.1))
        p.setPen(B.NOPEN)


def _scarf(p, hd, a, hue):                        # snug scarf at the neck
    cx, cy, R = hd.cx, hd.cy, hd.R
    ny = cy + R * 0.92
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(hue, "#13202c", 0.25)))
    p.drawRoundedRect(QRectF(cx - R * 0.8, ny, R * 1.6, R * 0.4), R * 0.2, R * 0.2)
    p.setBrush(B.qc(theme.blend(hue, "#13202c", 0.1)))      # hanging tail
    tx = cx + R * (0.3 + 0.12 * math.sin(a.t * 1.2))
    p.drawRoundedRect(QRectF(tx - R * 0.12, ny + R * 0.2, R * 0.24, R * 0.6),
                      R * 0.1, R * 0.1)


def _star(p, x, y, s, hue, glow):
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.4), 0.6 + 0.4 * glow))
    p.drawPolygon(B.poly((x, y - s), (x + s * 0.28, y - s * 0.28), (x + s, y),
                         (x + s * 0.28, y + s * 0.28), (x, y + s),
                         (x - s * 0.28, y + s * 0.28), (x - s, y),
                         (x - s * 0.28, y - s * 0.28)))


def _pompom(p, x, y, r, hue, a):
    gl = QRadialGradient(x, y, r * 1.6)
    gl.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.5), 0.9))
    gl.setColorAt(1.0, B.qc(hue, 0.0))
    p.setBrush(QBrush(gl)); p.drawEllipse(QPointF(x, y), r * 1.6, r * 1.6)
    p.setBrush(B.qc("#ffffff", 0.92)); p.drawEllipse(QPointF(x, y), r, r)


_COSTUMES = {
    "None": _none, "Wizard Hat": _wizard, "Party Hat": _party, "Beanie": _beanie,
    "Headphones": _headphones, "Sunglasses": _shades, "Scarf": _scarf,
}


def names():
    return list(_COSTUMES)


def draw(p, head, name, anim, hue):
    """Draw costume *name* over the character described by *head* (a Head anchor)."""
    _COSTUMES.get(name, _none)(p, head, anim, hue)
