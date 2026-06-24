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


def _crown(p, hd, a, hue):                        # golden zigzag crown
    cx, R, top = hd.cx, hd.R, hd.top
    y = top + R * 0.12
    gold = theme.blend(hue, "#ffd86b", 0.7)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(gold))
    pts = [(cx - R * 0.62, y)]
    for k in range(5):                                       # 5 spikes
        x = cx - R * 0.62 + R * 1.24 * k / 4.0
        pts.append((x - R * 0.155, y))
        pts.append((x, y - R * (0.34 if k % 2 == 0 else 0.5)))
        pts.append((x + R * 0.155, y))
    pts.append((cx + R * 0.62, y + R * 0.16))
    pts.append((cx - R * 0.62, y + R * 0.16))
    p.drawPolygon(B.poly(*pts))
    for k in range(5):                                       # glowing gems
        gx = cx - R * 0.5 + R * 1.0 * k / 4.0
        _star(p, gx, y - R * (0.34 if k % 2 == 0 else 0.5) + R * 0.04, R * 0.06,
              hue, 0.6 + 0.4 * math.sin(a.t * 3 + k))


def _tophat(p, hd, a, hue):                       # sleek cyber top hat
    cx, R, top = hd.cx, hd.R, hd.top
    sway = a.sway * R
    p.setPen(B.NOPEN)
    p.setBrush(B.qc("#15202c"))
    p.drawEllipse(QPointF(cx, top + R * 0.06), R * 0.95, R * 0.2)   # brim
    p.drawRoundedRect(QRectF(cx - R * 0.5 + sway, top - R * 0.95,
                             R * 1.0, R * 1.05), R * 0.08, R * 0.08)
    p.setBrush(B.qc(theme.blend(hue, "#15202c", 0.3)))             # glowing band
    p.drawRect(QRectF(cx - R * 0.5 + sway, top - R * 0.18, R * 1.0, R * 0.18))


def _flower(p, hd, a, hue):                       # a little flower by the ear
    cx, R, top = hd.cx, hd.R, hd.top
    fx, fy = cx - R * 0.66, top + R * 0.34
    pet = theme.blend(hue, "#ffffff", 0.45)
    p.setPen(B.NOPEN)
    for k in range(5):
        an = a.t * 0.5 + k * 1.2566
        p.setBrush(B.qc(pet, 0.95))
        p.drawEllipse(QPointF(fx + math.cos(an) * R * 0.16,
                              fy + math.sin(an) * R * 0.16), R * 0.12, R * 0.12)
    p.setBrush(B.qc("#ffe27a"))
    p.drawEllipse(QPointF(fx, fy), R * 0.1, R * 0.1)


def _bowtie(p, hd, a, hue):                       # bow tie at the neck
    cx, cy, R = hd.cx, hd.cy, hd.R
    ny = cy + R * 0.98
    col = theme.blend(hue, "#13202c", 0.2)
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(col))
    for s in (-1, 1):
        p.drawPolygon(B.poly((cx, ny), (cx + s * R * 0.42, ny - R * 0.22),
                             (cx + s * R * 0.42, ny + R * 0.22)))
    p.setBrush(B.qc(theme.blend(col, "#ffffff", 0.2)))
    p.drawEllipse(QPointF(cx, ny), R * 0.1, R * 0.13)         # knot


def _halo(p, hd, a, hue):                         # glowing floating halo
    cx, R, top = hd.cx, hd.R, hd.top
    y = top - R * 0.34 + math.sin(a.t * 1.4) * R * 0.04
    gl = QRadialGradient(cx, y, R * 0.7)
    gl.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.4), 0.0))
    gl.setColorAt(0.7, B.qc(theme.blend(hue, "#ffffff", 0.4), 0.5 + 0.4 * a.breath))
    gl.setColorAt(1.0, B.qc(hue, 0.0))
    p.setPen(B.NOPEN); p.setBrush(QBrush(gl))
    p.drawEllipse(QPointF(cx, y), R * 0.6, R * 0.24)
    B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.5), 0.9), R * 0.06)
    p.drawArc(QRectF(cx - R * 0.5, y - R * 0.16, R * 1.0, R * 0.32), 0, 360 * 16)
    p.setPen(B.NOPEN)


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
    "Top Hat": _tophat, "Crown": _crown, "Halo": _halo, "Headphones": _headphones,
    "Sunglasses": _shades, "Flower": _flower, "Scarf": _scarf, "Bow Tie": _bowtie,
}


def names():
    return list(_COSTUMES)


def draw(p, head, name, anim, hue):
    """Draw costume *name* over the character described by *head* (a Head anchor)."""
    _COSTUMES.get(name, _none)(p, head, anim, hue)
