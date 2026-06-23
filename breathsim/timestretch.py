"""WSOLA time-scale modification — change a sound's duration, keep its pitch.

Used to stretch a short spoken word so it lasts as long as the exhale, so the
word sounds *breathed out* over the whole breath rather than simply slowed down
(plain resampling would drop the pitch into a growl). WSOLA overlap-adds Hann
windowed grains at a fixed synthesis hop, sliding each grain's read position
within a small tolerance to best *continue* the previous grain — this keeps the
pitch and avoids the periodic buzz of naive overlap-add.

``time_stretch(x, ratio)`` returns roughly ``len(x) * ratio`` samples
(``ratio > 1`` lengthens). Mono in, mono out, pure numpy.
"""
from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def _resample_linear(x: np.ndarray, n: int) -> np.ndarray:
    if n <= 1:
        return np.zeros(max(n, 0))
    return np.interp(np.linspace(0.0, len(x) - 1, n), np.arange(len(x)), x)


def time_stretch(x, ratio: float, frame: int = 1024, tol: int = 400) -> np.ndarray:
    """Time-scale mono *x* by *ratio*, preserving pitch (WSOLA).

    Falls back to linear resampling for clips too short to window, and returns a
    copy unchanged when *ratio* is ~1."""
    x = np.asarray(x, dtype=float)
    n_in = len(x)
    out_len = int(round(n_in * max(ratio, 1e-4)))
    if out_len < 1:
        return np.zeros(0)
    if n_in < frame * 2:                        # too short for a windowed search
        return _resample_linear(x, out_len)
    if abs(ratio - 1.0) < 1e-3:
        return x.copy()

    Hs = frame // 2                             # synthesis hop (fixed)
    Ha = Hs / ratio                             # analysis hop (drives the rate)
    win = np.hanning(frame)
    base = tol + frame                          # leading pad so reads stay valid
    xp = np.concatenate([np.zeros(base), x,
                         np.zeros(2 * frame + Hs + tol + 2)])
    out = np.zeros(out_len + frame)
    norm = np.zeros(out_len + frame)

    delta = 0
    m = 0
    while m * Hs < out_len:
        read = base + int(round(m * Ha)) + delta
        read = min(max(read, 0), len(xp) - frame)
        s = m * Hs
        out[s:s + frame] += xp[read:read + frame] * win
        norm[s:s + frame] += win
        # The grain's "natural continuation" is the segment one synthesis hop on.
        nat = xp[read + Hs:read + Hs + frame]
        center = base + int(round((m + 1) * Ha))
        lo = max(0, center - tol)
        hi = min(len(xp) - frame, center + tol)
        if hi > lo and len(nat) == frame:
            cand = sliding_window_view(xp[lo:hi + frame], frame)
            energy = np.sqrt((cand * cand).sum(axis=1)) + 1e-6
            scores = (cand @ nat) / energy      # normalised cross-correlation
            delta = (lo + int(np.argmax(scores))) - center
        m += 1

    norm[norm < 1e-6] = 1.0
    return (out / norm)[:out_len]
