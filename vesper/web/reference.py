"""Reference numbers from the real Python core that the JavaScript port is tested against.

`fixture()` runs breathsim's breath clock (patterns.state_at, BreathController with
naturalness), envelopes, the DSP building blocks (RBJ biquads, one-pole LP, Kellet pink and
leaky-integrator brown filters), the Sleep wind-down / settle-in (SessionDirector with a tiny
fake app) and the sleep timer (vesper/sleeptimer.py). Written to tests/fixtures by
scripts/make_js_fixtures.py and read by vesper/web/static/*.test.mjs; also served at
/api/reference for the Verify page.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import signal

from breathsim import dsp, envelopes, patterns, voices  # noqa: F401  (voices first: it registers textures)
from breathsim import textures
from breathsim.controller import BreathController
from breathsim.naturalness import Naturalness
from breathsim.patterns import BreathPattern
from breathsim.session import SessionDirector

from .. import sleeptimer

STATE_KEYS = ("phase", "progress", "remaining", "volume", "airflow", "cycle_index",
              "cycle_frac", "pitch_mod", "tone_mod")


def _state(s) -> dict:
    return {k: getattr(s, k) for k in STATE_KEYS}


def _pat(p: BreathPattern) -> list:
    return [p.inhale, p.hold_full, p.exhale, p.hold_empty]


def _times(cycle: float, n: int = 29) -> list:
    return [cycle * 2.3 * i / (n - 1) for i in range(n)]


def _boundaries(p: BreathPattern) -> list:
    out, acc = [], 0.0
    for _, d in p.phases():
        acc += d
        out += [acc - 1e-9, acc, acc + 1e-9]
    return out


def _patterns_part():
    rows = []
    for p in patterns.PRESETS[:22]:
        ts = _times(p.cycle) + _boundaries(p) + [-1.0]
        rows.append({"name": p.name, "pattern": _pat(p),
                     "states": [[t, _state(patterns.state_at(p, t))] for t in ts]})
    bpm = [[b, le, _pat(patterns.pattern_for_bpm(b, le))]
           for b in (1, 3.5, 5.5, 6, 7.3, 12, 30) for le in (False, True)]
    return rows, bpm


def _naturalness_part():
    facs = []
    for amount, seed in ((0.25, 1), (0.6, 7), (1.0, 123456)):
        n = Naturalness(amount=amount, seed=seed)
        facs.append({"amount": amount, "seed": seed, "k": [
            [k, n.phase_factors(k), n.depth_factor(k), n.pitch_mod(k), n.tone_mod(k)]
            for k in (0, 1, 2, 5, 17, 99, 4096)]})
    ctl = BreathController(patterns.preset_by_name("4-7-8 Relaxing"))
    ctl.naturalness = Naturalness(amount=0.7, seed=3)
    states = [[t, _state(ctl.state_at(t))] for t in np.linspace(0, 80, 41).tolist()]
    ctl2 = BreathController(patterns.preset_by_name("Box Breathing 4-4-4-4"))
    ctl2.naturalness = Naturalness(amount=0.5, seed=1, depth=False, pitch=False)
    states2 = [[t, _state(ctl2.state_at(t))] for t in np.linspace(0, 70, 29).tolist()]
    return facs, [{"pattern": "4-7-8 Relaxing", "amount": 0.7, "seed": 3,
                   "flags": [True, True, True, True], "states": states},
                  {"pattern": "Box Breathing 4-4-4-4", "amount": 0.5, "seed": 1,
                   "flags": [True, False, False, True], "states": states2}]


def _envelopes_part():
    p = patterns.preset_by_name("Box Breathing 4-4-4-4")
    out = []
    for t in np.linspace(0, 16, 49).tolist():
        s = patterns.state_at(p, t)
        row = {"t": t}
        for env in ("airflow", "volume", "exhale", "inhale", "breath_both"):
            for atk in ("smooth", "explosive", "swell"):
                row[f"{env}/{atk}"] = envelopes.envelope(env, s, attack=atk)
        row["breath"] = envelopes.envelope("breath", s, attack="explosive",
                                           attack_in="swell", inhale_level=0.6,
                                           exhale_level=0.9)
        out.append(row)
    return out


def _dsp_part():
    sr = 44100
    x = [math.sin(0.37 * i) + 0.5 * math.cos(1.91 * i) * ((i % 7) - 3) / 3 for i in range(400)]
    coeffs = []
    for kind, fn in (("lowpass", dsp.lowpass), ("highpass", dsp.highpass),
                     ("bandpass", dsp.bandpass)):
        for fc, q in ((450.0, 0.8), (1400.0, 0.7), (4200.0, 0.6), (5.0, 1.0), (30000.0, 2.2)):
            b, a = fn(sr, fc, q)
            coeffs.append([kind, fc, q, b.tolist(), a.tolist()])
    b, a = dsp.lowpass(sr, 1400.0, 0.7)
    biquad = dsp.Biquad(b, a)
    bq_out = np.concatenate([biquad.process(np.array(x[:150])),
                             biquad.process(np.array(x[150:]))]).tolist()
    lp = dsp.OnePoleLP()
    op_out = np.concatenate([lp.process(np.array(x[:200]), 900.0, sr),
                             lp.process(np.array(x[200:]), 2500.0, sr)]).tolist()
    pink = signal.lfilter(dsp._PINK_B, dsp._PINK_A, x).tolist()
    brown = signal.lfilter([1.0], [1.0, -0.99], x).tolist()
    return {"sr": sr, "x": x, "coeffs": coeffs, "biquad": bq_out, "onepole": op_out,
            "pink": pink, "brown": brown, "scale": dsp._SCALE}


class _FakeCtl:
    def __init__(self):
        self.pattern = None
        self.running = True
        self.t = 0.0

    def set_pattern(self, p):
        self.pattern = p

    def elapsed(self):
        return self.t


class _FakeEngine:
    def __init__(self):
        self.master = None

    def set_master_volume(self, v):
        self.master = v


class _FakeApp:
    def __init__(self):
        self.controller, self.engine, self.user_volume = _FakeCtl(), _FakeEngine(), 0.8


def _session_part():
    a = patterns.preset_by_name("Calming 4-6 (Long Exhale)")
    b = patterns.preset_by_name("Extended 7-11")
    app = _FakeApp()
    sd = SessionDirector(app)
    sd.start_sleep(1200, a, b)
    wind = []
    for t in np.linspace(0, 1300, 27).tolist():
        sd._update_sleep(t)
        wind.append([t, _pat(app.controller.pattern), app.engine.master])
    app2 = _FakeApp()
    sd2 = SessionDirector(app2)
    target = patterns.preset_by_name("Coherent 5.5 (Resonance)")
    sd2.start_settle(target, duration=150.0)
    settle = [[0.0, _pat(app2.controller.pattern)]]
    for t in np.linspace(5, 160, 32).tolist():
        if sd2.settle:
            app2.controller.t = t
            sd2._update_settle(t)
            settle.append([t, _pat(app2.controller.pattern)])
    fade = [[m, e, *sleeptimer.fade_gain(m, e), sleeptimer.remaining_seconds(m, e)]
            for m in (0, 15, 30) for e in (0, 899.5, 900, 915, 929.9, 930, 1800, 1815, 1830, 5000)]
    return {"wind": {"duration": 1200, "a": _pat(a), "b": _pat(b), "user_volume": 0.8,
                     "rows": wind},
            "settle": {"duration": 150.0, "ratio": 0.62, "target": _pat(target),
                       "rows": settle},
            "fade": fade, "fade_seconds": sleeptimer.FADE_SECONDS}


def _textures_part():
    tarr = np.array([0.0, 0.05, 0.1005, 0.101, 0.13, 0.5, 1.7, 4.2, 9.0])
    hit = textures._Struck(44100, 220.0, textures._Bowl.PARTIALS, 0.1, amp=0.8, pan=0.3)
    left, right = hit.render(tarr)
    return {"bowl_partials": [list(x) for x in textures._Bowl.PARTIALS],
            "chime_partials": [list(x) for x in textures._Chimes.PARTIALS],
            "chime_notes": list(textures._Chimes.NOTES), "chime_base": textures._Chimes.BASE,
            "struck": {"f0": 220.0, "t0": 0.1, "amp": 0.8, "pan": 0.3, "t": tarr.tolist(),
                       "left": left.tolist(), "right": right.tolist(),
                       "dead": [hit.dead(x) for x in (30.0, 38.4, 38.6)]}}


LEVEL_VOICES = ("Deep Calm", "Soft Whisper", "Sleepy Warm", "Ocean Waves", "Gentle Rain",
                "Soft Rainstorm", "Brown Noise", "Deep Sleep (Pink Noise)")


def _levels_part(sr=48000, seconds=8.0, block=512):
    """RMS of the real NoiseTrack (seeded) at a steady mid-inhale state: the browser's synthesis of
    the same recipe should land close (the noise itself differs, so only statistically)."""
    from breathsim import tracks
    st = patterns.BreathState(phase="inhale", progress=0.5, remaining=1.0, volume=1.0,
                              airflow=1.0, cycle_index=0, label="Breathe In")
    out = []
    for name in LEVEL_VOICES:
        tr = tracks.build_track(voices.get_voice(name), sr)
        tr.nL.rng = np.random.default_rng(5)
        if getattr(tr, "stereo", False):
            tr.nR.rng = np.random.default_rng(6)
        x = np.concatenate([tr.render(block, st, st) for _ in range(int(seconds * sr / block))])
        x = x[sr:]                                        # skip the first second (filters settle)
        out.append({"name": name, "rms_l": float(np.sqrt(np.mean(x[:, 0] ** 2))),
                    "rms_r": float(np.sqrt(np.mean(x[:, 1] ** 2)))})
    return {"sr": sr, "seconds": seconds, "rows": out}


def fixture() -> dict:
    rows, bpm = _patterns_part()
    facs, nat_states = _naturalness_part()
    return {"patterns": rows, "bpm": bpm, "naturalness": facs, "nat_states": nat_states,
            "envelopes": _envelopes_part(), "dsp": _dsp_part(), "session": _session_part(),
            "textures": _textures_part(), "levels": _levels_part()}
