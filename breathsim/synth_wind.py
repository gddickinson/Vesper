"""Winds & organs: sustained tonal sources -- organs, reed drones, flutes, horns.

Two shapes, both pure additive (absolute-time sines, phase-continuous across
blocks):

* :class:`_Organ` -- a continuous drone: a stack of harmonics with a chosen
  spectrum, a gentle tremulant (slow amplitude + pitch wobble), slight detuning
  for beating, and a touch of breath 'chiff' noise. Used for the pipe organ, the
  harmonium / shruti reed drone (lovely under chants), a soft reed organ and a
  breathy wooden flute.
* :class:`_Horn` -- a periodic blast: every so often a sustained chord swells in
  (slow attack), holds, and releases. Used for a wistful train whistle (a chord of
  pitches), a deep fog horn and a two-tone ship horn.

Each is a ``kind="texture"`` voice (plugged in via ``texture_registry.register_generator``);
registered as the **Winds & Organs** group. Mirrors `synth_bell.py`.
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp
from .texture_registry import register_generator
from .voices import GROUP_WIND, VoiceConfig, register

TWO_PI = dsp.TWO_PI


class _Organ:
    """A continuous additive drone with a tremulant, beating and breath chiff."""

    def __init__(self, sr, rng, spec):
        self.sr = sr
        self.f0 = spec["f0"]
        self.partials = spec["partials"]              # (ratio, amp)
        self.norm = sum(a for _, a in self.partials) + 1e-9
        self.trem = spec.get("trem", (0.0, 0.0))      # (rate Hz, depth 0..1)
        self.detune = spec.get("detune", 0.0)         # cents-ish beat on a 2nd layer
        self.chiff = spec.get("chiff", 0.0)
        self.nz = dsp.Noise("pink", sr, seed=int(rng.integers(1, 2 ** 31)))
        self.bp = dsp.Biquad(*dsp.bandpass(sr, spec.get("chiff_fc", 2000.0), 0.7))

    def step(self, tarr, frames, *_):
        rate, depth = self.trem
        trem = 1.0 - depth + depth * (0.5 + 0.5 * np.sin(TWO_PI * rate * tarr)) \
            if rate > 0 else 1.0
        swell = 0.78 + 0.22 * np.sin(TWO_PI * 0.05 * tarr)
        out = np.zeros(frames)
        for ratio, a in self.partials:
            out += a * np.sin(TWO_PI * self.f0 * ratio * tarr)
            if self.detune:
                out += a * 0.7 * np.sin(TWO_PI * self.f0 * ratio
                                        * (1.0 + self.detune) * tarr)
        mono = out / (self.norm * (1.7 if self.detune else 1.0)) * trem * swell
        if self.chiff:
            mono = mono + self.bp.process(self.nz.generate(frames)) * self.chiff
        return np.column_stack([mono, mono])


class _Blast:
    """One horn blast: a chord with a slow raised-cosine attack, hold and release."""

    def __init__(self, sr, f0, t0, amp, pan, ratios, atk, hold, rel, detune):
        self.t0 = t0
        self.f = []
        for r in ratios:
            self.f.append(f0 * r)
            if detune:
                self.f.append(f0 * r * (1.0 + detune))
        self.amp = amp / (len(self.f) + 1e-9)
        self.atk, self.hold, self.rel = atk, hold, rel
        self.life = atk + hold + rel
        th = (pan + 1.0) * (math.pi / 4.0)
        self.gl, self.gr = math.cos(th), math.sin(th)

    def render(self, tarr):
        ts = tarr - self.t0
        a = np.clip(ts / self.atk, 0.0, 1.0)
        env = 0.5 - 0.5 * np.cos(np.pi * a)                    # slow swell in
        rs = np.clip((ts - self.atk - self.hold) / self.rel, 0.0, 1.0)
        env *= 0.5 + 0.5 * np.cos(np.pi * rs)                  # slow release
        env = np.where((ts >= 0.0) & (ts <= self.life), env, 0.0)
        out = np.zeros(len(tarr))
        for f in self.f:
            out += np.sin(TWO_PI * f * tarr)
        out = out * env * self.amp
        return out * self.gl, out * self.gr

    def dead(self, end):
        return (end - self.t0) > self.life


class _Horn:
    """Sounds a horn/whistle blast every so often (a foghorn calling, a train
    whistle in the distance)."""

    def __init__(self, sr, rng, spec):
        self.sr, self.rng, self.spec = sr, rng, spec
        self.blasts = []
        self.next = float(spec.get("first", 2.0))

    def step(self, tarr, frames, *_):
        end = float(tarr[-1])
        sp = self.spec
        while self.next < end:
            self.blasts.append(_Blast(
                self.sr, sp["f0"], self.next, self.rng.uniform(*sp["amp"]),
                (self.rng.random() * 2 - 1) * sp.get("pan", 0.2), sp["ratios"],
                sp.get("atk", 0.3), self.rng.uniform(*sp["hold"]),
                sp.get("rel", 1.0), sp.get("detune", 0.0)))
            self.next += self.rng.uniform(*sp["interval"])
        L, R = np.zeros(frames), np.zeros(frames)
        alive = []
        for b in self.blasts:
            l, r = b.render(tarr)
            L += l
            R += r
            if not b.dead(end):
                alive.append(b)
        self.blasts = alive
        return np.column_stack([L, R])


# --- library ---------------------------------------------------------------
# Organs/drones: (key, name, seed, gain, cls, spec, desc)
_DRONES = [
    ("pipe_organ", "Pipe Organ", 61, 1.086, _Organ, dict(
        f0=130.81, partials=[(1, 1.0), (2, 0.7), (3, 0.5), (4, 0.4), (5, 0.28),
                             (6, 0.2), (8, 0.12)], trem=(5.0, 0.12), detune=0.001,
        chiff=0.0),
     "A full, churchy pipe-organ drone with a gentle tremulant."),
    ("harmonium", "Harmonium (Shruti)", 62, 0.979, _Organ, dict(
        f0=146.83, partials=[(1, 1.0), (2, 0.8), (3, 0.6), (4, 0.45), (5, 0.4),
                             (6, 0.3), (7, 0.2)], trem=(5.5, 0.1), detune=0.006,
        chiff=0.05, chiff_fc=2600.0),
     "A buzzy reed harmonium / shruti-box drone - a warm bed under chants."),
    ("reed_organ", "Reed Organ", 63, 0.998, _Organ, dict(
        f0=196.0, partials=[(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.18), (5, 0.1)],
        trem=(4.5, 0.14), detune=0.003, chiff=0.03),
     "A soft, mellow reed organ, breathing slowly."),
    ("wood_flute", "Wooden Flute", 64, 0.658, _Organ, dict(
        f0=329.63, partials=[(1, 1.0), (2, 0.18), (3, 0.08)], trem=(5.5, 0.08),
        detune=0.0, chiff=0.16, chiff_fc=3200.0),
     "A soft, breathy wooden-flute drone with airy chiff."),
]

# Horns/whistles: periodic blasts.
_HORNS = [
    ("train_whistle", "Train Whistle", 65, 1.274, _Horn, dict(
        f0=440.0, ratios=[1.0, 1.19, 1.5, 1.78], interval=(9.0, 16.0),
        amp=(0.6, 0.9), hold=(1.2, 2.2), atk=0.25, rel=1.4, detune=0.004,
        pan=0.3),
     "A wistful train whistle in the distance - a soft minor chord, fading."),
    ("fog_horn", "Fog Horn", 66, 1.165, _Horn, dict(
        f0=70.0, ratios=[1.0, 2.0], interval=(12.0, 20.0), amp=(0.7, 1.0),
        hold=(2.0, 3.2), atk=0.4, rel=1.6, detune=0.003, pan=0.15),
     "A deep fog horn calling slowly across the water."),
    ("ship_horn", "Ship Horn", 67, 1.023, _Horn, dict(
        f0=98.0, ratios=[1.0, 1.5], interval=(14.0, 24.0), amp=(0.7, 1.0),
        hold=(1.6, 2.8), atk=0.35, rel=1.5, detune=0.004, pan=0.2),
     "A low two-tone ship's horn sounding now and then in the harbour."),
]


def _register():
    for key, name, seed, gain, cls, spec, desc in (_DRONES + _HORNS):
        register_generator(key, (lambda s, r, c=cls, sp=spec: c(s, r, sp)), seed)
        register(VoiceConfig(name, GROUP_WIND, kind="texture", texture=key,
                             env="volume", floor=1.0, gain=gain, description=desc))


_register()
