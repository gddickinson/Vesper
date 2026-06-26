"""The Skull character: a gentle, storybook **talking skull** for spooky / folklore
tales. It lives in the shared 2D character framework, so it breathes, tilts and
drifts with the head like the others -- but instead of cute eyes it has hollow
sockets with a faint ember glow, a nasal aperture, cranial sutures, and an
**articulated mandible** that hinges open with ``anim.mouth`` (driven by the
narration amplitude), so it really looks like it is telling the story.

Sleep-gentle by design: warm ivory bone, a soft low-contrast glow, slow motion --
atmospheric, not frightening.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QPainterPath, QRadialGradient

from . import char_base as B

_BONE, _BONE_DK, _SHADOW = "#e7dfca", "#bdb195", "#6f654c"
_CAVITY, _TOOTH, _TOOTH_DK = "#140f0a", "#f1ebd8", "#cabf9f"


class Skull(B.Character):
    name = "Skull"

    def draw(self, p, w, h, a):
        cx, cy, R = B.head_box(w, h, a, ypos=0.44)
        hue = a.hue
        p.setPen(B.NOPEN)
        p.save()
        if a.tilt:                                           # head-cock -> a real tilt
            p.translate(cx, cy); p.rotate(a.tilt * 7.0); p.translate(-cx, -cy)
        B.aura(p, cx, cy, R, hue, a.breath)
        self._mandible(p, cx, cy, R, a)                      # behind, drops with mouth
        self._cranium(p, cx, cy, R)
        self._cheeks(p, cx, cy, R)
        self._sutures(p, cx, cy, R)
        self._sockets(p, cx, cy, R, a, hue)
        self._nasal(p, cx, cy, R)
        self._upper_teeth(p, cx, cy, R)
        p.restore()
        return B.Head(cx, cy, R, cy - R * 1.25)

    # ---- bony upper skull (cranium + maxilla) ----------------------------
    def _cranium(self, p, cx, cy, R):
        g = QRadialGradient(cx, cy - R * 0.5, R * 1.7)
        g.setColorAt(0.0, B.qc("#f3ecd9"))
        g.setColorAt(0.7, B.qc(_BONE))
        g.setColorAt(1.0, B.qc(_BONE_DK))
        p.setBrush(QBrush(g))
        path = QPainterPath()
        top = cy - R * 1.18
        path.moveTo(cx, top)                                 # crown
        path.cubicTo(cx + R * 1.02, top, cx + R * 1.04, cy - R * 0.18,
                     cx + R * 0.86, cy + R * 0.16)           # temple -> cheekbone
        path.cubicTo(cx + R * 0.74, cy + R * 0.44,
                     cx + R * 0.5, cy + R * 0.5,
                     cx + R * 0.43, cy + R * 0.62)           # down to the maxilla
        path.lineTo(cx - R * 0.43, cy + R * 0.62)            # upper-jaw base
        path.cubicTo(cx - R * 0.5, cy + R * 0.5,
                     cx - R * 0.74, cy + R * 0.44,
                     cx - R * 0.86, cy + R * 0.16)
        path.cubicTo(cx - R * 1.04, cy - R * 0.18,
                     cx - R * 1.02, top, cx, top)
        path.closeSubpath()
        p.drawPath(path)

    def _cheeks(self, p, cx, cy, R):
        p.setBrush(B.qc("#f1ead6", 0.45))                    # zygomatic highlight
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.62, cy + R * 0.12),
                          R * 0.2, R * 0.13)
        p.setBrush(B.qc(_SHADOW, 0.16))                      # soft temple hollows
        for s in (-1, 1):
            p.drawEllipse(QPointF(cx + s * R * 0.72, cy - R * 0.35),
                          R * 0.16, R * 0.26)

    def _sutures(self, p, cx, cy, R):
        B.pen(p, B.qc(_SHADOW, 0.35), max(1.0, R * 0.018))
        top = cy - R * 1.05
        p.drawLine(QPointF(cx, top), QPointF(cx, cy - R * 0.62))   # sagittal
        zig = QPainterPath()                                       # coronal, jagged
        zig.moveTo(cx - R * 0.66, cy - R * 0.5)
        for i in range(1, 7):
            x = cx - R * 0.66 + i * R * 0.22
            zig.lineTo(x, cy - R * 0.5 + (R * 0.05 if i % 2 else -R * 0.05))
        p.strokePath(zig, p.pen())
        p.setPen(B.NOPEN)

    # ---- hollow eye sockets with a faint ember glow ----------------------
    def _sockets(self, p, cx, cy, R, a, hue):
        ey = cy - R * 0.12
        sx = R * 0.42
        for s in (-1, 1):
            ex = cx + s * sx
            p.setBrush(B.qc(_CAVITY))                         # deep hollow
            p.drawEllipse(QPointF(ex, ey), R * 0.27, R * 0.32)
            p.setBrush(B.qc("#000000", 0.55))                # darker inner rim
            p.drawEllipse(QPointF(ex, ey + R * 0.03), R * 0.2, R * 0.24)
            g = QRadialGradient(ex, ey + R * 0.04, R * 0.22)  # ember (breathes)
            glow = 0.18 + 0.22 * a.breath
            g.setColorAt(0.0, B.qc(hue, glow))
            g.setColorAt(1.0, B.qc(hue, 0.0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(ex, ey + R * 0.04), R * 0.22, R * 0.22)
            p.setBrush(B.qc(hue, 0.5 + 0.3 * a.breath))      # pinpoint pupil-light
            p.drawEllipse(QPointF(ex, ey + R * 0.04), R * 0.05, R * 0.05)
        B.pen(p, B.qc(_SHADOW, 0.4), max(1.0, R * 0.02))     # brow ridge
        p.drawArc(QRectF(cx - sx - R * 0.3, ey - R * 0.42, R * 0.6, R * 0.4),
                  20 * 16, 140 * 16)
        p.drawArc(QRectF(cx + sx - R * 0.3, ey - R * 0.42, R * 0.6, R * 0.4),
                  20 * 16, 140 * 16)
        p.setPen(B.NOPEN)

    def _nasal(self, p, cx, cy, R):
        ny = cy + R * 0.22
        p.setBrush(B.qc(_CAVITY))
        p.drawPolygon(B.poly((cx, cy + R * 0.02),
                             (cx - R * 0.11, ny), (cx, ny + R * 0.06),
                             (cx + R * 0.11, ny)))

    def _upper_teeth(self, p, cx, cy, R):
        ty = cy + R * 0.5
        self._teeth_row(p, cx, ty, R, n=8, up=True)

    # ---- the articulated lower jaw ---------------------------------------
    def _mandible(self, p, cx, cy, R, a):
        drop = min(1.0, max(0.0, a.mouth / 0.5)) * R * 0.62  # hinge open
        top = cy + R * 0.52
        chin = top + R * 0.5 + drop
        if drop > R * 0.03:                                  # dark mouth cavity
            p.setBrush(B.qc(_CAVITY))
            p.drawRoundedRect(QRectF(cx - R * 0.4, top - R * 0.02,
                                     R * 0.8, drop + R * 0.12), R * 0.1, R * 0.1)
        g = QRadialGradient(cx, chin - R * 0.1, R * 1.0)
        g.setColorAt(0.0, B.qc(_BONE))
        g.setColorAt(1.0, B.qc(_BONE_DK))
        p.setBrush(QBrush(g))
        jaw = QPainterPath()                                 # U-shaped jaw bone
        jaw.moveTo(cx - R * 0.6, top - drop * 0.12)          # left hinge
        jaw.cubicTo(cx - R * 0.62, top + R * 0.34 + drop * 0.5,
                    cx - R * 0.4, chin, cx, chin)            # to the chin
        jaw.cubicTo(cx + R * 0.4, chin,
                    cx + R * 0.62, top + R * 0.34 + drop * 0.5,
                    cx + R * 0.6, top - drop * 0.12)         # right hinge
        jaw.lineTo(cx + R * 0.42, top + drop + R * 0.16)     # inner edge (teeth shelf)
        jaw.cubicTo(cx + R * 0.3, chin - R * 0.18,
                    cx - R * 0.3, chin - R * 0.18,
                    cx - R * 0.42, top + drop + R * 0.16)
        jaw.closeSubpath()
        p.drawPath(jaw)
        self._teeth_row(p, cx, top + drop + R * 0.05, R, n=8, up=False)

    def _teeth_row(self, p, cx, ty, R, n, up):
        tw = R * 0.84 / n
        p.setPen(B.NOPEN)
        for i in range(n):
            x = cx - R * 0.42 + (i + 0.5) * (R * 0.84 / n)
            p.setBrush(B.qc(_TOOTH))
            p.drawRoundedRect(QRectF(x - tw * 0.4, ty, tw * 0.8, R * 0.12),
                              tw * 0.25, tw * 0.25)
            B.pen(p, B.qc(_TOOTH_DK, 0.6), max(0.8, R * 0.01))  # seam
            p.drawLine(QPointF(x - tw * 0.4, ty + R * 0.04),
                       QPointF(x - tw * 0.4, ty + R * 0.1))
            p.setPen(B.NOPEN)
