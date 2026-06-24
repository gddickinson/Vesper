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

# --- data sonification: the real solar system ------------------------------
# Kepler's "harmony of the spheres" heard literally. Real planetary orbital
# periods (years, Mercury..Neptune); a planet's orbital *frequency* is ~ 1/period.
# We take each planet's frequency as a ratio to the slowest (Neptune), fold it
# into one octave, and snap it to the nearest just-intonation degree so the chord
# is consonant and restful -- a scale that genuinely encodes the solar system.
_ORBITAL_YEARS = [0.2408, 0.6152, 1.0, 1.881, 11.862, 29.457, 84.02, 164.8]
_JI = [1 / 1, 9 / 8, 6 / 5, 5 / 4, 4 / 3, 3 / 2, 5 / 3, 9 / 5, 15 / 8, 2 / 1]


def _planet_scale():
    slow = 1.0 / max(_ORBITAL_YEARS)            # Neptune: slowest = lowest tone
    degrees = set()
    for yr in _ORBITAL_YEARS:
        r = (1.0 / yr) / slow
        while r >= 2.0:
            r /= 2.0
        while r < 1.0:
            r *= 2.0
        degrees.add(round(min(_JI, key=lambda j: abs(math.log2(j / r))), 6))
    base = sorted(degrees)
    return sorted(set(base + [d * 2.0 for d in base if d < 2.0]))   # +1 octave


_PLANET_SCALE = _planet_scale()                 # [1, 5/4, 4/3, 9/5, 2, ...]


class _Pad:
    """A slow, soft sustained note: a small additive partial stack under a
    raised-cosine attack / hold / release, with gentle vibrato and a stereo pan."""

    def __init__(self, sr, f, t0, atk, hold, rel, amp, pan, partials, vib,
                 f_end=None):
        self.f0, self.f1, self.t0 = f, (f if f_end is None else f_end), t0
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
        # Integrate frequency -> phase so an optional linear pitch glide (f0->f1
        # over the note, e.g. a black-hole ringdown) stays perfectly click-free.
        u = np.clip(ts / self.life, 0.0, 1.0)
        phase = TWO_PI * (self.f0 * ts + 0.5 * (self.f1 - self.f0) * ts * u)
        tone = np.zeros(len(tarr))
        for ratio, pa in self.partials:
            tone += pa * np.sin(ratio * phase + vib)
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
        self.pulse = p.get("pulse")          # (rate_hz, depth) slow pulsar beat
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
        self.breath = p.get("breath", 0.0)   # 0..1: how much it breathes with you
        self.blp, self.brp = dsp.OnePoleLP(), dsp.OnePoleLP()
        self.wants_state = True              # TextureTrack feeds us the breath state

    def _spawn(self, t):
        p = self.p
        f = self.root * float(self.rng.choice(p["scale"])) * \
            float(self.rng.choice(p["octaves"]))
        gl = p.get("glide")
        f_end = f * self.rng.uniform(*gl) if gl else None
        self.pads.append(_Pad(
            self.sr, f, t,
            self.rng.uniform(*p["attack"]), self.rng.uniform(*p["hold"]),
            self.rng.uniform(*p["release"]), self.rng.uniform(*p["amp"]),
            (self.rng.random() * 2 - 1) * p["pan"], p["partials"], p["vib"],
            f_end))

    def step(self, tarr, frames, s0=None, s1=None):
        end = float(tarr[-1])
        bd = 0.5                                       # breath drive: lung volume
        if s0 is not None:
            bd = 0.5 * (getattr(s0, "volume", 0.5) + getattr(s1, "volume", 0.5))
        br = self.breath
        if tarr[0] >= self.root_next:                 # slow consonant root drift
            self.root = self.base * float(self.rng.choice(self.p["roots"]))
            self.root_next += self.rng.uniform(*self.p["root_period_range"])
        while self.next < end:
            self._spawn(self.next)
            gap = self.rng.uniform(*self.p["interval"])
            if br:
                gap *= 1.0 - 0.4 * br * bd            # gently denser as lungs fill
            self.next += gap

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
            if self.pulse:                            # slow pulsar beat
                rate, depth = self.pulse
                beat = np.clip(np.sin(TWO_PI * rate * tarr), 0.0, 1.0) ** 2
                swell = swell * ((1.0 - depth) + depth * beat)
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

        if br:                                         # breathe with the listener
            v0 = getattr(s0, "volume", 0.5) if s0 is not None else 0.5
            v1 = getattr(s1, "volume", 0.5) if s1 is not None else 0.5
            lvl = 1.0 + br * 0.3 * (np.linspace(v0, v1, frames) - 0.5)  # gentle swell
            L = L * lvl
            R = R * lvl
            fc = 6500.0 - br * 4800.0 * (1.0 - bd)     # ...and opens on the inhale
            L = self.blp.process(L, fc, self.sr)
            R = self.brp.process(R, fc, self.sr)

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
    vib=(0.18, 0.6), drone=0.16, reverb=0.55, damp=2800.0, breath=0.5)

