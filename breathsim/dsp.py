"""Low-level DSP building blocks: coloured noise and stateful filters.

Everything here processes audio in blocks while carrying filter state across
calls, so a real-time stream produces a continuous, click-free signal.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import signal

TWO_PI = 2.0 * math.pi


# --- Biquad filter designers (RBJ audio EQ cookbook) -----------------------

def _clamp_fc(fc: float, sr: int) -> float:
    return float(min(max(fc, 20.0), sr * 0.45))


def lowpass(sr: int, fc: float, q: float = 0.707):
    w0 = TWO_PI * _clamp_fc(fc, sr) / sr
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    b0, b1, b2 = (1 - cw) / 2, 1 - cw, (1 - cw) / 2
    a0, a1, a2 = 1 + alpha, -2 * cw, 1 - alpha
    return _norm(b0, b1, b2, a0, a1, a2)


def highpass(sr: int, fc: float, q: float = 0.707):
    w0 = TWO_PI * _clamp_fc(fc, sr) / sr
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    b0, b1, b2 = (1 + cw) / 2, -(1 + cw), (1 + cw) / 2
    a0, a1, a2 = 1 + alpha, -2 * cw, 1 - alpha
    return _norm(b0, b1, b2, a0, a1, a2)


def bandpass(sr: int, fc: float, q: float = 1.0):
    w0 = TWO_PI * _clamp_fc(fc, sr) / sr
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    b0, b1, b2 = alpha, 0.0, -alpha          # constant 0 dB peak gain
    a0, a1, a2 = 1 + alpha, -2 * cw, 1 - alpha
    return _norm(b0, b1, b2, a0, a1, a2)


def _norm(b0, b1, b2, a0, a1, a2):
    b = np.array([b0, b1, b2]) / a0
    a = np.array([1.0, a1 / a0, a2 / a0])
    return b, a


class Biquad:
    """A static second-order section processed block by block."""

    def __init__(self, b, a):
        self.b = np.asarray(b, dtype=float)
        self.a = np.asarray(a, dtype=float)
        self.zi = np.zeros(max(len(self.a), len(self.b)) - 1)

    def process(self, x: np.ndarray) -> np.ndarray:
        y, self.zi = signal.lfilter(self.b, self.a, x, zi=self.zi)
        return y

    def update(self, b, a):
        """Swap coefficients while keeping filter state (for swept filters)."""
        self.b = np.asarray(b, dtype=float)
        self.a = np.asarray(a, dtype=float)


class OnePoleLP:
    """One-pole low-pass with a cutoff that can change smoothly per block.

    Used for dynamic 'brightness' modulation (e.g. a breath getting brighter
    at peak airflow) without the coefficient-swap clicks of a biquad.
    """

    def __init__(self):
        self.zi = np.zeros(1)

    def process(self, x: np.ndarray, fc: float, sr: int) -> np.ndarray:
        fc = _clamp_fc(fc, sr)
        alpha = 1.0 - math.exp(-TWO_PI * fc / sr)
        b = np.array([alpha])
        a = np.array([1.0, -(1.0 - alpha)])
        y, self.zi = signal.lfilter(b, a, x, zi=self.zi)
        return y


# --- Coloured noise --------------------------------------------------------

# Paul Kellet's economy IIR pink-noise filter (approx -3 dB/oct, 20-20k Hz).
_PINK_B = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
_PINK_A = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])

# Scale factors that bring each colour to roughly unit RMS (measured).
_SCALE = {"white": 1.0, "pink": 12.0, "brown": 0.141}


class Noise:
    """Stateful coloured-noise generator (white / pink / brown)."""

    def __init__(self, kind: str = "white", sr: int = 44100, seed=None):
        self.kind = kind
        self.sr = sr
        self.rng = np.random.default_rng(seed)
        self._pink_zi = np.zeros(max(len(_PINK_A), len(_PINK_B)) - 1)
        self._brown_zi = np.zeros(1)
        self.scale = _SCALE.get(kind, 1.0)

    def generate(self, frames: int) -> np.ndarray:
        white = self.rng.standard_normal(frames)
        if self.kind == "white":
            out = white
        elif self.kind == "pink":
            out, self._pink_zi = signal.lfilter(
                _PINK_B, _PINK_A, white, zi=self._pink_zi)
        elif self.kind == "brown":
            # Leaky integrator -> -6 dB/oct red noise.
            out, self._brown_zi = signal.lfilter(
                [1.0], [1.0, -0.99], white, zi=self._brown_zi)
        else:
            out = white
        return out * self.scale


def soft_clip(x: np.ndarray) -> np.ndarray:
    """Gentle tanh limiter to keep the master bus from clipping."""
    return np.tanh(x)
