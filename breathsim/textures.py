"""Procedural ambience textures (``kind="texture"``).

Event-driven nature/relaxation beds that the simple filtered-noise NoiseTrack
can't make: a crackling **Campfire**, a struck **Singing Bowl**, scattered
**Wind Chimes**, and a field of **Night Crickets**. Each is a small stateful
generator producing click-free stereo blocks; everything is **seeded
deterministically** so the level (and the calibrated gain) is reproducible.

Registered into the voices registry on import (see the bottom of voices.py).
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp
from .voices import GROUP_NATURE, VoiceConfig, register

TWO_PI = dsp.TWO_PI


class _Struck:
    """A struck resonator: decaying inharmonic partials with a soft 2 ms attack.

    Uses absolute time for the sinusoids (phase stays continuous across blocks
    with no accumulator) and an exponential decay per partial from the strike."""

    def __init__(self, sr, f0, partials, t0, amp, pan, decay_scale=1.0):
        self.f = [f0 * r for r, _, _ in partials]
        self.pa = [a for _, a, _ in partials]
        self.pd = [d * decay_scale for _, _, d in partials]
        self.t0 = t0
        self.amp = amp / (sum(self.pa) + 1e-9)
        th = (pan + 1.0) * (math.pi / 4.0)
        self.gl, self.gr = math.cos(th), math.sin(th)
        self.dmax = max(self.pd)

    def render(self, tarr):
        ts = tarr - self.t0
        atk = np.clip(ts / 0.002, 0.0, 1.0)             # avoid an onset click
        out = np.zeros(len(tarr))
        for f, a, d in zip(self.f, self.pa, self.pd):
            env = atk * np.exp(-np.maximum(ts, 0.0) / d)
            out += a * np.sin(TWO_PI * f * tarr) * env
        out = np.where(ts >= 0.0, out, 0.0) * self.amp
        return out * self.gl, out * self.gr

    def dead(self, t):
        return (t - self.t0) > self.dmax * 7.0


class _Campfire:
    """A low flame roar + hiss with random crackles and the odd louder snap."""

    def __init__(self, sr, rng):
        self.sr, self.rng = sr, rng
        self.bed = dsp.Noise("brown", sr, seed=101)
        self.bedLP = dsp.OnePoleLP()
        self.roar = dsp.Noise("brown", sr, seed=102)
        self.roarLP = dsp.OnePoleLP()
        self.crk = dsp.Noise("white", sr, seed=103)
        self.cr = []
        self.next = 0.3

    def step(self, tarr, frames):
        bed = self.bedLP.process(self.bed.generate(frames), 1700.0, self.sr) * 0.6
        roar = self.roarLP.process(self.roar.generate(frames), 360.0, self.sr) * 0.9
        noise = self.crk.generate(frames)
        body = bed + roar
        L, R = body.copy(), body.copy()
        end = float(tarr[-1])
        while self.next < end:
            big = self.rng.random() < 0.05
            self.cr.append(dict(
                t0=self.next, f=1400.0 + 2600.0 * self.rng.random(),
                pan=(self.rng.random() * 2 - 1) * 0.6,
                amp=(0.30 + 0.12 * self.rng.random()) if big
                    else (0.05 + 0.13 * self.rng.random()),
                dec=(0.06 if big else 0.018) + 0.03 * self.rng.random()))
            self.next += float(self.rng.exponential(1.0 / 9.0))
        alive = []
        for h in self.cr:
            ts = tarr - h["t0"]
            env = np.where(ts >= 0.0, np.exp(-np.maximum(ts, 0.0) / h["dec"]), 0.0)
            tone = 0.5 * np.sin(TWO_PI * h["f"] * tarr)
            burst = (tone + 0.5 * np.clip(noise, -2.0, 2.0)) * env * h["amp"]
            th = (h["pan"] + 1.0) * (math.pi / 4.0)
            L += burst * math.cos(th)
            R += burst * math.sin(th)
            if (end - h["t0"]) < h["dec"] * 7.0:
                alive.append(h)
        self.cr = alive
        return np.column_stack([L, R])


class _Crickets:
    """A few detuned, panned crickets: a high tone, a fast trill, a chirp gate."""

    def __init__(self, sr, rng):
        self.sr = sr
        self.cr = [dict(f=4200.0 + 1100.0 * rng.random(),
                        am=26.0 + 16.0 * rng.random(),
                        song=0.6 + 0.6 * rng.random(),
                        ph=rng.random() * TWO_PI,
                        pan=(rng.random() * 2 - 1) * 0.7,
                        amp=0.16 + 0.08 * rng.random()) for _ in range(4)]
        self.bed = dsp.Noise("brown", sr, seed=151)
        self.bedLP = dsp.OnePoleLP()

    def step(self, tarr, frames):
        night = self.bedLP.process(self.bed.generate(frames), 480.0, self.sr) * 0.18
        L, R = night.copy(), night.copy()
        for c in self.cr:
            tone = np.sin(TWO_PI * c["f"] * tarr)
            trill = 0.5 + 0.5 * np.sin(TWO_PI * c["am"] * tarr)
            song = np.sin(TWO_PI * c["song"] * tarr + c["ph"])
            gate = np.clip((song - 0.35) / 0.25, 0.0, 1.0)     # chirp bursts
            sig = tone * trill * gate * c["amp"]
            th = (c["pan"] + 1.0) * (math.pi / 4.0)
            L += sig * math.cos(th)
            R += sig * math.sin(th)
        return np.column_stack([L, R])


class _Strikes:
    """Shared scheduler for struck voices (bowl periodic, chimes in gusts)."""

    def __init__(self, sr, rng):
        self.sr, self.rng = sr, rng
        self.hits = []

    def _mix(self, tarr, frames, end):
        L, R = np.zeros(frames), np.zeros(frames)
        alive = []
        for hk in self.hits:
            l, r = hk.render(tarr)
            L += l
            R += r
            if not hk.dead(end):
                alive.append(hk)
        self.hits = alive
        return np.column_stack([L, R])


class _Bowl(_Strikes):
    PARTIALS = [(1.0, 1.0, 5.5), (1.005, 0.5, 5.5), (2.0, 0.5, 4.0),
                (2.7, 0.35, 3.0), (4.8, 0.18, 2.0)]    # 1.005 = slow beating

    def __init__(self, sr, rng):
        super().__init__(sr, rng)
        self.next = 1.0

    def step(self, tarr, frames):
        end = float(tarr[-1])
        while self.next < end:
            f0 = float(self.rng.choice([196.0, 220.0, 261.6, 293.7]))
            self.hits.append(_Struck(self.sr, f0, self.PARTIALS, self.next,
                                     amp=0.7 + 0.2 * self.rng.random(),
                                     pan=(self.rng.random() * 2 - 1) * 0.3))
            self.next += 7.0 + 5.0 * self.rng.random()
        return self._mix(tarr, frames, end)


class _Chimes(_Strikes):
    PARTIALS = [(1.0, 1.0, 2.6), (2.0, 0.4, 1.8), (3.8, 0.2, 1.0)]
    NOTES = [1.0, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2.0, 9 / 4]   # pentatonic-ish
    BASE = 523.25                                           # ~C5

    def __init__(self, sr, rng):
        super().__init__(sr, rng)
        self.next = 0.8

    def step(self, tarr, frames):
        end = float(tarr[-1])
        while self.next < end:
            t = self.next
            for _ in range(2 + int(self.rng.random() * 4)):     # a gust of 2-5
                ratio = self.NOTES[int(self.rng.random() * len(self.NOTES))]
                self.hits.append(_Struck(
                    self.sr, self.BASE * ratio, self.PARTIALS, t,
                    amp=0.35 + 0.25 * self.rng.random(),
                    pan=(self.rng.random() * 2 - 1) * 0.8,
                    decay_scale=0.8 + 0.5 * self.rng.random()))
                t += 0.08 + 0.22 * self.rng.random()
            self.next += 3.0 + 5.0 * self.rng.random()
        return self._mix(tarr, frames, end)


_GENS = {"campfire": _Campfire, "bowl": _Bowl, "chimes": _Chimes,
         "crickets": _Crickets}
_SEED = {"campfire": 41, "bowl": 42, "chimes": 43, "crickets": 44}


class TextureTrack:
    def __init__(self, cfg: VoiceConfig, sr: int):
        self.cfg = cfg
        self.sr = sr
        rng = np.random.default_rng(_SEED.get(cfg.texture, 11))
        self.gen = _GENS[cfg.texture](sr, rng)
        self._t = 0.0

    def render(self, frames, s0, s1):
        tarr = self._t + np.arange(frames) / self.sr
        out = self.gen.step(tarr, frames)
        self._t += frames / self.sr
        f = self.cfg.floor
        a0 = f + (1.0 - f) * getattr(s0, "volume", 0.5)
        a1 = f + (1.0 - f) * getattr(s1, "volume", 0.5)
        amp = np.linspace(a0, a1, frames)
        return out * amp[:, None] * self.cfg.gain


def _t(name, texture, gain, desc):
    register(VoiceConfig(name, GROUP_NATURE, kind="texture", texture=texture,
                         env="volume", floor=1.0, gain=gain, description=desc))


# Gains calibrated to ~0.75 peak at unit level over a 150 s deterministic render
# (TARGET/unit-peak; see SESSION_LOG). The two broadband-noise beds get a little
# extra headroom for long sessions, where the noise can wander higher.
_t("Campfire", "campfire", 0.16,
   "A soft fire: a low roar with gentle crackles and the odd quiet snap.")
_t("Singing Bowl", "bowl", 1.10,
   "A metal bowl struck softly now and then, ringing slowly down.")
_t("Wind Chimes", "chimes", 0.55,
   "Scattered chimes drifting in on the breeze, in a gentle pentatonic.")
_t("Night Crickets", "crickets", 0.72,
   "A summer night: a field of crickets chirping over a low hush.")