_CHOIR = dict(
    base=146.83, scale=_PENTA, roots=[1 / 1, 3 / 2, 5 / 4, 4 / 3],
    octaves=[1.0, 2.0, 2.0], root_period=36.0, root_period_range=(26.0, 50.0),
    interval=(2.2, 4.5), attack=(3.0, 6.0), hold=(2.5, 7.0), release=(5.0, 9.0),
    amp=(0.22, 0.42), pan=0.8,
    partials=[(1.0, 1.0), (2.0, 0.6), (3.0, 0.5), (4.0, 0.32), (5.0, 0.22),
              (6.0, 0.12)],
    vib=(5.2, 0.5), formant=[(700.0, 3.0, 1.0), (1100.0, 4.0, 0.7),
                             (2600.0, 6.0, 0.3)],
    drone=0.10, reverb=0.6, damp=3200.0, breath=0.45)

_DEEP = dict(
    base=55.0, scale=_MINOR, roots=[1 / 1, 6 / 5, 4 / 3, 3 / 2],
    octaves=[1.0, 1.0, 2.0], root_period=55.0, root_period_range=(40.0, 80.0),
    interval=(7.0, 14.0), attack=(6.0, 10.0), hold=(6.0, 12.0),
    release=(8.0, 14.0), amp=(0.30, 0.55), pan=0.6,
    partials=[(0.5, 0.6), (1.0, 1.0), (2.0, 0.25), (3.0, 0.08)],
    vib=(0.12, 0.4), shimmer=(3800.0, 0.06), drone=0.22, reverb=0.7, damp=1900.0, breath=0.35)

_SOLAR = dict(           # bright, airy, streaming - the solar wind
    base=164.81, scale=_PENTA, roots=_ROOTS, octaves=[1.0, 2.0, 2.0, 4.0],
    root_period=34.0, root_period_range=(24.0, 48.0), interval=(2.5, 5.0),
    attack=(3.0, 6.0), hold=(2.0, 6.0), release=(5.0, 9.0), amp=(0.18, 0.36),
    pan=0.9, partials=[(1.0, 1.0), (2.0, 0.4), (3.0, 0.18), (5.0, 0.06)],
    vib=(0.22, 0.7), shimmer=(5200.0, 0.10), drone=0.10, reverb=0.6, damp=4200.0, breath=0.6)

_NEBULA = dict(          # lush chords blooming slowly - a star nursery
    base=130.81, scale=_PENTA, roots=_ROOTS, octaves=[1.0, 2.0, 2.0],
    root_period=48.0, root_period_range=(36.0, 70.0), interval=(3.5, 7.0),
    attack=(6.0, 10.0), hold=(4.0, 10.0), release=(8.0, 13.0), amp=(0.22, 0.45),
    pan=0.8, partials=[(1.0, 1.0), (2.0, 0.5), (3.0, 0.3), (4.0, 0.18), (5.0, 0.1)],
    vib=(0.16, 0.6), formant=[(520.0, 3.0, 0.8), (1500.0, 5.0, 0.4)],
    drone=0.16, reverb=0.7, damp=2600.0, breath=0.4)

_PULSAR = dict(          # a slow, steady cosmic beat from a spinning star
    base=73.42, scale=_PENTA, roots=[1 / 1, 3 / 2, 4 / 3, 5 / 4],
    octaves=[1.0, 2.0, 2.0, 4.0], root_period=40.0, root_period_range=(30.0, 56.0),
    interval=(4.0, 8.0), attack=(3.0, 6.0), hold=(2.0, 6.0), release=(5.0, 9.0),
    amp=(0.20, 0.40), pan=0.85, partials=[(1.0, 1.0), (2.0, 0.35), (3.0, 0.12)],
    # 0.748 Hz is the real spin rate of PSR B1919+21, the first pulsar ever
    # found (period 1.3373 s) - a calm, true cosmic beat.
    vib=(0.20, 0.6), pulse=(0.748, 0.7), drone=0.22, reverb=0.6, damp=3000.0,
    breath=0.4)

_GRAVITY = dict(         # deep tones sliding down - a black-hole ringdown
    base=49.0, scale=_MINOR, roots=[1 / 1, 6 / 5, 4 / 3, 3 / 2],
    octaves=[1.0, 1.0, 2.0], root_period=60.0, root_period_range=(45.0, 85.0),
    interval=(6.0, 12.0), attack=(4.0, 7.0), hold=(3.0, 7.0), release=(7.0, 12.0),
    amp=(0.30, 0.55), pan=0.6,
    partials=[(0.5, 0.5), (1.0, 1.0), (2.0, 0.22), (3.0, 0.07)],
    vib=(0.10, 0.3), glide=(0.5, 0.78), shimmer=(3000.0, 0.05),
    drone=0.20, reverb=0.78, damp=1700.0, breath=0.3)

