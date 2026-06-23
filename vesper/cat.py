"""A friendly 2D cartoon cat -- the fallback face when the 3D avatar (faceView)
isn't installed or can't render.

Pure QPainter: the cat breathes (gentle bob + zoom), blinks, twitches its ears,
its pupils wander, and its mouth opens to 'talk' -- all driven by the same
per-frame state the 3D face receives (`vol`, `mouth`, `eye_open`, `t`). It sits
over the same animated background as the 3D head, in the app's calm palette.
Force it with the env var ``VESPER_FACE=cat`` even when faceView is present.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF, QRadialGradient

from . import theme

_FUR = "#5b8fb0"          # slate-blue fur (echoes the avatar)
_FUR_DK = "#3f6a86"
_MUZZLE = "#cfe6f2"       # pale muzzle
_EYE = "#86e6bf"          # gentle glowing eyes (matches the coherence mint)
_NOSE = "#e7a6b0"         # soft pink nose
_INNER_EAR = "#caa0b4"


def _qc(hexs, a=1.0):
    c = QColor(hexs)
    c.setAlphaF(max(0.0, min(1.0, a)))
    return c


class CatFace:
    def draw(self, p, w, h, st):
        vol = float(st.get("vol", 0.5))
        t = float(st.get("t", 0.0))
        mouth = max(0.0, min(0.6, float(st.get("mouth", 0.0))))
        eye_open = max(0.04, min(1.0, float(st.get("eye_open", 1.0))))
        cx = w / 2.0
        cy = h * 0.47 + math.sin(t * 0.6) * h * 0.006        # gentle breathing bob
        R = min(w, h) * 0.23 * (0.97 + 0.05 * vol)           # head radius (breathes)
        p.setPen(Qt.PenStyle.NoPen)

        # shoulders / body, behind the head
        bw, bh = R * 2.3, R * 1.7
        p.setBrush(_qc(_FUR_DK, 0.92))
        p.drawRoundedRect(QRectF(cx - bw / 2, cy + R * 0.45, bw, bh), R * 0.7, R * 0.7)

        # ears (with a slow twitch), each with an inner ear
        tw = math.sin(t * 0.8) * 0.05
        for s in (-1, 1):
            ex, ey = cx + s * R * 0.6, cy - R * 0.58
            tip = QPointF(ex + s * R * 0.16, ey - R * 0.8 - s * tw * R)
            b1 = QPointF(ex - R * 0.34, ey + R * 0.02)
            b2 = QPointF(ex + R * 0.32, ey - R * 0.06)
            p.setBrush(_qc(_FUR))
            p.drawPolygon(QPolygonF([tip, b1, b2]))
            inner = QPolygonF([
                QPointF(tip.x(), tip.y() + R * 0.18),
                QPointF(ex * 0.6 + b1.x() * 0.4, ey * 0.55 + b1.y() * 0.45),
                QPointF(ex * 0.6 + b2.x() * 0.4, ey * 0.55 + b2.y() * 0.45)])
            p.setBrush(_qc(_INNER_EAR, 0.85))
            p.drawPolygon(inner)

        # head
        grad = QRadialGradient(cx, cy - R * 0.12, R * 1.25)
        grad.setColorAt(0.0, _qc(theme.blend(_FUR, "#ffffff", 0.22)))
        grad.setColorAt(1.0, _qc(_FUR))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), R * 1.06, R)

        # pale muzzle
        my = cy + R * 0.24
        p.setBrush(_qc(_MUZZLE, 0.92))
        p.drawEllipse(QPointF(cx, my + R * 0.08), R * 0.62, R * 0.48)

        # eyes (glow + iris + wandering slit pupil + catchlight)
        eyey = cy - R * 0.12
        ew, eh = R * 0.3, R * 0.32 * eye_open + R * 0.02
        for s in (-1, 1):
            ex = cx + s * R * 0.42
            g = QRadialGradient(ex, eyey, ew * 1.9)
            g.setColorAt(0.0, _qc(_EYE, 0.45 * eye_open))
            g.setColorAt(1.0, _qc(_EYE, 0.0))
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(ex, eyey), ew * 1.9, ew * 1.9)
            p.setBrush(_qc("#0d2230"))
            p.drawEllipse(QPointF(ex, eyey), ew, eh)
            if eye_open > 0.25:
                p.setBrush(_qc(_EYE))
                p.drawEllipse(QPointF(ex, eyey), ew * 0.72, eh * 0.84)
                px = ex + math.sin(0.2 * t + s) * ew * 0.16
                p.setBrush(_qc("#08131c"))
                p.drawEllipse(QPointF(px, eyey), ew * 0.2, eh * 0.8)
                p.setBrush(_qc("#ffffff", 0.85))
                p.drawEllipse(QPointF(ex - ew * 0.22, eyey - eh * 0.32),
                              ew * 0.12, eh * 0.12)

        # nose
        ny = my - R * 0.02
        p.setBrush(_qc(_NOSE))
        p.drawPolygon(QPolygonF([QPointF(cx - R * 0.1, ny),
                                 QPointF(cx + R * 0.1, ny),
                                 QPointF(cx, ny + R * 0.12)]))

        # mouth: a soft 'w' when quiet, opening to an oval (+ tongue) to talk
        my0 = ny + R * 0.12
        if mouth < 0.06:
            pen = QPen(_qc(_FUR_DK))
            pen.setWidthF(max(1.5, R * 0.03))
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            r2 = R * 0.17
            p.drawArc(QRectF(cx - r2, my0 - r2 * 0.2, r2, r2), 200 * 16, 160 * 16)
            p.drawArc(QRectF(cx, my0 - r2 * 0.2, r2, r2), 180 * 16, 160 * 16)
            p.setPen(Qt.PenStyle.NoPen)
        else:
            oh = R * (0.06 + 0.34 * mouth)         # smaller; opens downward only
            mcy = my0 + R * 0.04 + oh              # top edge sits below the nose
            p.setBrush(_qc("#26141c"))
            p.drawEllipse(QPointF(cx, mcy), R * 0.2, oh)
            p.setBrush(_qc(_NOSE, 0.9))            # tongue, low in the mouth
            p.drawEllipse(QPointF(cx, mcy + oh * 0.35), R * 0.1, oh * 0.5)

        # whiskers (slight sway)
        wp = QPen(_qc("#dfeef5", 0.7))
        wp.setWidthF(max(1.0, R * 0.012))
        p.setPen(wp)
        for s in (-1, 1):
            wx = cx + s * R * 0.28
            for k, (dy, ln, ang) in enumerate(
                    [(-0.04, 0.72, -0.12), (0.06, 0.8, 0.0), (0.16, 0.72, 0.12)]):
                sway = math.sin(t * 0.9 + k) * 0.02
                y0 = my + R * dy
                p.drawLine(QPointF(wx, y0),
                           QPointF(wx + s * R * ln, y0 + R * (ang + sway)))
        p.setPen(Qt.PenStyle.NoPen)
