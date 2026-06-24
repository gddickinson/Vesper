"""Generative 'cosmic' music: endless, non-repeating, soothing pads.

Research-grounded (Eno/Reich generative ambient + just-intonation 'music of the
spheres' + NASA-style cosmic sonification). The core trick, from Eno's and Reich's
phasing systems, is to overlap independent voices on slow, near-coprime cycles so
the texture *never exactly repeats*; randomness is constrained to a consonant scale
so it always sounds pleasant (no chaotic notes); and a steady drone anchors a very
slow harmonic drift, giving the gentlest tension and release. One engine plays
several 'palettes' (presets).

All NumPy, deterministically seeded, rendered in click-free blocks via absolute-time
oscillators (phase stays continuous with no accumulator, as in textures.py), and
washed through a spacious :class:`~breathsim.reverb.Reverb` -- ambient music lives
in reverb. Registered as the **Cosmic Music** voice group (``kind="texture"``); see
the bottom of voices.py.
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp
from .reverb import Reverb
from .textures import register_generator
from .voices import GROUP_MUSIC, VoiceConfig, register

TWO_PI = dsp.TWO_PI

# Just-intonation degrees (Pythagorean / Kepler 'harmony of the spheres'): small
# whole-number ratios are maximally consonant. This major-pentatonic subset has no
# semitone clashes, so *any* overlap of these tones stays restful.
_PENTA = [1 / 1, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2 / 1, 9 / 4, 5 / 2, 3 / 1]
# A softly wistful set (just minor third 6/5 and minor seventh 9/5) for deep space.
_MINOR = [1 / 1, 9 / 8, 6 / 5, 3 / 2, 9 / 5, 2 / 1, 12 / 5, 3 / 1]
# Consonant roots to drift slowly between (I, V, IV, vi, III flavours).
_ROOTS = [1 / 1, 3 / 2, 4 / 3, 5 / 4, 5 / 3, 6 / 5]


class _Pad:
    """A slow, soft sustained note: a small additive partial stack under a
    raised-cosine attack / hold / release, with gentle vibrato and a stereo pan."""

    def __init__(self, sr, f, t0, atk, hold, rel, amp, pan, partials, vib):
        self.f, self.t0 = f, t0
        self.atk, self.hold, self.rel = atk, hold, rel
        self.life = atk + hold + rel
        self.amp = amp / (sum(a for _, a in partials) + 1e-9)
        th = (pan + 1.0) * (math.pi / 4.0)
        self.gl, self.gr = math.cos(th), math.sin(th)
        self.partials = partials
        self.vr, self.vd = vib

    def render(self, tarr):
        ts = tarr - self.t0
        atk = np.clip(ts / self.atk, 0.0, 1.0)
        env = 0.5 - 0.5 * np.cos(np.pi * atk)                  # smooth fade in
        rs = np.clip((ts - self.atk - self.hold) / self.rel, 0.0, 1.0)
        env *= 0.5 + 0.5 * np.cos(np.pi * rs)                  # smooth fade out
        env = np.where((ts >= 0.0) & (ts <= self.life), env, 0.0)
        vib = self.vd * np.sin(TWO_PI * self.vr * tarr) if self.vd else 0.0
        tone = np.zeros(len(tarr))
        for ratio, pa in self.partials:
            tone += pa * np.sin(TWO_PI * self.f * ratio * tarr + vib)
        sig = tone * env * self.amp
        return sig * self.gl, sig * self.gr

    def dead(self, end):
        return (end - self.t0) > self.life


class _Cosmic:
    """Plays one palette: schedules overlapping pads on slow near-coprime gaps over
    a steady drone, drifts the root through consonant roots, optionally colours the
    pads with a vowel formant (choir) or adds an airy shimmer (deep space)."""

    def __init__(self, sr, rng, p):
        self.sr, self.rng, self.p = sr, rng, p
        self.pads = []
        self.next = 0.4
        self.base = p["base"]
        self.root = self.base
        self.root_next = p["root_period"]
        self.rev = Reverb(sr, p.get("damp", 2600.0))
        self.drone = p.get("drone", 0.0)
        sh = p.get("shimmer")
        if sh:
            self.nz = dsp.Noise("white", sr, seed=909)
            self.bp = dsp.Biquad(*dsp.bandpass(sr, sh[0], 0.7))
            self.sh_amp = sh[1]
        else:
            self.nz = None
        fmt = p.get("formant")          # parallel vowel resonators (per channel)
        if fmt:
            self.fl = [(dsp.Biquad(*dsp.bandpass(sr, fc, q)), g) for fc, q, g in fmt]
            self.fr = [(dsp.Biquad(*dsp.bandpass(sr, fc, q)), g) for fc, q, g in fmt]
        else:
            self.fl = None

    def _spawn(self, t):
        p = self.p
        f = self.root * float(self.rng.choice(p["scale"])) * \
            float(self.rng.choice(p["octaves"]))
        self.pads.append(_Pad(
            self.sr, f, t,
            self.rng.uniform(*p["attack"]), self.rng.uniform(*p["hold"]),
            self.rng.uniform(*p["release"]), self.rng.uniform(*p["amp"]),
            (self.rng.random() * 2 - 1) * p["pan"], p["partials"], p["vib"]))

    def step(self, tarr, frames):
        end = float(tarr[-1])
        if tarr[0] >= self.root_next:                 # slow consonant root drift
            self.root = self.base * float(self.rng.choice(self.p["roots"]))
            self.root_next += self.rng.uniform(*self.p["root_period_range"])
        while self.next < end:
            self._spawn(self.next)
            self.next += self.rng.uniform(*self.p["interval"])

        L, R = np.zeros(frames), np.zeros(frames)
        alive = []
        for pad in self.pads:
            l, r = pad.render(tarr)
            L += l
            R += r
            if not pad.dead(end):
                alive.append(pad)
        self.pads = alive

        if self.fl:                                   # vowel colour (choir)
            vL = sum(bp.process(L) * g for bp, g in self.fl)
            vR = sum(bp.process(R) * g for bp, g in self.fr)
            L, R = 0.6 * L + 1.3 * vL, 0.6 * R + 1.3 * vR
        if self.drone:                                # steady tonal anchor
            swell = 0.6 + 0.4 * np.sin(TWO_PI * 0.03 * tarr)
            d = (np.sin(TWO_PI * self.base * tarr)
                 + 0.5 * np.sin(TWO_PI * self.base * 2.0 * tarr)
                 + 0.3 * np.sin(TWO_PI * self.base * 1.5 * tarr)) * swell * self.drone
            L += d
            R += d
        if self.nz is not None:                       # airy high shimmer
            air = self.bp.process(self.nz.generate(frames))
            air = air * (0.5 + 0.5 * np.sin(TWO_PI * 0.05 * tarr + 1.3)) * self.sh_amp
            L += air
            R += air * 0.9

        wL, wR = self.rev.process(L, R)
        amt = self.p.get("reverb", 0.5)
        return np.column_stack([L * (1.0 - 0.25 * amt) + wL * amt,
                                R * (1.0 - 0.25 * amt) + wR * amt])


# --- palettes --------------------------------------------------------------
_SPHERES = dict(
    base=110.0, scale=_PENTA, roots=_ROOTS, octaves=[1.0, 2.0, 2.0, 4.0],
    root_period=42.0, root_period_range=(30.0, 60.0), interval=(3.0, 6.5),
    attack=(4.0, 7.0), hold=(3.0, 9.0), release=(6.0, 11.0), amp=(0.25, 0.5),
    pan=0.7, partials=[(1.0, 1.0), (2.0, 0.35), (3.0, 0.12), (4.0, 0.05)],
    vib=(0.18, 0.6), drone=0.16, reverb=0.55, damp=2800.0)

_CHOIR = dict(
    base=146.83, scale=_PENTA, roots=[1 / 1, 3 / 2, 5 / 4, 4 / 3],
    octaves=[1.0, 2.0, 2.0], root_period=36.0, root_period_range=(26.0, 50.0),
    interval=(2.2, 4.5), attack=(3.0, 6.0), hold=(2.5, 7.0), release=(5.0, 9.0),
    amp=(0.22, 0.42), pan=0.8,
    partials=[(1.0, 1.0), (2.0, 0.6), (3.0, 0.5), (4.0, 0.32), (5.0, 0.22),
              (6.0, 0.12)],
    vib=(5.2, 0.5), formant=[(700.0, 3.0, 1.0), (1100.0, 4.0, 0.7),
                             (2600.0, 6.0, 0.3)],
    drone=0.10, reverb=0.6, damp=3200.0)

_DEEP = dict(
    base=55.0, scale=_MINOR, roots=[1 / 1, 6 / 5, 4 / 3, 3 / 2],
    octaves=[1.0, 1.0, 2.0], root_period=55.0, root_period_range=(40.0, 80.0),
    interval=(7.0, 14.0), attack=(6.0, 10.0), hold=(6.0, 12.0),
    release=(8.0, 14.0), amp=(0.30, 0.55), pan=0.6,
    partials=[(0.5, 0.6), (1.0, 1.0), (2.0, 0.25), (3.0, 0.08)],
    vib=(0.12, 0.4), shimmer=(3800.0, 0.06), drone=0.22, reverb=0.7, damp=1900.0)

# (key, display name, palette, seed, calibrated gain, description). Gains are set
# so the worst peak over a long deterministic render sits near 0.75 (see
# tools-style calibration in SESSION_LOG); reverb buildup is included.
_PRESETS = [
    ("spheres", "Music of the Spheres", _SPHERES, 71, 0.46,
     "Slow, consonant pads drifting in just intonation over a soft drone - the "
     "harmony of the spheres."),
    ("choir", "Starlight Choir", _CHOIR, 72, 0.50,
     "An endless, wordless choir of vowel-like voices, swelling and fading among "
     "the stars."),
    ("deep", "Deep Space", _DEEP, 73, 0.40,
     "Vast, low, slow tones with an airy shimmer - the hush of the deep, dark "
     "between the stars."),
]


def _register():
    for key, name, pal, seed, gain, desc in _PRESETS:
        register_generator(key, (lambda s, r, p=pal: _Cosmic(s, r, p)), seed)
        register(VoiceConfig(name, GROUP_MUSIC, kind="texture", texture=key,
                             env="volume", floor=1.0, gain=gain, description=desc))


_register()
