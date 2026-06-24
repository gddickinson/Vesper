"""Gentle, peak-safe stereo movement for the ambience bed.

Two subtle effects, both designed so they can *never* push the signal louder
than it came in (so calibrated peaks stay safe) and stay click-free (all state
carries across blocks):

- **Pseudo-stereo widening** (complementary-comb / Schroeder style): each output
  channel is a *convex* blend of its own channel and a short, differently-delayed
  copy of the other channel. Because it is a convex combination its magnitude is
  bounded by the input peak, yet the two slightly different delays decorrelate
  L and R so even a mono bed gains width and air.
- **Very slow auto-pan**: a sub-0.05 Hz balance drift that only ever *attenuates*
  one side (never boosts), so the bed sways gently without touching peak levels.

This is a width / pan effect for ambience, not 3D or binaural anything.
"""
from __future__ import annotations

import math

import numpy as np

TWO_PI = 2.0 * math.pi


class Spatializer:
    def __init__(self, sr, width=0.35, pan_depth=0.16, pan_hz=0.02,
                 dl_ms=17.0, dr_ms=23.0):
        self.sr = int(sr)
        self.width = float(max(0.0, min(0.5, width)))   # convex weight on the cross copy
        self.pan_depth = float(max(0.0, min(0.5, pan_depth)))
        self.pan_hz = float(pan_hz)
        self.dl = max(1, int(round(dl_ms * 1e-3 * sr)))
        self.dr = max(1, int(round(dr_ms * 1e-3 * sr)))
        self.maxd = max(self.dl, self.dr)
        self._tail_l = np.zeros(self.maxd)             # last maxd samples (dry)
        self._tail_r = np.zeros(self.maxd)
        self._n = 0                                    # free-running LFO sample count

    def process(self, stereo):
        """stereo: (frames, 2) float array -> (frames, 2). Stateful."""
        if stereo.ndim != 2 or stereo.shape[1] != 2:
            return stereo
        frames = stereo.shape[0]
        if frames == 0:
            return stereo
        left = stereo[:, 0]
        right = stereo[:, 1]
        md = self.maxd
        ext_l = np.concatenate([self._tail_l, left])
        ext_r = np.concatenate([self._tail_r, right])
        # delayed-by-d copy aligned to the current block: ext[md - d : md - d + frames]
        r_del = ext_r[md - self.dl: md - self.dl + frames]   # R into L, delay dl
        l_del = ext_l[md - self.dr: md - self.dr + frames]   # L into R, delay dr
        m = self.width
        lw = (1.0 - m) * left + m * r_del
        rw = (1.0 - m) * right + m * l_del
        # slow attenuate-only auto-pan (gains stay <= 1, so peak can only shrink)
        if self.pan_depth > 1e-6 and self.pan_hz > 0.0:
            t = (self._n + np.arange(frames)) / self.sr
            p = np.sin(TWO_PI * self.pan_hz * t)
            lw = lw * (1.0 - self.pan_depth * np.clip(p, 0.0, None))
            rw = rw * (1.0 - self.pan_depth * np.clip(-p, 0.0, None))
        self._n += frames
        self._tail_l = left[-md:] if frames >= md else np.concatenate(
            [self._tail_l[frames:], left])
        self._tail_r = right[-md:] if frames >= md else np.concatenate(
            [self._tail_r[frames:], right])
        return np.column_stack([lw, rw])


class SpatialTrack:
    """Wrap a track so its rendered stereo block is run through a Spatializer."""

    def __init__(self, inner, spatializer):
        self.inner = inner
        self.sp = spatializer

    def render(self, frames, s0, s1):
        return self.sp.process(self.inner.render(frames, s0, s1))
