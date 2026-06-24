"""Rhythmic & environmental effects: trains, ships, thunderstorms, a buoy bell.

Composite generators built from filtered coloured noise + scheduled events +
(for the buoy) a tiny struck resonator. Everything is deterministic (any Noise is
seeded from the passed rng; only block-wise noise is generated per frame) and
slow / low-contrast so it soothes rather than startles.

Each is a ``kind="texture"`` voice (plugged in via ``textures.register_generator``);
registered as the **Environmental FX** group. Mirrors `synth_drum.py`.
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp
from .textures import register_generator
from .voices import GROUP_FX, VoiceConfig, register

TWO_PI = dsp.TWO_PI


def _seed(rng):
    return int(rng.integers(1, 2 ** 31))


class _Train:
    """Wheel clickety-clack (paired clacks on a tempo) + a low rolling rumble +
    a rhythmic engine chuff. ``steam`` adds a breathier, slower chuff."""

    def __init__(self, sr, rng, spec):
        self.sr, self.spec = sr, spec
        self.beat = 60.0 / float(spec["bpm"])
        self.rumble = dsp.Noise("brown", sr, seed=_seed(rng))
        self.rlp = dsp.OnePoleLP()
        self.clk = dsp.Noise("white", sr, seed=_seed(rng))
        self.cbp = dsp.Biquad(*dsp.bandpass(sr, spec.get("clack_fc", 2200.0), 1.1))
        self.chuff = dsp.Noise("pink", sr, seed=_seed(rng))
        self.chbp = dsp.Biquad(*dsp.bandpass(sr, spec.get("chuff_fc", 600.0), 0.8))
        self.clacks = []                                  # (t0, amp) short bursts
        self.next = 0.3

    def step(self, tarr, frames, *_):
        end = float(tarr[-1])
        sp = self.spec
        while self.next < end:
            self.clacks.append((self.next, 1.0))          # da-
            self.clacks.append((self.next + sp.get("gap", 0.16), 0.8))   # -dum
            self.next += self.beat
        rum = self.rlp.process(self.rumble.generate(frames), 130.0, self.sr) * 2.6
        env = np.zeros(frames)
        chf = np.zeros(frames)
        for t0, a in self.clacks:
            ts = tarr - t0
            env += np.where(ts >= 0.0, np.exp(-np.maximum(ts, 0.0) / 0.012), 0.0) * a
        # engine chuff: one soft puff per beat (steam = stronger/slower)
        ph = (tarr / self.beat) % 1.0
        puff = np.clip(1.0 - ph / sp.get("chuff_w", 0.4), 0.0, 1.0) ** 2
        chf = self.chbp.process(self.chuff.generate(frames)) * puff * sp.get("chuff", 0.4)
        clack = self.cbp.process(self.clk.generate(frames) * env) * 0.9
        mono = rum * sp.get("rumble", 0.5) + clack + chf
        return np.column_stack([mono, mono * 0.96])


class _Ship:
    """Water lapping the hull (slow band-passed swells) + occasional wooden creaks
    + a rare low horn blast."""

    def __init__(self, sr, rng, spec):
        self.sr, self.rng, self.spec = sr, rng, spec
        self.wash = dsp.Noise("pink", sr, seed=_seed(rng))
        self.wbp = dsp.Biquad(*dsp.bandpass(sr, 480.0, 0.5))
        self.creaks = []
        self.next_creak = 3.0
        self.horns = []
        self.next_horn = 12.0

    def step(self, tarr, frames, *_):
        end = float(tarr[-1])
        wash = self.wbp.process(self.wash.generate(frames))
        swell = 0.5 + 0.5 * np.sin(TWO_PI * 0.13 * tarr + 0.5)        # gentle lap
        mono = wash * swell * 0.7
        while self.next_creak < end:                                  # wooden groan
            self.creaks.append((self.next_creak,
                                self.rng.uniform(70, 160),
                                self.rng.uniform(0.10, 0.22)))
            self.next_creak += self.rng.uniform(4.0, 9.0)
        alive = []
        for t0, f, a in self.creaks:
            ts = tarr - t0
            e = np.where(ts >= 0.0, np.exp(-np.maximum(ts, 0.0) / 0.6), 0.0)
            e *= np.clip(ts / 0.15, 0.0, 1.0)
            mono = mono + a * np.sin(TWO_PI * f * (1.0 - 0.04 * np.clip(ts, 0, 2)) * tarr) * e
            if (end - t0) < 4.0:
                alive.append((t0, f, a))
        self.creaks = alive
        while self.next_horn < end:                                  # rare low horn
            self.horns.append((self.next_horn, self.rng.uniform(0.5, 0.8)))
            self.next_horn += self.rng.uniform(20.0, 38.0)
        ah = []
        for t0, a in self.horns:
            ts = tarr - t0
            atk = np.clip(ts / 0.4, 0.0, 1.0)
            env = (0.5 - 0.5 * np.cos(np.pi * atk))
            rs = np.clip((ts - 2.4) / 1.4, 0.0, 1.0)
            env *= 0.5 + 0.5 * np.cos(np.pi * rs)
            env = np.where((ts >= 0.0) & (ts <= 3.8), env, 0.0)
            mono = mono + a * 0.5 * (np.sin(TWO_PI * 88.0 * tarr)
                                     + 0.6 * np.sin(TWO_PI * 132.0 * tarr)) * env
            if (end - t0) < 3.8:
                ah.append((t0, a))
        self.horns = ah
        return np.column_stack([mono, mono])


class _Storm:
    """A distant rumble bed + occasional thunder (a soft crack then a long rolling
    rumble), randomly spaced with long gaps. Gentle and far-off."""

    def __init__(self, sr, rng, spec):
        self.sr, self.rng = sr, rng
        self.bed = dsp.Noise("brown", sr, seed=_seed(rng))
        self.blp = dsp.OnePoleLP()
        self.crack = dsp.Noise("white", sr, seed=_seed(rng))
        self.chp = dsp.Biquad(*dsp.highpass(sr, 800.0, 0.7))
        self.rum = dsp.Noise("brown", sr, seed=_seed(rng))
        self.rlp = dsp.OnePoleLP()
        self.events = []
        self.next = 6.0

    def step(self, tarr, frames, *_):
        end = float(tarr[-1])
        bed = self.blp.process(self.bed.generate(frames), 90.0, self.sr) * 2.2
        wob = 0.5 + 0.5 * np.sin(TWO_PI * 0.05 * tarr)
        mono = bed * (0.25 + 0.25 * wob)
        while self.next < end:
            self.events.append((self.next, self.rng.uniform(0.6, 1.0),
                                self.rng.uniform(2.5, 5.0)))
            self.next += self.rng.uniform(12.0, 26.0)
        crackbuf = self.chp.process(self.crack.generate(frames))
        rumbuf = self.rlp.process(self.rum.generate(frames), 220.0, self.sr) * 2.4
        alive = []
        for t0, a, dur in self.events:
            ts = tarr - t0
            crk = np.where((ts >= 0.0) & (ts < 0.5),
                           np.exp(-np.maximum(ts, 0.0) / 0.08), 0.0)
            roll = np.where(ts >= 0.0, np.clip(ts / 0.6, 0.0, 1.0)
                            * np.exp(-np.maximum(ts, 0.0) / dur), 0.0)
            mono = mono + crackbuf * crk * a * 0.5 + rumbuf * roll * a
            if (end - t0) < dur * 4.0 + 1.0:
                alive.append((t0, a, dur))
        self.events = alive
        return np.column_stack([mono, mono * 0.95])


class _Buoy:
    """A bell buoy rocked by the swell: a struck two-mode bell tolling irregularly
    over a faint sea wash."""

    def __init__(self, sr, rng, spec):
        self.sr, self.rng = sr, rng
        self.f0 = spec.get("f0", 280.0)
        self.wash = dsp.Noise("pink", sr, seed=_seed(rng))
        self.wbp = dsp.Biquad(*dsp.bandpass(sr, 520.0, 0.5))
        self.rings = []
        self.next = 2.0

    def step(self, tarr, frames, *_):
        end = float(tarr[-1])
        wash = self.wbp.process(self.wash.generate(frames))
        swell = 0.5 + 0.5 * np.sin(TWO_PI * 0.11 * tarr)
        mono = wash * swell * 0.4
        while self.next < end:
            self.rings.append((self.next, self.rng.uniform(0.5, 1.0)))
            self.next += self.rng.uniform(2.5, 6.0)        # rocked irregularly
        alive = []
        for t0, a in self.rings:
            ts = tarr - t0
            atk = np.clip(ts / 0.003, 0.0, 1.0)
            tsp = np.maximum(ts, 0.0)
            body = (np.sin(TWO_PI * self.f0 * tarr) * np.exp(-tsp / 2.2)
                    + 0.5 * np.sin(TWO_PI * self.f0 * 2.76 * tarr) * np.exp(-tsp / 1.2))
            mono = mono + np.where(ts >= 0.0, body, 0.0) * atk * a * 0.5
            if (end - t0) < 16.0:
                alive.append((t0, a))
        self.rings = alive
        return np.column_stack([mono, mono * 0.97])


# --- library ---------------------------------------------------------------
_SPECS = [
    ("train_steam", "Train (Steam)", 41, 0.158, _Train, dict(
        bpm=150, gap=0.17, rumble=0.5, chuff=0.5, chuff_w=0.45, chuff_fc=520.0,
        clack_fc=2000.0),
     "A steam train rolling along: clickety-clack wheels, a chuffing engine and "
     "a low rumble."),
    ("train_diesel", "Train (Diesel)", 42, 0.122, _Train, dict(
        bpm=186, gap=0.14, rumble=0.6, chuff=0.25, chuff_w=0.7, chuff_fc=180.0,
        clack_fc=2400.0),
     "A diesel train: steady clacking rails over a deep engine rumble."),
    ("ship", "Ship / Harbour", 43, 0.434, _Ship, dict(),
     "On a boat: water laps the hull, timbers creak, and a horn sounds far off."),
    ("storm", "Thunderstorm", 44, 0.123, _Storm, dict(),
     "A distant thunderstorm: a low rumble bed with soft, far-off thunder rolls."),
    ("buoy", "Ocean Buoy Bell", 45, 0.577, _Buoy, dict(f0=280.0),
     "A bell buoy rocked by the swell, tolling slowly over a faint sea wash."),
]


def _register():
    for key, name, seed, gain, cls, spec, desc in _SPECS:
        register_generator(key, (lambda s, r, c=cls, sp=spec: c(s, r, sp)), seed)
        register(VoiceConfig(name, GROUP_FX, kind="texture", texture=key,
                             env="volume", floor=1.0, gain=gain, description=desc))


_register()
