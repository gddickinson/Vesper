"""Visualization scenes drawn with QPainter (ambient set).

Each scene is a small object with a persistent state and a ``draw(p, w, h, c)``
method, where ``c`` is the per-frame context dict (breath volume/airflow/phase/
cycle_frac/remaining/label, anim time ``t``, ``prog``, ``running``, ``subtitle``,
``status``, ``hint``). Chosen by the active mode: Orb (meditate/breathwork),
Night (sleep), Ripple (chant/sing) and Wave (relax). The pitch trainer lives in
``scene_pitch.py``. Mirrors the Tk scenes, but with real alpha/gradient glow.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPen,
                           QPolygonF, QRadialGradient)

from . import scene_fx, theme

AMBIENT = ["orb", "night", "ripple", "wave", "fireplace"]


def _qc(hexstr, alpha=1.0):
    c = QColor(hexstr)
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    return c


def _text(p, cx, cy, text, hexcol, size, bold=False, alpha=1.0):
    if not text:
        return
    p.setPen(_qc(hexcol, alpha))
    f = QFont("Helvetica Neue", size)
    f.setBold(bold)
    p.setFont(f)
    fm = p.fontMetrics()
    tw = fm.horizontalAdvance(text)
    p.drawText(int(cx - tw / 2), int(cy + fm.ascent() / 2 - fm.descent() / 2), text)


def _overlay(p, w, cx, label_y, count_y, hint_y, status_y, c, hue,
             show_count=True):
    running = c["running"]
    _text(p, cx, label_y, c["label"] if running else "Ready",
          theme.blend(theme.TEXT, hue, 0.3), 26)
    count = ""
    if show_count and running and c["remaining"] > 0.05:
        count = str(int(math.ceil(c["remaining"] - 1e-6)))
    if c.get("subtitle"):
        count = c["subtitle"]
    _text(p, cx, count_y, count, theme.TEXT, 30 if c.get("subtitle") else 52,
          bold=not c.get("subtitle"))
    _text(p, cx, hint_y, c.get("hint", ""), theme.MUTED, 13)
    _text(p, cx, status_y, c.get("status", ""), theme.MUTED, 11)


class OrbScene:
    name = "orb"

    def __init__(self):
        self.motes = scene_fx.Motes(n=16, seed=4)
        self.rings = []                 # (spawn_t, hue) soft exhale rings
        self._last_phase = None

    def draw(self, p, w, h, c):
        p.fillRect(0, 0, w, h, _qc(theme.BG))
        cx, cy = w / 2, h * 0.45
        r_max = min(w, h) * 0.29
        r_min = r_max * 0.34
        running = c["running"]
        t = c["t"]
        vol = c["volume"] if running else 0.5
        radius = r_min + (r_max - r_min) * vol
        hue = theme.phase_hue(c["phase"]) if running else theme.ACCENT_DIM

        # a faint ambient vignette tints the dark field with the phase hue and
        # breathes with the orb (kept very low-contrast)
        amb = QRadialGradient(cx, cy, min(w, h) * 0.78)
        amb.setColorAt(0.0, _qc(theme.blend(theme.BG, hue, 0.13),
                                0.25 + 0.25 * vol))
        amb.setColorAt(1.0, _qc(theme.BG, 0.0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(amb))
        p.drawEllipse(QPointF(cx, cy), min(w, h) * 0.78, min(w, h) * 0.78)
        # a soft flattened reflection bloom below, as if the orb rests on stillness
        ry = cy + radius * 1.55
        refl = QRadialGradient(cx, ry, radius * 1.3)
        refl.setColorAt(0.0, _qc(theme.glow(hue, 0.3), 0.10 + 0.08 * vol))
        refl.setColorAt(1.0, _qc(hue, 0.0))
        p.setBrush(QBrush(refl))
        p.drawEllipse(QPointF(cx, ry), radius * 1.3, radius * 0.5)

        # soft exhale rings: a gentle ring expands outward at each exhale onset
        if running and c["phase"] != self._last_phase:
            if c["phase"] == "exhale":
                self.rings.append((t, hue))
            self._last_phase = c["phase"]
        elif not running:
            self._last_phase = c["phase"]
        speed, maxr = min(w, h) * 0.14, r_max * 2.1
        self.rings = [r for r in self.rings
                      if (t - r[0]) * speed < (maxr - radius)][-4:]
        p.setBrush(Qt.BrushStyle.NoBrush)
        for spawn, rhue in self.rings:
            rad = radius + (t - spawn) * speed
            frac = (rad - radius) / (maxr - radius + 1e-6)
            p.setPen(QPen(_qc(theme.glow(rhue, 0.4), 0.45 * (1 - frac)),
                          max(1.0, 2.5 * (1 - frac))))
            p.drawEllipse(QPointF(cx, cy), rad, rad)

        grad = QRadialGradient(cx, cy, radius * 1.55)
        grad.setColorAt(0.0, _qc(theme.glow(hue, 0.4), 0.5 + 0.4 * vol))
        grad.setColorAt(0.5, _qc(hue, 0.32 + 0.28 * vol))
        grad.setColorAt(1.0, _qc(hue, 0.0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), radius * 1.55, radius * 1.55)
        p.setBrush(_qc(theme.glow(hue, 0.18 + 0.16 * vol), 0.92))
        p.drawEllipse(QPointF(cx, cy), radius * 0.94, radius * 0.94)

        # floating motes drifting slowly over the field (dust in light)
        self.motes.draw(p, w, h, t, theme.glow(hue, 0.5),
                        alpha=0.30 if running else 0.16)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(_qc(theme.blend(theme.BG, hue, 0.5)), 1))
        p.drawEllipse(QPointF(cx, cy), r_max, r_max)

        # coherence cue: near ~6 breaths/min a soft mint halo breathes gently
        bpm = c.get("bpm", 0.0)
        if running and 5.0 <= bpm <= 7.0:
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * c.get("cycle_frac", 0.0))
            rcoh = r_max * 1.33
            p.setPen(QPen(_qc("#86e6bf", 0.10 + 0.15 * pulse), 2.5))
            p.drawEllipse(QPointF(cx, cy), rcoh, rcoh)

        if running:
            ang = -math.pi / 2 + 2 * math.pi * c.get("cycle_frac", 0.0)
            dx, dy = cx + r_max * math.cos(ang), cy + r_max * math.sin(ang)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_qc(theme.glow(hue, 0.55)))
            p.drawEllipse(QPointF(dx, dy), 5, 5)

        # Phase-progress ring: fills over the current phase, then resets. The
        # per-phase hue (cool inhale / mint hold / lavender exhale / blue rest)
        # makes the four phases — and the holds — read at a glance.
        if c["running"]:
            pr = max(0.0, min(1.0, c.get("progress", 0.0)))
            rp = r_max * 1.08
            rect = QRectF(cx - rp, cy - rp, 2 * rp, 2 * rp)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(_qc(theme.blend(theme.BG, hue, 0.30)), 2))
            p.drawArc(rect, 90 * 16, 360 * 16)               # faint full ring
            p.setPen(QPen(_qc(theme.glow(hue, 0.45)), 4))
            p.drawArc(rect, 90 * 16, int(-360 * pr * 16))    # bright phase sweep

        prog = c.get("prog") if c["running"] else None
        if prog is not None:
            r = r_max * 1.18
            rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(_qc(theme.BORDER), 2))
            p.drawArc(rect, 90 * 16, 360 * 16)
            p.setPen(QPen(_qc(theme.glow(hue, 0.25)), 3))
            p.drawArc(rect, 90 * 16, int(-360 * max(0.0, min(1.0, prog)) * 16))

        _overlay(p, w, cx, cy - 18, cy + 30, cy + r_max + 56, h - 22, c, hue)


class WaveScene:
    name = "wave"

    def __init__(self):
        rng = np.random.default_rng(8)
        self.stars = [dict(nx=float(rng.random()), ny=float(rng.random()) * 0.4,
                           ph=float(rng.random()) * 6.28,
                           sp=0.2 + float(rng.random()) * 0.5) for _ in range(26)]

    def draw(self, p, w, h, c):
        sky = QLinearGradient(0.0, 0.0, 0.0, float(h))
        sky.setColorAt(0.0, _qc(theme.blend(theme.BG, theme.WATER[0], 0.22)))
        sky.setColorAt(1.0, _qc(theme.blend(theme.BG, theme.WATER[2], 0.5)))
        p.fillRect(0, 0, w, h, QBrush(sky))
        vol = c["volume"] if c["running"] else 0.5
        t = c["t"]
        base = h * 0.6 - (vol - 0.5) * h * 0.22
        mx, my, mr = w * 0.70, h * 0.20, min(w, h) * 0.05
        p.setPen(Qt.PenStyle.NoPen)
        for s in self.stars:                          # a few faint stars in the sky
            sy = s["ny"] * h
            if sy > base - 14:
                continue
            tw = 0.5 + 0.5 * math.sin(t * 0.7 * s["sp"] + s["ph"])
            p.setBrush(_qc(theme.blend(theme.BG, theme.STAR, 0.2 + 0.6 * tw)))
            r = 0.5 + 1.2 * tw
            p.drawEllipse(QPointF(s["nx"] * w, sy), r, r)
        halo = QRadialGradient(mx, my, mr * 2.6)      # moon + soft halo
        halo.setColorAt(0.0, _qc(theme.MOON, 0.16))
        halo.setColorAt(1.0, _qc(theme.MOON, 0.0))
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(mx, my), mr * 2.6, mr * 2.6)
        p.setBrush(_qc(theme.MOON, 0.85))
        p.drawEllipse(QPointF(mx, my), mr, mr)
        hglow = QLinearGradient(0.0, base - 26, 0.0, base)   # soft glow at the horizon
        hgcol = theme.blend(theme.WATER[2], theme.MOON, 0.35)
        hglow.setColorAt(0.0, _qc(hgcol, 0.0))
        hglow.setColorAt(1.0, _qc(hgcol, 0.16))
        p.fillRect(0, int(base - 26), w, 26, QBrush(hglow))
        for i, col in enumerate(theme.WATER):         # smoother layered swells
            amp, speed = 8 + 6 * i, 0.6 + 0.3 * i
            k = 2 * math.pi / (w * (0.55 + 0.3 * i))
            off = base + i * 24
            poly = QPolygonF()
            x = 0
            while x <= w + 12:
                poly.append(QPointF(x, off + amp * math.sin(x * k + t * speed + i)))
                x += 12
            poly.append(QPointF(w, h))
            poly.append(QPointF(0, h))
            p.setBrush(_qc(col, 0.92))
            p.drawPolygon(poly)
        glint = QLinearGradient(0.0, base, 0.0, float(h))  # moonlight path on the sea
        glint.setColorAt(0.0, _qc(theme.MOON, 0.13))
        glint.setColorAt(1.0, _qc(theme.MOON, 0.0))
        gw = mr * 2.2 * (0.85 + 0.4 * vol)            # breathes a touch with the breath
        p.fillRect(int(mx - gw / 2), int(base), int(gw), int(h - base), QBrush(glint))
        for j in range(10):                           # moon-reflection shimmer
            yy = base + j * (h - base) / 10.0
            sway = math.sin(t * 1.2 + j * 0.7) * (4 + j)
            ww = mr * (0.7 + j * 0.16)
            p.setBrush(_qc(theme.MOON, 0.10 * (1 - j / 10.0)))
            p.drawEllipse(QPointF(mx + sway, yy), ww, 2.2)
        k0, amp0, sp0 = 2 * math.pi / (w * 0.55), 8, 0.6   # foam crests on the top
        p.setBrush(_qc(theme.blend(theme.WATER[0], "#ffffff", 0.7), 0.5))
        x = 0
        while x <= w:
            sn = math.sin(x * k0 + t * sp0)
            if sn < -0.82:
                p.drawEllipse(QPointF(x, base + amp0 * sn), 1.8, 1.1)
            x += 14
        hue = theme.phase_hue(c["phase"]) if c["running"] else theme.ACCENT
        _overlay(p, w, w / 2, base - 74, base - 34, h - 56, h - 22, c, hue)


class NightScene:
    name = "night"

    def __init__(self):
        rng = np.random.default_rng(3)
        self.stars = [dict(nx=float(rng.random()), ny=float(rng.random()),
                           ph=float(rng.random()) * 6.28,
                           sp=0.2 + float(rng.random()) * 0.6) for _ in range(64)]
        # a fainter, slower far layer for depth (parallax + gentler twinkle)
        self.far = [dict(nx=float(rng.random()), ny=float(rng.random()),
                         ph=float(rng.random()) * 6.28,
                         sp=0.1 + float(rng.random()) * 0.3) for _ in range(96)]
        self.clouds = scene_fx.Clouds(n=4, seed=6)
        self.shoot = scene_fx.ShootingStar(seed=11)

    def draw(self, p, w, h, c):
        # deeper vertical gradient: near-black overhead easing to the night blue
        grad = QLinearGradient(0.0, 0.0, 0.0, float(h))
        grad.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#000007", 0.55)))
        grad.setColorAt(1.0, _qc(theme.NIGHT_BG))
        p.fillRect(0, 0, w, h, QBrush(grad))
        vol = c["volume"] if c["running"] else 0.5
        t = c["t"]
        # a faint, dim horizon glow low on the sky (deep indigo, never bright)
        glow = QLinearGradient(0.0, float(h) * 0.7, 0.0, float(h))
        glow.setColorAt(0.0, _qc(theme.blend(theme.NIGHT_BG, "#1b2746", 0.6), 0.0))
        glow.setColorAt(1.0, _qc(theme.blend(theme.NIGHT_BG, "#1b2746", 0.6), 0.28))
        p.fillRect(0, int(h * 0.7), w, h - int(h * 0.7), QBrush(glow))
        self.clouds.draw(p, w, h, t,
                         _qc(theme.blend(theme.NIGHT_BG, theme.MOON, 0.5), 0.05))
        p.setPen(Qt.PenStyle.NoPen)
        for s in self.far:                          # far layer: smaller, dimmer, slower
            y = (s["ny"] + t * 0.006 * s["sp"]) % 1.0
            tw = 0.5 + 0.5 * math.sin(t * 0.5 * s["sp"] + s["ph"])
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, theme.STAR, 0.12 + 0.3 * tw)))
            r = 0.4 + 0.7 * tw
            p.drawEllipse(QPointF(s["nx"] * w, y * h), r, r)
        for s in self.stars:
            y = (s["ny"] + t * 0.012 * s["sp"]) % 1.0
            tw = 0.5 + 0.5 * math.sin(t * 0.8 * s["sp"] + s["ph"])
            p.setBrush(_qc(theme.blend(theme.NIGHT_BG, theme.STAR, 0.25 + 0.7 * tw)))
            r = 0.6 + 1.6 * tw
            p.drawEllipse(QPointF(s["nx"] * w, y * h), r, r)
        self.shoot.draw(p, w, h, t, theme.STAR)
        mx, my, mr = w * 0.72, h * 0.26, min(w, h) * 0.075
        halo = QRadialGradient(mx, my, mr * (2.4 + 0.9 * vol))
        halo.setColorAt(0.0, _qc(theme.MOON, 0.18 + 0.12 * vol))
        halo.setColorAt(1.0, _qc(theme.MOON, 0.0))
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(mx, my), mr * (2.4 + 0.9 * vol), mr * (2.4 + 0.9 * vol))
        p.setBrush(_qc(theme.MOON))
        p.drawEllipse(QPointF(mx, my), mr, mr)
        # a subtle, very slowly drifting crescent: a sky-coloured disc carves the
        # terminator, so the moon shows a gentle gibbous/crescent phase
        off = (0.42 + 0.12 * math.sin(t * 0.01)) * mr
        sky = _qc(theme.blend(theme.NIGHT_BG, "#000007", 0.28))
        p.setBrush(sky)
        p.drawEllipse(QPointF(mx + off, my - off * 0.35), mr * 1.04, mr * 1.04)
        hue = theme.blend(theme.STAR, theme.ACCENT, 0.35)
        _overlay(p, w, w / 2, h * 0.62, h * 0.62 + 40, h * 0.62 + 78, h - 22, c, hue)


class RippleScene:
    name = "ripple"
    POOL = 9

    def __init__(self):
        self.active = []
        self._last = None
        self._next = 0.0

    def draw(self, p, w, h, c):
        p.fillRect(0, 0, w, h, _qc(theme.RIPPLE_BG))
        cx, cy = w / 2, h * 0.46
        vol = c["volume"] if c["running"] else 0.5
        t, running = c["t"], c["running"]
        hue_now = theme.phase_hue(c["phase"]) if running else theme.ACCENT
        sheen = QRadialGradient(cx, cy, min(w, h) * 0.62)  # still-water sheen, hue-drift
        sheen.setColorAt(0.0, _qc(theme.blend(theme.RIPPLE_BG, hue_now, 0.10), 0.5))
        sheen.setColorAt(1.0, _qc(theme.RIPPLE_BG, 0.0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(sheen))
        p.drawEllipse(QPointF(cx, cy), min(w, h) * 0.62, min(w, h) * 0.62)
        if running and t >= self._next:
            self.active.append((t, hue_now, vol))
            self._next = t + (1.4 - 0.6 * vol)            # louder tone -> closer rings
        if running and c["phase"] != self._last:
            if c["phase"] in ("inhale", "exhale"):
                self.active.append((t, hue_now, vol))
            self._last = c["phase"]
        elif not running:
            self._last = c["phase"]
        speed, maxr = 70.0, min(w, h) * 0.55
        self.active = [r for r in self.active
                       if (t - r[0]) * speed < maxr][-self.POOL:]
        p.setBrush(Qt.BrushStyle.NoBrush)
        for spawn, rhue, rv in self.active:               # colour brightens with tone
            rad = (t - spawn) * speed
            frac = rad / maxr
            col = theme.blend(theme.blend(rhue, "#ffffff", 0.25 * rv),
                              theme.RIPPLE_BG, frac)
            p.setPen(QPen(_qc(col), max(1.0, 3 * (1 - frac))))
            p.drawEllipse(QPointF(cx, cy), rad, rad)
            if rad > 6:                                   # faint companion (interference)
                p.setPen(QPen(_qc(col, 0.3 * (1 - frac)), 1.0))
                p.drawEllipse(QPointF(cx, cy), rad * 0.82, rad * 0.82)
        hue = hue_now
        cr = min(w, h) * 0.05 * (0.7 + 0.6 * vol)
        gl = QRadialGradient(cx, cy, cr * 3.0)            # central glow pulses w/ tone
        gl.setColorAt(0.0, _qc(theme.glow(hue, 0.45), 0.4 + 0.4 * vol))
        gl.setColorAt(1.0, _qc(hue, 0.0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(gl))
        p.drawEllipse(QPointF(cx, cy), cr * 3.0, cr * 3.0)
        p.setBrush(_qc(theme.blend(hue, "#ffffff", 0.2 * vol)))
        p.drawEllipse(QPointF(cx, cy), cr, cr)
        _overlay(p, w, cx, cy - 70, cy + 4, h - 56, h - 22, c, hue)


class FireplaceScene:
    """A soft hearth: a warm pulsing glow, gently flickering flame tongues and a
    few embers rising and fading. Slow and low-contrast (no strobing); pairs with
    the Campfire ambience. Motion is derived from anim time, so it is smooth and
    reproducible with no per-frame randomness."""
    name = "fireplace"
    _BG_TOP, _BG_BOT = "#0c0a08", "#1b1008"
    _BASE, _MID, _TIP, _EMBER = "#c0461a", "#e8842c", "#f4c350", "#f0b860"

    def __init__(self):
        rng = np.random.default_rng(21)
        self.tongues = [dict(
            dx=(float(rng.random()) * 2 - 1) * 0.11, wd=0.045 + 0.045 * float(rng.random()),
            ht=0.17 + 0.12 * float(rng.random()), swp=float(rng.random()) * 6.28,
            sws=0.5 + float(rng.random()) * 0.7, flp=float(rng.random()) * 6.28,
            fls=0.7 + float(rng.random()) * 0.9) for _ in range(7)]
        self.embers = [dict(
            x0=(float(rng.random()) * 2 - 1) * 0.17, sp=0.5 + float(rng.random()) * 0.8,
            ph=float(rng.random()), dr=float(rng.random()) * 6.28,
            sz=1.0 + float(rng.random()) * 1.7) for _ in range(14)]

    def draw(self, p, w, h, c):
        grad = QLinearGradient(0.0, 0.0, 0.0, float(h))
        grad.setColorAt(0.0, _qc(self._BG_TOP))
        grad.setColorAt(1.0, _qc(self._BG_BOT))
        p.fillRect(0, 0, w, h, QBrush(grad))
        t, running = c["t"], c["running"]
        vol = c["volume"] if running else 0.5
        cx, base = w * 0.5, h * 0.78
        breath = 0.85 + 0.30 * vol                       # the fire breathes with you
        p.setPen(Qt.PenStyle.NoPen)
        gr = min(w, h) * 0.55                             # warm hearth glow
        glow = QRadialGradient(cx, base, gr)
        glow.setColorAt(0.0, _qc(self._MID, 0.20 + 0.16 * vol))
        glow.setColorAt(0.5, _qc(self._BASE, 0.10 + 0.07 * vol))
        glow.setColorAt(1.0, _qc(self._BASE, 0.0))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(cx, base), gr, gr)
        for sgn in (-1, 1):                               # two dark logs at the base
            p.save()
            p.translate(cx + sgn * w * 0.05, base + 10)
            p.rotate(sgn * 11)
            p.setBrush(_qc("#1c0f08"))
            p.drawRoundedRect(QRectF(-w * 0.14, -7, w * 0.28, 14), 6, 6)
            p.restore()
        for tg in self.tongues:                           # soft, swaying flame tongues
            flick = 0.82 + 0.18 * math.sin(t * tg["fls"] + tg["flp"])
            sway = math.sin(t * tg["sws"] + tg["swp"]) * w * 0.012
            tx, th, tw = cx + tg["dx"] * w, tg["ht"] * h * breath * flick, tg["wd"] * w
            steps = 7
            for i in range(steps):
                f = i / (steps - 1)                       # 0 base -> 1 tip
                yy, xx = base - f * th, tx + sway * f
                rad = tw * (1.0 - 0.65 * f)
                col = theme.blend(theme.blend(self._BASE, self._MID, min(1.0, f * 1.6)),
                                  self._TIP, max(0.0, f * 1.5 - 0.5))
                a = (0.13 + 0.10 * vol) * (1.0 - 0.45 * f)
                bg = QRadialGradient(xx, yy, rad)
                bg.setColorAt(0.0, _qc(col, min(1.0, a * 1.7)))
                bg.setColorAt(1.0, _qc(col, 0.0))
                p.setBrush(QBrush(bg))
                p.drawEllipse(QPointF(xx, yy), rad, rad * 1.4)
        core = QRadialGradient(cx, base - h * 0.05, w * 0.11)   # bright heart
        core.setColorAt(0.0, _qc(self._TIP, 0.16 + 0.16 * vol))
        core.setColorAt(1.0, _qc(self._TIP, 0.0))
        p.setBrush(QBrush(core))
        p.drawEllipse(QPointF(cx, base - h * 0.05), w * 0.11, w * 0.11)
        for e in self.embers:                             # embers drifting upward
            cyc = (t * 0.08 * e["sp"] + e["ph"]) % 1.0
            ey = base - cyc * h * 0.55
            ex = cx + e["x0"] * w + math.sin(t * 0.6 + e["dr"]) * w * 0.02
            a = max(0.0, 1.0 - cyc) * 0.7
            p.setBrush(_qc(theme.blend(self._EMBER, "#ffffff", 0.2), a))
            p.drawEllipse(QPointF(ex, ey), e["sz"], e["sz"])
        _overlay(p, w, cx, h * 0.30, h * 0.30 + 40, h * 0.30 + 78, h - 22,
                 c, self._MID)


_CLASSES = {"orb": OrbScene, "night": NightScene, "ripple": RippleScene,
            "wave": WaveScene, "fireplace": FireplaceScene}

# Larger scenes live in their own modules (keeps this file small); register here.
from .scene_rain import RainScene  # noqa: E402
_CLASSES["rain"] = RainScene
AMBIENT.append("rain")
from .scene_aurora import AuroraScene  # noqa: E402
_CLASSES["aurora"] = AuroraScene
AMBIENT.append("aurora")
from .scene_mandala import MandalaScene  # noqa: E402
_CLASSES["mandala"] = MandalaScene
AMBIENT.append("mandala")


def make(name):
    if name == "pitch":
        from .scene_pitch import PitchScene
        return PitchScene()
    return _CLASSES.get(name, OrbScene)()


def names():
    return AMBIENT
