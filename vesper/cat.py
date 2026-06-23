"""A friendly 2D cartoon cat -- the fallback face when the 3D avatar (faceView)
isn't installed, and a runtime option (View > Cartoon cat face).

Pure QPainter, but alive: it **breathes** (a swelling aura, a rising chest, a head
bob + zoom, pupils that dilate on the in-breath), **blinks**, twitches its ears,
**smiles** (eyes squint, mouth lifts) and opens its mouth to **talk** -- all driven
by the same per-frame state the 3D face receives (`vol`/`mouth`/`eye_open`/`smile`/
`t`/`hue`). Soft tabby markings, cheek tufts and curved whiskers give it character
while staying calm and on-theme. Force it from the start with `VESPER_FACE=cat`.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF, QRadialGradient

from . import theme

_FUR = "#5b8fb0"          # slate-blue fur (echoes the avatar)
_FUR_DK = "#3f6a86"
_STRIPE = "#33566d"       # soft tabby markings (low-contrast)
_MUZZLE = "#cfe6f2"       # pale muzzle
_CHEST = "#bcdcec"        # pale chest blaze
_EYE = "#86e6bf"          # gentle glowing eyes (the coherence mint)
_EYE_DK = "#0c1f2c"
_NOSE = "#e7a6b0"         # soft pink nose / tongue
_INNER_EAR = "#caa0b4"
_ROUND = Qt.PenCapStyle.RoundCap
_NOPEN = Qt.PenStyle.NoPen


def _qc(hexs, a=1.0):
    c = QColor(hexs)
    c.setAlphaF(max(0.0, min(1.0, a)))
    return c


def _poly(*pts):
    return QPolygonF([QPointF(*p) for p in pts])


class CatFace:
    def draw(self, p, w, h, st):
        vol = float(st.get("vol", 0.5))
        t = float(st.get("t", 0.0))
        mouth = max(0.0, min(0.6, float(st.get("mouth", 0.0))))
        eye_open = max(0.04, min(1.0, float(st.get("eye_open", 1.0))))
        smile = max(0.0, min(1.0, float(st.get("smile", 0.12))))
        hue = st.get("hue", _EYE)
        cx = w / 2.0
        cy = h * 0.47 + math.sin(t * 0.6) * h * 0.006        # gentle breathing bob
        R = min(w, h) * 0.23 * (0.97 + 0.05 * vol)           # head radius (breathes)
        p.setPen(_NOPEN)

        # breath aura: a soft halo that swells on the in-breath, tinted by phase
        aura = QRadialGradient(cx, cy, R * 2.1)
        aura.setColorAt(0.0, _qc(hue, 0.07 + 0.13 * vol))
        aura.setColorAt(0.6, _qc(hue, 0.04 + 0.06 * vol))
        aura.setColorAt(1.0, _qc(hue, 0.0))
        p.setBrush(QBrush(aura))
        p.drawEllipse(QPointF(cx, cy), R * 2.1, R * 2.1)

        self._body(p, cx, cy, R, vol)
        self._ears(p, cx, cy, R, t, mouth)
        self._tufts(p, cx, cy, R)                            # fur behind the rim

        grad = QRadialGradient(cx, cy - R * 0.12, R * 1.25)  # head
        grad.setColorAt(0.0, _qc(theme.blend(_FUR, "#ffffff", 0.22)))
        grad.setColorAt(1.0, _qc(_FUR))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), R * 1.06, R)

        self._forehead(p, cx, cy, R)                         # tabby 'M'
        my = cy + R * 0.24
        p.setPen(_NOPEN)
        p.setBrush(_qc(_MUZZLE, 0.92))                       # pale muzzle
        p.drawEllipse(QPointF(cx, my + R * 0.08), R * 0.62, R * 0.48)

        self._eyes(p, cx, cy, R, t, vol, eye_open, smile)
        self._nose_mouth(p, cx, cy, R, my, mouth, smile)
        self._whiskers(p, cx, cy, R, t, mouth, my)

    # --- parts -------------------------------------------------------------
    def _body(self, p, cx, cy, R, vol):
        bw = R * 2.3 * (0.95 + 0.10 * vol)                   # chest widens on inhale
        bh = R * 1.7
        by = cy + R * 0.45 - R * 0.05 * vol                  # and rises a little
        p.setBrush(_qc(_FUR_DK, 0.95))
        p.drawRoundedRect(QRectF(cx - bw / 2, by, bw, bh), R * 0.7, R * 0.7)
        for s in (-1, 1):                                    # faint body stripes
            p.setBrush(_qc(_STRIPE, 0.5))
            for k in range(2):
                sx = cx + s * (bw * 0.2 + k * bw * 0.13)
                p.drawEllipse(QPointF(sx, by + bh * 0.5), bw * 0.022, bh * 0.32)
        p.setBrush(_qc(_CHEST, 0.45))                        # pale chest blaze
        p.drawEllipse(QPointF(cx, by + bh * 0.52), bw * 0.2, bh * 0.4)

    def _ears(self, p, cx, cy, R, t, mouth):
        twitch = math.sin(t * 0.8) * 0.05
        perk = mouth * R * 0.12                              # perk up while talking
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.6, cy - R * 0.58
            tip = QPointF(ex + s * R * 0.16, ey - R * 0.8 - s * twitch * R - perk)
            b1 = QPointF(ex - R * 0.34, ey + R * 0.02)
            b2 = QPointF(ex + R * 0.32, ey - R * 0.06)
            p.setBrush(_qc(_FUR))
            p.drawPolygon(_poly((tip.x(), tip.y()), (b1.x(), b1.y()),
                                (b2.x(), b2.y())))
            p.setBrush(_qc(_INNER_EAR, 0.85))
            p.drawPolygon(_poly(
                (tip.x(), tip.y() + R * 0.2),
                (ex * 0.6 + b1.x() * 0.4, ey * 0.55 + b1.y() * 0.45),
                (ex * 0.6 + b2.x() * 0.4, ey * 0.55 + b2.y() * 0.45)))

    def _tufts(self, p, cx, cy, R):
        p.setBrush(_qc(_FUR))
        for s in (-1, 1):
            bx = cx + s * R * 0.98
            for k in range(2):
                yy = cy + R * (0.04 + k * 0.2)
                p.drawPolygon(_poly((bx + s * R * 0.16, yy),
                                    (bx - s * R * 0.05, yy - R * 0.1),
                                    (bx - s * R * 0.05, yy + R * 0.1)))

    def _forehead(self, p, cx, cy, R):
        pen = QPen(_qc(_STRIPE, 0.55))
        pen.setWidthF(R * 0.05)
        pen.setCapStyle(_ROUND)
        p.setPen(pen)
        top = cy - R * 0.6
        p.drawLine(QPointF(cx, top), QPointF(cx, top + R * 0.3))
        for s in (-1, 1):
            p.drawLine(QPointF(cx + s * R * 0.13, top),
                       QPointF(cx + s * R * 0.22, top + R * 0.27))
        p.setPen(_NOPEN)

    def _eyes(self, p, cx, cy, R, t, vol, eye_open, smile):
        eyey = cy - R * 0.1
        ew = R * 0.31
        squint = max(0.0, smile - 0.3) / 0.7                 # happy -> narrow eyes
        eo = min(eye_open, 1.0 - 0.5 * squint)
        eh = R * 0.34 * eo + R * 0.015
        for s in (-1, 1):
            ex = cx + s * ew * 1.35
            g = QRadialGradient(ex, eyey, ew * 1.9)          # soft glow
            g.setColorAt(0.0, _qc(_EYE, 0.4 * eo))
            g.setColorAt(1.0, _qc(_EYE, 0.0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(ex, eyey), ew * 1.9, ew * 1.9)
            p.setBrush(_qc(_EYE_DK))
            p.drawEllipse(QPointF(ex, eyey), ew, eh)
            if eo > 0.22:
                p.setBrush(_qc(_EYE))                        # mint iris
                p.drawEllipse(QPointF(ex, eyey), ew * 0.74, eh * 0.86)
                pw = ew * (0.13 + 0.16 * vol)                # pupil dilates on inhale
                px = ex + math.sin(0.18 * t + s) * ew * 0.14
                py = eyey + math.sin(0.13 * t + s * 1.7) * eh * 0.1
                p.setBrush(_qc("#07121a"))
                p.drawEllipse(QPointF(px, py), pw, eh * 0.82)
                p.setBrush(_qc("#ffffff", 0.9))             # catchlight
                p.drawEllipse(QPointF(ex - ew * 0.24, eyey - eh * 0.34),
                              ew * 0.14, eh * 0.14)
            if squint > 0.05:                               # happy lower lid (fur)
                p.setBrush(_qc(theme.blend(_FUR, "#ffffff", 0.18)))
                lid = eh * (0.4 + 0.6 * squint)
                p.drawEllipse(QPointF(ex, eyey + eh + lid * 0.2 - eh * 0.1),
                              ew * 1.15, lid)

    def _nose_mouth(self, p, cx, cy, R, my, mouth, smile):
        ny = my - R * 0.02
        p.setPen(_NOPEN)
        p.setBrush(_qc(_NOSE))                              # nose (rounded triangle)
        p.drawPolygon(_poly((cx - R * 0.1, ny), (cx + R * 0.1, ny),
                            (cx, ny + R * 0.13)))
        p.setBrush(_qc("#ffffff", 0.55))                   # nose highlight
        p.drawEllipse(QPointF(cx - R * 0.03, ny + R * 0.02), R * 0.022, R * 0.018)
        my0 = ny + R * 0.13
        if mouth < 0.06:                                   # quiet: a content 'w'
            pen = QPen(_qc(_FUR_DK))
            pen.setWidthF(max(1.5, R * 0.03))
            pen.setCapStyle(_ROUND)
            p.setPen(pen)
            p.drawLine(QPointF(cx, my0 - R * 0.04), QPointF(cx, my0))  # philtrum
            span = int((150 + 40 * smile) * 16)            # smile widens the curve
            r2 = R * 0.17
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.15, r2, r2), 205 * 16, span)
            p.drawArc(QRectF(cx, my0 - r2 * 0.15, r2, r2), (335 * 16) - span, span)
            p.setPen(_NOPEN)
        else:                                              # talking: wider-than-tall
            ow = R * 0.24
            oh = R * (0.05 + 0.26 * mouth)
            mcy = my0 + R * 0.04 + oh
            p.setBrush(_qc("#241019"))
            p.drawEllipse(QPointF(cx, mcy), ow, oh)
            p.setBrush(_qc(_NOSE, 0.95))                   # tongue, low in the mouth
            p.drawEllipse(QPointF(cx, mcy + oh * 0.4), ow * 0.55, oh * 0.5)
            pen = QPen(_qc(_MUZZLE, 0.5))                  # soft lower lip / chin
            pen.setWidthF(R * 0.02)
            pen.setCapStyle(_ROUND)
            p.setPen(pen)
            p.drawArc(QRectF(cx - ow, mcy - oh * 0.1, ow * 2, oh * 2.1),
                      200 * 16, 140 * 16)
            p.setPen(_NOPEN)

    def _whiskers(self, p, cx, cy, R, t, mouth, my):
        pen = QPen(_qc("#eaf4f8", 0.72))
        pen.setWidthF(max(1.0, R * 0.013))
        pen.setCapStyle(_ROUND)
        p.setPen(pen)
        lift = mouth * R * 0.06                             # raise a touch on talk
        for s in (-1, 1):
            wx = cx + s * R * 0.26
            for k, (dy, ln, drop) in enumerate(
                    [(-0.02, 0.8, -0.05), (0.08, 0.88, 0.05), (0.18, 0.8, 0.14)]):
                sway = math.sin(t * 0.9 + k) * 0.015
                y0 = my + R * dy - lift
                mid = QPointF(wx + s * R * ln * 0.5, y0 + R * (drop * 0.4 + sway))
                end = QPointF(wx + s * R * ln, y0 + R * (drop + sway))
                p.drawLine(QPointF(wx, y0), mid)
                p.drawLine(mid, end)
        p.setPen(_NOPEN)
