"""Monophonic pitch detection (YIN) + an optional live microphone tuner.

`detect_pitch` is pure NumPy and unit-testable on synthetic tones. `Tuner`
opens a `sounddevice` input stream and exposes the latest detected pitch; it
degrades gracefully (``available = False``) when no input device or no
`sounddevice` is present, so the GUI can simply hide the read-out.
"""
from __future__ import annotations

import numpy as np


def detect_pitch(frame, sr, fmin=70.0, fmax=1000.0, threshold=0.15):
    """Return (frequency_hz, clarity 0..1). frequency is 0.0 if unvoiced.

    Implements the YIN cumulative-mean-normalised difference function with
    parabolic interpolation (de Cheveigne & Kawahara, 2002).
    """
    x = np.asarray(frame, dtype=np.float64)
    n = x.size
    tau_max = int(sr / fmin)
    tau_min = max(2, int(sr / fmax))
    if n < tau_max + 64:
        return (0.0, 0.0)
    w = n - tau_max                              # comparison window length
    if np.sqrt(np.mean(x * x)) < 1e-4:           # silence
        return (0.0, 0.0)

    # Difference function d(tau) over the window, then CMND normalisation.
    d = np.empty(tau_max + 1)
    d[0] = 0.0
    a = x[:w]
    for tau in range(1, tau_max + 1):
        diff = a - x[tau:tau + w]
        d[tau] = np.dot(diff, diff)
    cum = np.cumsum(d[1:])
    cmnd = np.ones(tau_max + 1)
    taus = np.arange(1, tau_max + 1)
    cmnd[1:] = d[1:] * taus / np.where(cum == 0, 1e-12, cum)

    # First dip below threshold (then descend to its local minimum), else best.
    tau = -1
    t = tau_min
    while t < tau_max:
        if cmnd[t] < threshold:
            while t + 1 < tau_max and cmnd[t + 1] < cmnd[t]:
                t += 1
            tau = t
            break
        t += 1
    if tau < 0:
        tau = int(np.argmin(cmnd[tau_min:tau_max])) + tau_min

    # Parabolic interpolation around the chosen lag for sub-sample accuracy.
    if 1 <= tau < tau_max:
        a0, a1, a2 = cmnd[tau - 1], cmnd[tau], cmnd[tau + 1]
        denom = a0 + a2 - 2 * a1
        shift = 0.5 * (a0 - a2) / denom if abs(denom) > 1e-12 else 0.0
        tau_i = tau + float(np.clip(shift, -1.0, 1.0))
    else:
        tau_i = float(tau)
    clarity = float(max(0.0, 1.0 - cmnd[tau]))
    return (sr / tau_i, clarity)


class Tuner:
    """Background microphone pitch tracker; optional and self-disabling."""

    def __init__(self, sr=44100, block=2048):
        self.sr = int(sr)
        self.block = int(block)
        self._stream = None
        self._hz = 0.0
        self._clarity = 0.0
        self.available = False

    def start(self) -> bool:
        if self._stream is not None:
            return self.available
        try:
            import sounddevice as sd
            self._stream = sd.InputStream(
                channels=1, samplerate=self.sr, blocksize=self.block,
                callback=self._callback)
            self._stream.start()
            self.available = True
        except Exception:
            self._stream = None
            self.available = False
        return self.available

    def _callback(self, indata, frames, time_info, status):
        hz, clarity = detect_pitch(indata[:, 0], self.sr)
        self._clarity = clarity
        if hz > 0 and clarity > 0.6:
            self._hz = hz

    def latest(self):
        """(frequency_hz, clarity) of the most recent confident detection."""
        return (self._hz, self._clarity)

    def stop(self):
        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
        except Exception:
            pass
        self._stream = None
        self.available = False
