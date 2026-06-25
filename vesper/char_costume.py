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


def _nightcap(p, hd, a, hue):                     # cosy sleeping cap + droopy tip
    cx, R, top = hd.cx, hd.R, hd.top
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(hue, "#13202c", 0.5)))
    p.drawChord(QRectF(cx - R * 1.0, top - R * 0.55, R * 2.0, R * 1.5),
                8 * 16, 164 * 16)                      # snug dome
    droop = math.sin(a.t * 0.9) * R * 0.12
    tipx = cx - R * (0.7 + 0.2 * a.sway) + droop
    tipy = top - R * 0.2
    p.drawPolygon(B.poly((cx - R * 0.2, top - R * 0.5),
                         (cx + R * 0.1, top - R * 0.5),
                         (tipx, tipy)))                # flopping point
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.22)))   # fold band
    p.drawRoundedRect(QRectF(cx - R * 1.0, top + R * 0.12, R * 2.0, R * 0.28),
                      R * 0.14, R * 0.14)
    _pompom(p, tipx, tipy, R * 0.17, hue, a)


def _sleepmask(p, hd, a, hue):                    # eye mask pushed up on the brow
    cx, cy, R = hd.cx, hd.cy, hd.R
    y = cy - R * 0.36
    p.setPen(B.NOPEN)
    p.setBrush(B.qc(theme.blend(hue, "#241a3a", 0.45)))
    p.drawRoundedRect(QRectF(cx - R * 0.86, y - R * 0.24, R * 1.72, R * 0.5),
                      R * 0.24, R * 0.24)
    B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.5), 0.6), R * 0.05)   # strap
    p.drawArc(QRectF(cx - R * 1.02, y - R * 0.3, R * 2.04, R * 0.7),
              200 * 16, 140 * 16)
    p.setPen(B.NOPEN)
    for s in (-1, 1):                                  # closed-eye stitches
        B.pen(p, B.qc("#cfe0ea", 0.7), R * 0.03)
        p.drawArc(QRectF(cx + s * R * 0.42 - R * 0.18, y - R * 0.1,
                         R * 0.36, R * 0.24), 200 * 16, 140 * 16)
    p.setPen(B.NOPEN)


def _earmuffs(p, hd, a, hue):                     # fuzzy ear warmers on a band
    cx, cy, R, top = hd.cx, hd.cy, hd.R, hd.top
    B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.4), 0.85), R * 0.12)
    p.drawArc(QRectF(cx - R * 0.96, top - R * 0.2, R * 1.92, R * 1.2),
              20 * 16, 140 * 16)                       # head band
    p.setPen(B.NOPEN)
    for s in (-1, 1):
        ex, ey = cx + s * R * 0.96, cy - R * 0.18
        gl = QRadialGradient(ex, ey, R * 0.5)
        gl.setColorAt(0.0, B.qc(theme.blend(hue, "#ffffff", 0.5), 0.9))
        gl.setColorAt(1.0, B.qc(hue, 0.0))
        p.setBrush(QBrush(gl)); p.drawEllipse(QPointF(ex, ey), R * 0.5, R * 0.5)
        p.setBrush(B.qc("#ffffff", 0.92))
        p.drawEllipse(QPointF(ex, ey), R * 0.34, R * 0.4)


def _witch(p, hd, a, hue):                        # pointed witch hat + buckle
    cx, R, top = hd.cx, hd.R, hd.top
    sway = a.sway * R * 1.2
    tip = (cx + sway, top - R * 1.7)
    base_y = top + R * 0.1
    bend = (cx + sway * 1.6 + R * 0.18, top - R * 0.9)   # bent point
    p.setPen(B.NOPEN)
    p.setBrush(B.qc("#1c1530"))
    p.drawPolygon(B.poly(tip, bend, (cx - R * 0.72, base_y),
                         (cx + R * 0.72, base_y)))
    p.setBrush(B.qc("#15102a"))                          # wide brim
    p.drawEllipse(QPointF(cx, base_y), R * 1.05, R * 0.24)
    p.setBrush(B.qc(theme.blend(hue, "#241a3a", 0.4)))   # band
    p.drawRect(QRectF(cx - R * 0.5, base_y - R * 0.28, R * 1.0, R * 0.18))
    p.setBrush(B.qc(theme.blend(hue, "#ffffff", 0.45)))  # buckle
    p.drawRect(QRectF(cx - R * 0.1, base_y - R * 0.3, R * 0.2, R * 0.22))
    _star(p, tip[0], tip[1] + R * 0.1, R * 0.1, hue, 0.6 + 0.4 * math.sin(a.t * 3))


def _pirate(p, hd, a, hue):                       # tricorne pirate hat + skull
    cx, R, top = hd.cx, hd.R, hd.top
    base_y = top - R * 0.04
    p.setPen(B.NOPEN)
    p.setBrush(B.qc("#1a2330"))
    p.drawPolygon(B.poly((cx - R * 1.05, base_y + R * 0.1),
                         (cx + R * 1.05, base_y + R * 0.1),
                         (cx + R * 0.5, base_y - R * 0.7),
                         (cx, base_y - R * 0.86),
                         (cx - R * 0.5, base_y - R * 0.7)))
    B.pen(p, B.qc(theme.blend(hue, "#ffffff", 0.4), 0.8), R * 0.05)   # trim
    p.drawPolyline(B.poly((cx - R * 1.0, base_y + R * 0.08),
                          (cx + R * 0.46, base_y - R * 0.66),
                          (cx, base_y - R * 0.82),
                          (cx - R * 0.46, base_y - R * 0.66),
                          (cx + R * 1.0, base_y + R * 0.08)))
    p.setPen(B.NOPEN)
    p.setBrush(B.qc("#eef2f5", 0.95))                    # little skull
    p.drawEllipse(QPointF(cx, base_y - R * 0.34), R * 0.16, R * 0.17)
    p.setBrush(B.qc("#1a2330"))
    for s in (-1, 1):
        p.drawEllipse(QPointF(cx + s * R * 0.06, base_y - R * 0.36),
                      R * 0.04, R * 0.05)


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
    "None": _none, "Nightcap": _nightcap, "Sleep Mask": _sleepmask,
    "Earmuffs": _earmuffs, "Wizard Hat": _wizard, "Witch Hat": _witch,
    "Pirate Hat": _pirate, "Party Hat": _party, "Beanie": _beanie,
    "Top Hat": _tophat, "Crown": _crown, "Halo": _halo, "Headphones": _headphones,
    "Sunglasses": _shades, "Flower": _flower, "Scarf": _scarf, "Bow Tie": _bowtie,
}


def names():
    return list(_COSTUMES)


def draw(p, head, name, anim, hue):
    """Draw costume *name* over the character described by *head* (a Head anchor)."""
    _COSTUMES.get(name, _none)(p, head, anim, hue)
