"""The pitch-trainer scene (Qt): target line + live-pitch trail.

A note grid with a bright target line and a glowing trail of the singer's live
pitch (green in tune, amber off), plus plain-words "Higher / Lower / In tune"
guidance. Fed a ``pitch`` dict (lo/hi/target/next/sung/clarity/tol) via the
window's ``pitch_context`` merged with the mic Tuner. Used by Sing & Chant.
Mirrors the Tk PitchScene.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPen

from breathsim import music

from . import theme
from .scenes import _qc, _text

_GOOD, _OFF = theme.GOOD, theme.OFFP


class PitchScene:
    name = "pitch"
    N = 80

    def __init__(self):
        self._hist = []

    def draw(self, p, w, h, c):
        p.fillRect(0, 0, w, h, _qc(theme.BG))
        pitch = c.get("pitch")
        _text(p, w / 2, h - 20, c.get("status", ""), theme.MUTED, 11)
        if not pitch or not pitch.get("lo"):
            _text(p, w / 2, h * 0.45,
                  c.get("hint") or "Turn on the pitch guide (mic) to begin",
                  theme.MUTED, 14)
            return
        left, top, bottom, right = 54, 50, h - 64, w - 18
        lo, hi = pitch["lo"], pitch["hi"]
        span = max(1e-6, math.log2(hi / lo))
        tgt, nxt = pitch.get("target"), pitch.get("next")
        sung, clar = pitch.get("sung", 0.0), pitch.get("clarity", 0.0)
        tol = pitch.get("tol", 30)
        voiced = sung > 0 and clar > 0.5

        def y(hz):
            f = min(1.0, max(0.0, math.log2(max(1e-6, hz) / lo) / span))
            return bottom - f * (bottom - top)

        # Note grid + names.
        m_lo = int(math.ceil(69 + 12 * math.log2(lo / music.A4)))
        m_hi = int(math.floor(69 + 12 * math.log2(hi / music.A4)))
        p.setPen(QPen(_qc(theme.BORDER), 1))
        for m in range(m_lo, m_hi + 1):
            yy = y(music.midi_to_hz(m))
            p.setPen(QPen(_qc(theme.BORDER), 1))
            p.drawLine(int(left), int(yy), int(right), int(yy))
            nm = music.NOTE_NAMES[m % 12] + str(m // 12 - 1)
            _text(p, left - 18, yy, nm, theme.FAINT, 10)

        # Target line + label.
        if tgt:
            yt = y(tgt)
            p.setPen(QPen(_qc(theme.ACCENT), 3))
            p.drawLine(int(left), int(yt), int(right), int(yt))
            nm, _ = music.hz_to_note(tgt)
            _text(p, left + 44, yt - 11, f"target {nm}", theme.ACCENT, 11, bold=True)
        if tgt and nxt and abs(music.semitones(tgt, nxt)) >= 1:
            yn = y(nxt)
            p.setPen(QPen(_qc(theme.ACCENT_DIM), 2))
            p.drawLine(int(right - 46), int(yn), int(right), int(yn))
            _text(p, right - 64, yn, "next", theme.MUTED, 10)

        # Live pitch trail (newest at the right).
        self._hist.append(sung if voiced else 0.0)
        self._hist = self._hist[-self.N:]
        n = len(self._hist)
        x_lo, x_hi = left + 10, right - 8
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(n):
            hz = self._hist[n - 1 - i]
            if hz <= 0:
                continue
            xx = x_hi - (i / (self.N - 1)) * (x_hi - x_lo)
            cents = 1200 * math.log2(hz / tgt) if tgt else 0.0
            col = _GOOD if (tgt and abs(cents) < tol) else _OFF
            r = 6 if i == 0 else max(1.0, 4.0 * (1 - i / self.N))
            p.setBrush(_qc(col, 1.0 - 0.65 * i / self.N))
            p.drawEllipse(QPointF(xx, y(hz)), r, r)

        # In-tune glow: a soft green frame when the current note is on target.
        if pitch.get("intune"):
            for k, a in ((6, 0.10), (3, 0.22)):
                pen = QPen(_qc(_GOOD, a))
                pen.setWidthF(k)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(QRectF(left - 3, top - 3,
                                         right - left + 6, bottom - top + 6), 12, 12)
        # Running "% in tune" score (once enough has been sung).
        if pitch.get("samples", 0) > 15:
            _text(p, right - 58, top - 18, f"{pitch.get('score', 0.0):.0f}% in tune",
                  _GOOD, 13, bold=True)

        # Plain-words guidance.
        if voiced and tgt:
            cents = 1200 * math.log2(sung / tgt)
            if abs(cents) < tol:
                txt, col = "In tune", _GOOD
            elif cents < 0:
                txt, col = f"Higher  ↑   {cents:+.0f}c", theme.TEXT
            else:
                txt, col = f"Lower  ↓   {cents:+.0f}c", theme.TEXT
        elif voiced:
            nm, ce = music.hz_to_note(sung)
            txt, col = f"{nm}   {ce:+.0f}c", theme.TEXT
        else:
            txt = "Sing…" if c["running"] else "Press Start, then sing"
            col = theme.MUTED
        _text(p, w / 2, 26, txt, col, 22)
        if c.get("subtitle"):
            _text(p, w / 2, h - 44, c["subtitle"], theme.MUTED, 26)