_PLANETS = dict(         # scale derived from real planetary orbital periods
    base=65.41, scale=_PLANET_SCALE, roots=[1 / 1, 4 / 3, 3 / 2, 5 / 4],
    octaves=[1.0, 2.0, 2.0, 4.0], root_period=50.0, root_period_range=(38.0, 70.0),
    interval=(3.5, 7.0), attack=(5.0, 9.0), hold=(4.0, 10.0), release=(7.0, 12.0),
    amp=(0.22, 0.45), pan=0.8,
    partials=[(1.0, 1.0), (2.0, 0.4), (3.0, 0.15), (4.0, 0.06)],
    vib=(0.16, 0.6), drone=0.16, reverb=0.62, damp=2700.0, breath=0.45)

_AURORA = dict(          # ethereal, slowly shifting curtains of light
    base=196.0, scale=_PENTA, roots=_ROOTS, octaves=[1.0, 1.0, 2.0],
    root_period=40.0, root_period_range=(30.0, 58.0), interval=(3.0, 6.0),
    attack=(5.0, 9.0), hold=(3.0, 8.0), release=(7.0, 12.0), amp=(0.18, 0.36),
    pan=1.0, partials=[(1.0, 1.0), (2.0, 0.45), (3.0, 0.2), (5.0, 0.08)],
    vib=(0.14, 0.7), shimmer=(6200.0, 0.07), drone=0.08, reverb=0.72,
    damp=3600.0, breath=0.55)

_RINGS = dict(           # icy, glittering - the shimmer of Saturn's rings
    base=261.63, scale=_PENTA, roots=[1 / 1, 3 / 2, 5 / 4, 9 / 8],
    octaves=[1.0, 2.0, 2.0], root_period=32.0, root_period_range=(24.0, 46.0),
    interval=(2.2, 4.5), attack=(3.0, 6.0), hold=(2.0, 6.0), release=(5.0, 9.0),
    amp=(0.14, 0.30), pan=1.0,
    partials=[(1.0, 1.0), (2.0, 0.55), (3.0, 0.35), (4.0, 0.22), (6.0, 0.1)],
    vib=(0.18, 0.6), shimmer=(7800.0, 0.09), drone=0.06, reverb=0.7,
    damp=5200.0, breath=0.4)

# (key, display name, palette, seed, calibrated gain, description). Gains are set
# so the worst peak over a long deterministic render sits near 0.75 (see
# tools-style calibration in SESSION_LOG); reverb buildup is included.
_PRESETS = [
    ("spheres", "Music of the Spheres", _SPHERES, 71, 0.441,
     "Slow, consonant pads drifting in just intonation over a soft drone - the "
     "harmony of the spheres."),
    ("choir", "Starlight Choir", _CHOIR, 72, 0.563,
     "An endless, wordless choir of vowel-like voices, swelling and fading among "
     "the stars."),
    ("deep", "Deep Space", _DEEP, 73, 0.436,
     "Vast, low, slow tones with an airy shimmer - the hush of the deep, dark "
     "between the stars."),
    ("solar", "Solar Wind", _SOLAR, 74, 0.541,
     "Bright, airy tones streaming past on the solar wind, with a high silver "
     "shimmer."),
    ("nebula", "Nebula Bloom", _NEBULA, 75, 0.536,
     "Lush chords blooming and fading slowly, like glowing clouds where stars are "
     "born."),
    ("pulsar", "Pulsar Pulse", _PULSAR, 76, 0.611,
     "A slow, steady cosmic beat from a spinning star, with soft tones drifting "
     "over it."),
    ("gravity", "Gravity Well", _GRAVITY, 77, 0.457,
     "Deep tones sliding slowly downward into the dark - the long ringdown of a "
     "black hole."),
    ("planets", "The Planets", _PLANETS, 78, 0.497,
     "Chords tuned to the real orbital periods of the planets - Kepler's harmony "
     "of the spheres, made audible."),
    ("aurora", "Aurora Tones", _AURORA, 79, 0.563,
     "Ethereal, slowly shifting curtains of light - soft, cold, glowing tones "
     "drifting across the sky."),
    ("rings", "Saturn Ring Shimmer", _RINGS, 80, 0.757,
     "Icy, glittering high tones - the slow shimmer of light on Saturn's rings."),
]


def _register():
    for key, name, pal, seed, gain, desc in _PRESETS:
        register_generator(key, (lambda s, r, p=pal: _Cosmic(s, r, p)), seed)
        register(VoiceConfig(name, GROUP_MUSIC, kind="texture", texture=key,
                             env="volume", floor=1.0, gain=gain, description=desc))


_register()
