"""A light, click-free reverb for the generative pads (block-delay feedback combs).

Ambient music lives in reverb; a sense of vast, slow space is what makes drifting
pads feel 'cosmic'. We use a bank of parallel feedback comb filters whose delay
lengths all exceed one audio block, so each block's feedback depends only on past
blocks -- there is no per-sample recursion, so the whole thing stays vectorised and
click-free across the streaming callbacks. A one-pole low-pass in each feedback
path damps the tail over time, the way real rooms swallow the highs, which reads as
warm and soothing rather than metallic.
"""
from __future__ import annotations

import numpy as np

from . import dsp

# (delay in samples, feedback gain). Coprime-ish primes give a smooth, slow wash;
# all are >= 2048 so they exceed the engine's audio block (so feedback is purely
# from past blocks). The Reverb chunks oversized blocks to keep this invariant.
_COMBS = [(2939, 0.80), (3181, 0.79), (3413, 0.77),
          (3677, 0.75), (4001, 0.73), (4283, 0.71)]
_STEREO = 233          # right-channel delay offset (samples) for a wide image


class _Comb:
    """A single damped feedback comb: y[n] = x[n] + g * lowpass(y[n-D])."""

    def __init__(self, sr, D, g, damp_fc):
        self.sr, self.D, self.g, self.damp_fc = sr, D, g, damp_fc
        self.buf = np.zeros(D)         # the last D output samples (oldest first)
        self.lp = dsp.OnePoleLP()

    def process(self, x):
        n = len(x)                     # caller guarantees n <= D
        delayed = self.buf[:n]         # y[n-D .. n-D+len]
        y = x + self.lp.process(delayed, self.damp_fc, self.sr) * self.g
        self.buf = np.concatenate([self.buf[n:], y])
        return y


class Reverb:
    """A stereo reverb: parallel damped combs (L and R slightly detuned), summed
    and gently low-passed. ``process(L, R)`` returns the wet (reverberated) pair;
    the caller mixes it with the dry signal."""

    def __init__(self, sr, damp_fc=2600.0):
        self.sr = sr
        self.min_d = min(d for d, _ in _COMBS)
        self.cl = [_Comb(sr, d, g, damp_fc) for d, g in _COMBS]
        self.cr = [_Comb(sr, d + _STEREO, g, damp_fc) for d, g in _COMBS]
        self.olp, self.orp = dsp.OnePoleLP(), dsp.OnePoleLP()
        self.n = len(_COMBS)

    def _bank(self, bank, x, olp):
        wet = np.zeros(len(x))
        for c in bank:
            wet += c.process(x)
        return olp.process(wet / self.n, 5200.0, self.sr)

    def process(self, L, R):
        if len(L) <= self.min_d:
            return (self._bank(self.cl, L, self.olp),
                    self._bank(self.cr, R, self.orp))
        outL, outR = [], []            # chunk oversized blocks (keep D >= chunk)
        for i in range(0, len(L), self.min_d):
            outL.append(self._bank(self.cl, L[i:i + self.min_d], self.olp))
            outR.append(self._bank(self.cr, R[i:i + self.min_d], self.orp))
        return np.concatenate(outL), np.concatenate(outR)
