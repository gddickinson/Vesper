"""Shared drawing kit for the 2D characters: colour helpers, a soft breath aura,
big **cute glossy eyes** (blink, gaze, pupil dilation, happy squint, catchlight)
and a blush -- so every character looks consistently cute and animates the same
way. Characters subclass :class:`Character` and return a :class:`Head` anchor so a
costume can be attached on top.
"""
from __future__ import annotations

import math
from collections import namedtuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF, QRadialGradient

from . import theme

NOPEN = Qt.PenStyle.NoPen
ROUND = Qt.PenCapStyle.RoundCap

# Head anchor a character returns, so costumes know where the head + crown are.
Head = namedtuple("Head", "cx cy R top")


def qc(hexs, a=1.0):
    c = QColor(hexs)
    c.setAlphaF(max(0.0, min(1.0, a)))
    return c


def poly(*pts):
    return QPolygonF([QPointF(*pt) for pt in pts])


def pen(p, color, width, cap=ROUND):
    q = QPen(color)
    q.setWidthF(max(0.8, width))
    q.setCapStyle(cap)
    p.setPen(q)


def head_box(w, h, anim, scale=0.23, ypos=0.47):
    """Shared head placement: centre (with idle sway), a breathing radius, and a
    gentle vertical bob. Keeps every character framed + breathing the same way."""
    R = min(w, h) * scale * (0.97 + 0.05 * anim.breath)
    cx = w / 2.0 + anim.sway * R
    cy = h * ypos + anim.bob * R
    return cx, cy, R


def aura(p, cx, cy, R, hue, breath):
    """A soft halo that swells on the in-breath (shared by all characters)."""
    g = QRadialGradient(cx, cy, R * 2.1)
    g.setColorAt(0.0, qc(hue, 0.07 + 0.13 * breath))
    g.setColorAt(0.6, qc(hue, 0.04 + 0.06 * breath))
    g.setColorAt(1.0, qc(hue, 0.0))
    p.setPen(NOPEN)
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(cx, cy), R * 2.1, R * 2.1)


def blush(p, cx, cy, R, dx, color="#f6a8b6", amt=0.5):
    p.setPen(NOPEN)
    for s in (-1, 1):
        p.setBrush(qc(color, 0.30 * amt))
        p.drawEllipse(QPointF(cx + s * dx, cy), R * 0.17, R * 0.11)


def cute_eyes(p, cx, eyey, ew, spacing, anim, iris="#86e6bf",
              dark="#0c1f2c", glow=True, gaze_amt=1.0):
    """Two big, glossy, cute eyes. Blink (lid closes), follow the gaze, the pupils
    dilate on the in-breath, the eyes squint when smiling, and each carries a bright
    catchlight. Centralised so every character shares the look + animation."""
    open_amt = 1.0 - anim.blink
    squint = max(0.0, anim.smile - 0.35) / 0.65            # happy -> narrower
    open_amt *= (1.0 - 0.5 * squint)
    eh = ew * (0.04 + 1.18 * open_amt)                     # eye height (blink squash)
    gx, gy = anim.gaze
    p.setPen(NOPEN)
    for s in (-1, 1):
        ex = cx + s * spacing
        if glow:
            g = QRadialGradient(ex, eyey, ew * 2.0)
            g.setColorAt(0.0, qc(iris, 0.38 * open_amt))
            g.setColorAt(1.0, qc(iris, 0.0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(ex, eyey), ew * 2.0, ew * 2.0)
        p.setBrush(qc(dark))                               # eye whites-as-dark base
        p.drawEllipse(QPointF(ex, eyey), ew, eh)
        if open_amt > 0.18:
            p.setBrush(qc(iris))                           # bright iris
            p.drawEllipse(QPointF(ex, eyey), ew * 0.82, eh * 0.9)
            pw = ew * (0.42 + 0.16 * anim.breath)          # pupil dilates inhaling
            px = ex + gx * ew * 0.9 * gaze_amt
            py = eyey + gy * eh * 0.8 * gaze_amt
            p.setBrush(qc("#06101a"))
            p.drawEllipse(QPointF(px, py), pw, pw * 1.04)
            p.setBrush(qc("#ffffff", 0.95))                # big catchlight (cute)
            p.drawEllipse(QPointF(px - ew * 0.26, py - eh * 0.30),
                          ew * 0.20, ew * 0.20)
            p.setBrush(qc("#ffffff", 0.6))                 # tiny secondary sparkle
            p.drawEllipse(QPointF(px + ew * 0.16, py + eh * 0.12),
                          ew * 0.08, ew * 0.08)
        if squint > 0.05:                                  # smiling lower lid
            return_lid = eh * (0.4 + 0.7 * squint)
            p.setBrush(qc(theme.blend(iris, "#ffffff", 0.2), 0.0))  # invisible spacer
    return eh


class Character:
    """A drawable 2D character. ``draw`` paints into *p* over (w, h) using the
    shared :class:`~vesper.char_anim.Anim` signals and returns a :class:`Head`
    anchor (head centre + radius + crown point) for costume attachment."""

    name = "Character"

    def draw(self, p, w, h, anim) -> Head:        # pragma: no cover - overridden
        raise NotImplementedError
