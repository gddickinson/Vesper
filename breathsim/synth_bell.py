"""Bells & gongs: a physically-grounded struck-resonator synth + a wide library.

A struck bell/bowl/gong is a set of decaying **inharmonic partials** (modes), each
a sine with its own amplitude and decay time, started by a soft strike. Real bells
follow the Hemony partial pattern relative to the prime: hum 0.5, prime 1.0, tierce
1.2 (a minor third -- the plaintive bell quality), quint 1.5, nominal 2.0, then
3.0 / 4.0; low partials are quiet but long, high ones bright but short. Gongs add
many dense inharmonic partials that **bloom** (swell in after the strike). Tibetan
bowls are inharmonic with close modes that **beat** slowly. Triangles are nearly
all high overtones. We model all of these with one configurable resonator.

Each instrument is a ``kind="texture"`` voice (plugged in via
``textures.register_generator``) that tolls slowly on its own -- a calm bell/gong
bed for meditation, chant or ambience. Registered as the **Bells & Gongs** group.
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp
from .textures import register_generator
from .voices import GROUP_BELLS, VoiceConfig, register

TWO_PI = dsp.TWO_PI


class _Bell:
    """One struck resonator: a stack of decaying (optionally blooming) partials.

    ``modes`` = list of (ratio, amp, decay_s, bloom_s). Absolute-time sines keep
    the phase continuous across blocks with no accumulator."""

    def __init__(self, sr, f0, modes, t0, amp, pan, decay_scale=1.0):
        self.t0 = t0
        self.f = [f0 * r for r, _, _, _ in modes]
        self.a = [a for _, a, _, _ in modes]
        self.dec = [d * decay_scale for _, _, d, _ in modes]
        self.bloom = [b for _, _, _, b in modes]
        self.amp = amp / (sum(self.a) + 1e-9)
        th = (pan + 1.0) * (math.pi / 4.0)
        self.gl, self.gr = math.cos(th), math.sin(th)
        self.dmax = max(self.dec)

    def render(self, tarr):
        ts = tarr - self.t0
        atk = np.clip(ts / 0.004, 0.0, 1.0)            # 4 ms onset, no click
        out = np.zeros(len(tarr))
        tsp = np.maximum(ts, 0.0)
        for f, a, dec, bloom in zip(self.f, self.a, self.dec, self.bloom):
            env = atk * np.exp(-tsp / dec)
            if bloom > 0.0:
                env = env * (1.0 - np.exp(-tsp / bloom))   # swell in (gong bloom)
            out += a * np.sin(TWO_PI * f * tarr) * env
        out = np.where(ts >= 0.0, out, 0.0) * self.amp
        return out * self.gl, out * self.gr

    def dead(self, end):
        return (end - self.t0) > self.dmax * 7.0


class _BellGen:
    """Tolls one bell/gong spec slowly: schedules strikes and sums living rings."""

    def __init__(self, sr, rng, spec):
        self.sr, self.rng, self.spec = sr, rng, spec
        self.modes = spec["modes"]
        self.bells = []
        self.next = float(spec.get("first", 1.0))

    def step(self, tarr, frames, *_):
        end = float(tarr[-1])
        sp = self.spec
        while self.next < end:
            f0 = sp["f0"] * (1.0 + (self.rng.random() * 2 - 1) * sp.get("jitter", 0.0))
            self.bells.append(_Bell(
                self.sr, f0, self.modes, self.next,
                amp=self.rng.uniform(*sp["amp"]),
                pan=(self.rng.random() * 2 - 1) * sp.get("pan", 0.3),
                decay_scale=sp.get("decay_scale", 1.0)))
            self.next += self.rng.uniform(*sp["interval"])
        L, R = np.zeros(frames), np.zeros(frames)
        alive = []
        for b in self.bells:
            l, r = b.render(tarr)
            L += l
            R += r
            if not b.dead(end):
                alive.append(b)
        self.bells = alive
        return np.column_stack([L, R])


class _SungBowl:
    """A rubbed (sung) singing bowl: a sustained drone of close, beating partials
    that swells slowly -- the continuous 'singing' rather than a single strike."""

    def __init__(self, sr, rng, spec):
        self.sr = sr
        self.f0 = spec["f0"]
        self.partials = spec["partials"]              # (ratio, amp)
        self.norm = sum(a for _, a in self.partials) + 1e-9

    def step(self, tarr, frames, *_):
        swell = 0.62 + 0.38 * np.sin(TWO_PI * 0.07 * tarr)
        out = np.zeros(frames)
        for r, a in self.partials:
            out += a * np.sin(TWO_PI * self.f0 * r * tarr)
        mono = out / self.norm * swell
        return np.column_stack([mono, mono])


# --- instrument library ----------------------------------------------------
# modes: (ratio, amp, decay_s, bloom_s).  f0 is the prime/fundamental (Hz).
_SPECS = [
    ("med_bell", "Meditation Bell", 71, 0.861, dict(
        f0=523.0, interval=(8.0, 14.0), amp=(0.7, 1.0), pan=0.25, decay_scale=1.0,
        modes=[(1.0, 1.0, 8.0, 0), (1.006, 0.6, 8.0, 0), (2.0, 0.5, 5.0, 0),
               (2.7, 0.2, 2.2, 0), (3.9, 0.12, 1.2, 0), (5.4, 0.07, 0.7, 0)]),
     "A clear Zen meditation bell (rin), ringing slowly down to silence."),
    ("temple_bell", "Temple Bell", 72, 1.049, dict(
        f0=98.0, interval=(15.0, 26.0), amp=(0.75, 1.0), pan=0.2, decay_scale=1.35,
        modes=[(0.5, 0.7, 12, 0), (1.0, 1.0, 9, 0), (1.003, 0.8, 9, 0),
               (1.19, 0.6, 8, 0), (1.5, 0.4, 4, 0), (2.0, 0.5, 2.5, 0),
               (2.74, 0.25, 1.5, 0), (4.0, 0.16, 0.8, 0)]),
     "A deep Japanese temple bell (bonsho): a long, low boom that lingers."),
    ("church_bell", "Church Bell", 73, 1.025, dict(
        f0=233.0, interval=(5.0, 9.0), amp=(0.7, 1.0), pan=0.3, decay_scale=1.0,
        modes=[(0.5, 0.6, 7, 0), (1.0, 1.0, 5, 0), (1.2, 0.7, 4.5, 0),
               (1.5, 0.5, 2.5, 0), (2.0, 0.55, 1.6, 0), (2.5, 0.25, 1.0, 0),
               (3.0, 0.3, 0.9, 0), (4.0, 0.2, 0.6, 0)]),
     "A cast church bell with the full Hemony partials and a plaintive tierce."),
    ("hand_bell", "Hand Bell", 74, 1.109, dict(
        f0=660.0, interval=(3.0, 6.0), amp=(0.6, 0.9), pan=0.4, decay_scale=1.0,
        modes=[(0.5, 0.4, 2, 0), (1.0, 1.0, 2.2, 0), (1.2, 0.6, 1.8, 0),
               (1.5, 0.4, 1.0, 0), (2.0, 0.5, 0.8, 0), (3.0, 0.25, 0.4, 0)]),
     "A small, bright hand bell, rung gently and often."),
    ("tibetan_bowl", "Tibetan Singing Bowl", 75, 0.837, dict(
        f0=196.0, interval=(10.0, 18.0), amp=(0.7, 1.0), pan=0.25, decay_scale=1.2,
        modes=[(1.0, 1.0, 9, 0), (1.004, 0.9, 9, 0), (2.78, 0.5, 6, 0),
               (2.79, 0.45, 6, 0), (5.4, 0.25, 3, 0), (5.42, 0.22, 3, 0),
               (8.9, 0.12, 1.5, 0)]),
     "A struck Tibetan bowl: inharmonic modes that beat slowly as they fade."),
    ("crystal_bowl", "Crystal Bowl", 76, 0.866, dict(
        f0=330.0, interval=(14.0, 22.0), amp=(0.7, 1.0), pan=0.2, decay_scale=1.0,
        modes=[(1.0, 1.0, 14, 0), (1.002, 0.8, 14, 0), (1.25, 0.12, 10, 0),
               (2.5, 0.16, 8, 0)]),
     "A crystal bowl: an almost pure, glassy tone that rings for a long time."),
    ("gong", "Gong (Tam-tam)", 77, 1.252, dict(
        f0=75.0, interval=(13.0, 22.0), amp=(0.7, 1.0), pan=0.25, decay_scale=1.4,
        modes=[(1.0, 0.8, 16, 0), (1.5, 0.5, 14, 0), (2.1, 0.5, 12, 1.6),
               (2.7, 0.45, 12, 2.0), (3.3, 0.4, 10, 2.6), (4.2, 0.4, 9, 3.2),
               (5.1, 0.32, 8, 3.8), (6.3, 0.28, 7, 4.2), (7.7, 0.22, 6, 4.6)]),
     "A great tam-tam gong: dense partials that bloom and shimmer, then fade."),
    ("nipple_gong", "Nipple Gong", 78, 0.981, dict(
        f0=165.0, interval=(8.0, 16.0), amp=(0.7, 1.0), pan=0.25, decay_scale=1.2,
        modes=[(1.0, 1.0, 10, 0), (1.5, 0.4, 7, 0), (2.0, 0.4, 6, 1.0),
               (2.6, 0.3, 5, 1.5), (4.0, 0.2, 3, 2.0)]),
     "A pitched nipple gong: a clear tone with a soft blooming shimmer."),
    ("triangle", "Triangle", 79, 0.891, dict(
        f0=2100.0, interval=(4.0, 8.0), amp=(0.5, 0.8), pan=0.6, decay_scale=1.0,
        modes=[(1.0, 0.4, 5, 0), (2.13, 0.6, 5, 0), (3.27, 0.7, 5, 0),
               (4.5, 0.6, 4, 0), (5.8, 0.5, 4, 0), (7.2, 0.4, 3, 0),
               (8.9, 0.3, 3, 0)]),
     "A triangle: a bright, high shimmer of overtones that lingers and sparkles."),
    ("tingsha", "Tingsha (Cymbals)", 80, 1.003, dict(
        f0=1180.0, interval=(5.0, 9.0), amp=(0.5, 0.85), pan=0.5, decay_scale=1.0,
        modes=[(1.0, 1.0, 3.5, 0), (1.01, 0.9, 3.5, 0), (2.7, 0.4, 2, 0),
               (2.73, 0.38, 2, 0), (5.3, 0.2, 1, 0)]),
     "Tibetan tingsha cymbals: a bright, ringing ping that beats as it fades."),
    ("tubular_bell", "Tubular Bell", 81, 0.893, dict(
        f0=110.0, interval=(6.0, 11.0), amp=(0.7, 1.0), pan=0.35, decay_scale=1.0,
        modes=[(2.0, 1.0, 6, 0), (3.0, 0.7, 5, 0), (4.0, 0.5, 4, 0),
               (5.0, 0.4, 3, 0), (6.0, 0.3, 2, 0), (9.2, 0.15, 1, 0)]),
     "An orchestral tubular bell: bright metallic partials over a struck pitch."),
]

_SUNG = ("sung_bowl", "Singing Bowl (Sung)", 82, 0.795, dict(
    f0=210.0, partials=[(1.0, 1.0), (1.004, 0.9), (2.01, 0.4), (2.0, 0.36),
                        (2.8, 0.2), (4.1, 0.1)]),
    "A rubbed singing bowl: a continuous, gently swelling beating drone.")


def _register():
    for key, name, seed, gain, spec, desc in _SPECS:
        register_generator(key, (lambda s, r, sp=spec: _BellGen(s, r, sp)), seed)
        register(VoiceConfig(name, GROUP_BELLS, kind="texture", texture=key,
                             env="volume", floor=1.0, gain=gain, description=desc))
    key, name, seed, gain, spec, desc = _SUNG
    register_generator(key, (lambda s, r, sp=spec: _SungBowl(s, r, sp)), seed)
    register(VoiceConfig(name, GROUP_BELLS, kind="texture", texture=key,
                         env="volume", floor=1.0, gain=gain, description=desc))


_register()
