"""Drums: a membrane/percussion synth + a small library, struck on a tempo.

Each hit is a struck drumhead: one or two **membrane modes** (decaying sines)
whose pitch glides gently *downward* as they fade (a real drumhead slackens as it
rings), plus a short **noise transient** for the attack (the stick/hand on the
skin). Hits land on a steady, slow tempo, so a drum is a calm rhythmic layer for
meditation, chant or ambience. Some drums alternate hit types over a short pattern
(a djembe's bass/slap, a slit drum's two tones).

Each drum is a ``kind="texture"`` voice (plugged in via
``textures.register_generator``); registered as the **Drums** group and offered in
the effects slot. Mirrors `synth_bell.py`.
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp
from .textures import register_generator
from .voices import GROUP_DRUMS, VoiceConfig, register

TWO_PI = dsp.TWO_PI


class _Hit:
    """One drum strike: membrane modes with a downward pitch glide (the tonal
    body) plus a short attack-transient envelope (filled with shared noise by the
    generator). Absolute-time sines keep the phase continuous across blocks."""

    def __init__(self, sr, f0, t0, amp, pan, modes, glide, tdecay, tamt):
        self.t0 = t0
        self.f0 = f0
        self.modes = modes                         # (ratio, amp, decay_s)
        self.glide = glide                         # end-freq multiplier (<1 = drop)
        self.tdecay = tdecay
        self.tamt = tamt
        self.amp = amp / (sum(a for _, a, _ in modes) + 1e-9)
        th = (pan + 1.0) * (math.pi / 4.0)
        self.gl, self.gr = math.cos(th), math.sin(th)
        self.life = max(d for _, _, d in modes)

    def body(self, tarr):
        ts = tarr - self.t0
        u = np.clip(ts / self.life, 0.0, 1.0)
        out = np.zeros(len(tarr))
        for ratio, a, dec in self.modes:
            f0 = self.f0 * ratio
            f1 = f0 * self.glide
            phase = TWO_PI * (f0 * ts + 0.5 * (f1 - f0) * ts * u)   # glide down
            out += a * np.sin(phase) * np.exp(-np.maximum(ts, 0.0) / dec)
        return np.where(ts >= 0.0, out, 0.0) * self.amp

    def transient(self, tarr):
        ts = tarr - self.t0
        return np.where(ts >= 0.0,
                        np.exp(-np.maximum(ts, 0.0) / self.tdecay), 0.0) * self.tamt

    def dead(self, end):
        return (end - self.t0) > self.life * 6.0 + 0.05


class _DrumGen:
    """Plays one drum spec at a steady tempo (with a touch of human swing/level
    variation), cycling through its hit pattern."""

    def __init__(self, sr, rng, spec):
        self.sr, self.rng, self.spec = sr, rng, spec
        self.beat = 60.0 / float(spec["bpm"])
        self.pattern = spec.get("pattern", [dict(fmul=1.0, amul=1.0, tmul=1.0)])
        self.noise = dsp.Noise("white", sr, seed=int(rng.integers(1, 2 ** 31)))
        self.bp = dsp.Biquad(*dsp.bandpass(sr, spec.get("tfc", 2200.0), 0.7))
        self.hits = []
        self.next = float(spec.get("first", 0.5))
        self.i = 0

    def step(self, tarr, frames, *_):
        end = float(tarr[-1])
        sp = self.spec
        while self.next < end:
            step = self.pattern[self.i % len(self.pattern)]
            self.i += 1
            amp = self.rng.uniform(*sp["amp"]) * step.get("amul", 1.0)
            self.hits.append(_Hit(
                self.sr, sp["f0"] * step.get("fmul", 1.0), self.next, amp,
                (self.rng.random() * 2 - 1) * sp.get("pan", 0.2),
                sp["modes"], sp.get("glide", 0.9), sp.get("tdecay", 0.012),
                sp.get("transient", 0.4) * step.get("tmul", 1.0)))
            swing = 1.0 + (self.rng.random() * 2 - 1) * sp.get("swing", 0.02)
            self.next += self.beat * swing
        L, R = np.zeros(frames), np.zeros(frames)
        tmono = np.zeros(frames)
        alive = []
        for h in self.hits:
            b = h.body(tarr)
            L += b * h.gl
            R += b * h.gr
            tmono += h.transient(tarr)
            if not h.dead(end):
                alive.append(h)
        self.hits = alive
        trans = self.bp.process(self.noise.generate(frames) * tmono)
        return np.column_stack([L + trans, R + trans])


# --- drum library ----------------------------------------------------------
# modes: (ratio, amp, decay_s). f0 = lowest membrane mode (Hz). glide < 1 drops.
_SPECS = [
    ("frame_drum", "Frame Drum", 51, 0.648, dict(
        f0=92.0, bpm=52, amp=(0.7, 1.0), pan=0.15, glide=0.88, tdecay=0.02,
        transient=0.5, tfc=1400.0,
        modes=[(1.0, 1.0, 0.5), (1.6, 0.3, 0.3), (2.4, 0.15, 0.18)]),
     "A soft, slow shamanic frame drum - a steady, grounding heartbeat-pulse."),
    ("taiko", "Taiko", 52, 0.66, dict(
        f0=68.0, bpm=44, amp=(0.75, 1.0), pan=0.12, glide=0.8, tdecay=0.03,
        transient=0.45, tfc=900.0,
        modes=[(1.0, 1.0, 0.9), (1.5, 0.4, 0.5), (2.1, 0.2, 0.3)]),
     "A deep taiko boom: a big, low drum struck slowly, fading with a soft thud."),
    ("tabla", "Tabla", 53, 0.6, dict(
        f0=210.0, bpm=82, amp=(0.6, 0.95), pan=0.25, glide=0.97, tdecay=0.008,
        transient=0.4, tfc=3200.0, swing=0.04,
        modes=[(1.0, 1.0, 0.7), (2.0, 0.5, 0.5), (3.0, 0.3, 0.35),
               (4.0, 0.18, 0.2)],
        pattern=[dict(fmul=1.0, amul=1.0), dict(fmul=1.0, amul=0.6),
                 dict(fmul=1.5, amul=0.8, tmul=1.3), dict(fmul=1.0, amul=0.5)]),
     "A pitched, ringing tabla, tapping out a soft cycle."),
    ("djembe", "Djembe", 54, 0.415, dict(
        f0=98.0, bpm=90, amp=(0.6, 0.95), pan=0.3, glide=0.85, tdecay=0.012,
        transient=0.5, tfc=2600.0, swing=0.03,
        modes=[(1.0, 1.0, 0.45), (1.7, 0.4, 0.28)],
        pattern=[dict(fmul=1.0, amul=1.0, tmul=0.6),          # bass
                 dict(fmul=2.4, amul=0.6, tmul=1.6),          # slap
                 dict(fmul=2.0, amul=0.5, tmul=1.4)]),        # tone
     "A hand drum alternating a round bass and a bright slap."),
    ("slit_drum", "Log Drum", 55, 0.695, dict(
        f0=290.0, bpm=66, amp=(0.6, 0.95), pan=0.35, glide=0.99, tdecay=0.006,
        transient=0.3, tfc=2000.0,
        modes=[(1.0, 1.0, 0.8), (2.7, 0.3, 0.4), (5.2, 0.12, 0.2)],
        pattern=[dict(fmul=1.0), dict(fmul=1.335)]),          # two wooden tones
     "A wooden slit (log) drum: two warm, hollow tones trading slowly."),
    ("woodblock", "Woodblock", 56, 0.714, dict(
        f0=900.0, bpm=88, amp=(0.5, 0.85), pan=0.3, glide=0.98, tdecay=0.004,
        transient=0.35, tfc=3600.0,
        modes=[(1.0, 1.0, 0.12), (2.6, 0.4, 0.07)]),
     "A high, dry woodblock: a clean, light click on a gentle pulse."),
    ("bodhran", "Bodhran", 57, 0.664, dict(
        f0=120.0, bpm=72, amp=(0.6, 0.95), pan=0.2, glide=0.8, tdecay=0.016,
        transient=0.4, tfc=1700.0, swing=0.03,
        modes=[(1.0, 1.0, 0.4), (1.8, 0.35, 0.22)],
        pattern=[dict(amul=1.0), dict(amul=0.6), dict(amul=0.8),
                 dict(amul=0.55)]),
     "An Irish bodhran frame drum with a soft, bending low voice."),
]


def _register():
    for key, name, seed, gain, spec, desc in _SPECS:
        register_generator(key, (lambda s, r, sp=spec: _DrumGen(s, r, sp)), seed)
        register(VoiceConfig(name, GROUP_DRUMS, kind="texture", texture=key,
                             env="volume", floor=1.0, gain=gain, description=desc))


_register()
