"""A sound-wave + spectrum visualiser widget for the Qt Voice Editor.

``WaveformView.set_data(mono, sr)`` stores the rendered voice and repaints: a
min/max waveform on top (with a peak read-out, red if it would clip) over a
log-frequency magnitude spectrum below (so formants / brightness are visible
while editing). Pure QPainter + NumPy; no audio device needed. Mirrors the Tk
``WaveformView`` visual logic.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from . import theme

_DANGER = "#e0715f"          # clip warning (Qt theme has no DANGER)


def _qc(hexstr, alpha=1.0):
    c = QColor(hexstr)
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    return c


class WaveformView(QWidget):
    """Paints a min/max waveform over a log-frequency spectrum."""

    def __init__(self, width=424, height=160, parent=None):
        super().__init__(parent)
        self.W, self.H = int(width), int(height)
        self.setFixedSize(self.W, self.H)
        self._mono = np.zeros(0, dtype=float)
        self._sr = 44100

    def clear(self):
        self._mono = np.zeros(0, dtype=float)
        self.update()

    def set_data(self, mono, sr):
        """Store the rendered (mono) samples + sample rate and repaint."""
        x = np.asarray(mono, dtype=float)
        if x.ndim == 2:                       # mix stereo -> mono defensively
            x = x.mean(axis=1)
        self._mono = x
        self._sr = int(sr) if sr else 44100
        self.update()

    # Legacy parity: the Tk widget's method was named ``show``.
    show = set_data

    def _font(self, size=9):
        f = QFont("Helvetica Neue", size)
        return f

    def _text(self, p, x, y, text, hexcol, anchor="w", size=9):
        p.setPen(_qc(hexcol))
        p.setFont(self._font(size))
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(text)
        if anchor == "e":
            x = x - tw
        elif anchor == "c":
            x = x - tw / 2
        p.drawText(int(x), int(y + fm.ascent() / 2 - fm.descent() / 2), text)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        W, H = self.W, self.H
        p.fillRect(0, 0, W, H, _qc(theme.CARD))
        p.setPen(QPen(_qc(theme.BORDER), 1))
        p.drawRect(0, 0, W - 1, H - 1)

        wav_h = int(H * 0.56)
        mid = wav_h // 2
        x = self._mono
        peak = float(np.max(np.abs(x))) if x.size else 0.0

        p.setPen(QPen(_qc(theme.BORDER), 1))
        p.drawLine(0, mid, W, mid)

        if peak < 1e-6 or x.size < 8:
            self._text(p, W / 2, mid, "(silent)", theme.MUTED, anchor="c")
        else:
            norm = x / peak
            n = norm.size
            amp = wav_h * 0.46
            p.setPen(QPen(_qc(theme.ACCENT), 1))
            for px in range(W):
                a = int(px * n / W)
                b = max(a + 1, int((px + 1) * n / W))
                seg = norm[a:b]
                y0 = mid - float(seg.max()) * amp
                y1 = mid - float(seg.min()) * amp
                p.drawLine(px, int(y0), px, int(y1))

        clip = peak > 1.0
        label = f"peak {peak:.2f}" + ("  CLIP" if clip else "")
        self._text(p, W - 5, 9, label, _DANGER if clip else theme.MUTED,
                   anchor="e")

        self._spectrum(p, x, self._sr, wav_h + 6, H - 3)
        p.end()

    def _spectrum(self, p, x, sr, top, bottom):
        W = self.W
        p.setPen(QPen(_qc(theme.BORDER), 1))
        p.drawLine(0, top - 3, W, top - 3)
        win = 4096
        if x.size < win:
            self._text(p, W / 2, (top + bottom) / 2, "(no spectrum)",
                       theme.FAINT, anchor="c")
            return
        # Analyse the loudest window (where the voice is actually sounding).
        step = win // 2
        best_i, best = 0, 0.0
        for i in range(0, x.size - win, step):
            r = float(np.sqrt(np.mean(x[i:i + win] ** 2)))
            if r > best:
                best, best_i = r, i
        if best < 1e-6:
            self._text(p, W / 2, (top + bottom) / 2, "(no spectrum)",
                       theme.FAINT, anchor="c")
            return
        seg = x[best_i:best_i + win] * np.hanning(win)
        mag = np.abs(np.fft.rfft(seg))
        db = 20 * np.log10(mag + 1e-9)
        db -= db.max()
        nbins = mag.size
        f_lo, f_hi = 60.0, min(sr / 2.0, 11000.0)
        lspan = math.log10(f_hi / f_lo)
        h = bottom - top
        poly = QPolygonF()
        for px in range(W):
            f = f_lo * (10 ** ((px / W) * lspan))
            idx = min(nbins - 1, int(f / (sr / 2.0) * (nbins - 1)))
            y = bottom - max(0.0, (db[idx] + 70.0) / 70.0) * h     # -70 dB floor
            poly.append(QPointF(float(px), float(y)))
        if poly.size() >= 2:
            p.setPen(QPen(_qc(theme.ACCENT_WARM), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPolyline(poly)
        self._text(p, 5, top + 8, "spectrum", theme.FAINT, anchor="w")
