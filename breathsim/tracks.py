"""Audio track renderers.

A *track* takes a :class:`~breathsim.voices.VoiceConfig` and renders stereo
audio blocks synchronised to the breath. ``render(frames, s0, s1)`` produces a
``(frames, 2)`` float array, linearly ramping the breath envelope from state
``s0`` (block start) to ``s1`` (block end) to avoid zipper noise.
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp, envelopes
from .patterns import PHASE_EXHALE, PHASE_INHALE, BreathState
from .voices import VoiceConfig

SQRT2 = math.sqrt(2.0)


def _make_static(ftype: str, sr: int, fc: float, q: float) -> dsp.Biquad:
    if ftype == "lowpass":
        b, a = dsp.lowpass(sr, fc, q)
    elif ftype == "highpass":
        b, a = dsp.highpass(sr, fc, q)
    else:
        b, a = dsp.bandpass(sr, fc, q)
    return dsp.Biquad(b, a)


def _env_value(cfg: VoiceConfig, state: BreathState) -> float:
    # Route through the shared envelope so noise/tonal voices honour the
    # phase-gating modes too (inhale / exhale / breath); airflow & volume are
    # returned unchanged, so existing voices behave identically.
    base = envelopes.envelope(cfg.env, state, attack=cfg.attack,
                              attack_in=cfg.attack_in,
                              inhale_level=cfg.inhale_level,
                              exhale_level=cfg.exhale_level)
    return cfg.floor + (1.0 - cfg.floor) * base


class _PanMixin:
    """Equal-power auto-pan shared by tracks; keeps a phase accumulator."""

    def _init_pan(self):
        self._pan_phase = 0.0

    def _pan_gains(self, cfg: VoiceConfig, frames: int, sr: int):
        if cfg.pan_rate <= 0 or cfg.pan_depth <= 0:
            return None
        inc = dsp.TWO_PI * cfg.pan_rate / sr
        t = self._pan_phase + inc * np.arange(1, frames + 1)
        self._pan_phase = float(t[-1] % dsp.TWO_PI)
        pan = cfg.pan_depth * np.sin(t)            # -depth..depth
        theta = (pan + 1.0) * (math.pi / 4.0)
        return np.cos(theta), np.sin(theta)


class NoiseTrack(_PanMixin):
    """Filtered-noise voice: breath timbres and nature ambiences."""

    def __init__(self, cfg: VoiceConfig, sr: int):
        self.cfg = cfg
        self.sr = sr
        self.stereo = cfg.width > 0.0
        ftype, fc, q = cfg.filt
        self.nL = dsp.Noise(cfg.noise, sr)
        self.statL = _make_static(ftype, sr, fc, q)
        self.brightL = dsp.OnePoleLP()
        if self.stereo:
            self.nR = dsp.Noise(cfg.noise, sr)
            self.statR = _make_static(ftype, sr, fc, q)
            self.brightR = dsp.OnePoleLP()
        self._init_pan()

    def _chain(self, noise, stat, bright, frames, amp, phase, tone=1.0):
        x = stat.process(noise.generate(frames))
        cutoff = (self.cfg.bright_base
                  + self.cfg.bright_mod * float(amp.mean())) * tone
        if phase == PHASE_EXHALE:
            cutoff *= self.cfg.exhale_mul
        x = bright.process(x, cutoff, self.sr)
        return x * amp

    def render(self, frames: int, s0: BreathState, s1: BreathState):
        amp = np.linspace(_env_value(self.cfg, s0),
                          _env_value(self.cfg, s1), frames)
        tone = s0.tone_mod                       # naturalness: per-breath timbre
        left = self._chain(self.nL, self.statL, self.brightL, frames, amp,
                           s0.phase, tone)
        if self.stereo:
            right = self._chain(self.nR, self.statR, self.brightR,
                                frames, amp, s0.phase, tone)
        else:
            right = left
        out = np.empty((frames, 2))
        pan = self._pan_gains(self.cfg, frames, self.sr)
        if pan is None:
            out[:, 0] = left
            out[:, 1] = right
        else:
            out[:, 0] = left * pan[0] * SQRT2
            out[:, 1] = right * pan[1] * SQRT2
        out *= self.cfg.gain
        return out


class TonalTrack:
    """Additive-sine drone that blooms with the breath envelope.

    ``transpose`` is a frequency multiplier (e.g. 2**(semitones/12)) so the same
    drone/reference voice can be set to any key/note."""

    def __init__(self, cfg: VoiceConfig, sr: int, transpose: float = 1.0):
        self.cfg = cfg
        self.sr = sr
        self.transpose = transpose
        self.phase = np.zeros(len(cfg.partials))

    def render(self, frames: int, s0: BreathState, s1: BreathState):
        amp = np.linspace(_env_value(self.cfg, s0),
                          _env_value(self.cfg, s1), frames)
        mono = np.zeros(frames)
        pf = 2.0 ** (s0.pitch_mod / 12.0)        # naturalness: per-breath pitch
        idx = np.arange(1, frames + 1)
        for i, (ratio, pamp) in enumerate(self.cfg.partials):
            inc = dsp.TWO_PI * (self.cfg.base_freq * ratio * pf
                                * self.transpose) / self.sr
            ph = self.phase[i] + inc * idx
            mono += pamp * np.sin(ph)
            self.phase[i] = float(ph[-1] % dsp.TWO_PI)
        mono *= amp * self.cfg.gain
        return np.column_stack([mono, mono])


class SampleTrack:
    """Play a loaded sample. ``trigger="loop"`` (default) loops continuously with
    its level modulated by the breath; ``trigger="exhale"``/``"inhale"`` fires the
    clip *once* at the start of that phase (a spoken word landing each breath)."""

    def __init__(self, cfg: VoiceConfig, sr: int):
        self.cfg = cfg
        self.sr = sr
        data = np.asarray(cfg.data, dtype=float)
        if data.ndim == 1:
            data = np.column_stack([data, data])
        self.data = data
        self.n = len(data)
        self.pos = 0
        self.trigger = getattr(cfg, "trigger", "loop")
        self._last_phase = None
        self._playing = self.trigger == "loop"

    def _render_loop(self, frames, s0, s1):
        amp = np.linspace(_env_value(self.cfg, s0),
                          _env_value(self.cfg, s1), frames)
        idx = (self.pos + np.arange(frames)) % self.n
        self.pos = int((self.pos + frames) % self.n)
        return self.data[idx] * amp[:, None] * self.cfg.gain

    def render(self, frames: int, s0: BreathState, s1: BreathState):
        if self.trigger == "loop":
            return self._render_loop(frames, s0, s1)
        target = PHASE_EXHALE if self.trigger == "exhale" else PHASE_INHALE
        if s0.phase == target and self._last_phase != target:   # rising edge
            self.pos, self._playing = 0, True
        self._last_phase = s0.phase
        out = np.zeros((frames, 2))
        if self._playing:
            end = min(self.pos + frames, self.n)
            out[: end - self.pos] = self.data[self.pos:end] * self.cfg.gain
            self.pos = end
            if self.pos >= self.n:
                self._playing = False
        return out


class SynthBreathTrack:
    """A clearly-synthetic breath: a swept resonant whoosh plus a soft detuned
    pad, carried by the breath envelope so it still reads as breathing.

    ``voicing`` blends whoosh (0) -> tonal pad (1); ``bright_base`` /
    ``bright_mod`` set the swept-resonance range; ``am_rate`` adds a mechanical
    pulse (e.g. a respirator)."""

    def __init__(self, cfg: VoiceConfig, sr: int, transpose: float = 1.0):
        self.cfg = cfg
        self.sr = sr
        self.base_freq = cfg.base_freq * transpose
        self.noise = dsp.Noise(cfg.noise, sr)
        self.bp = dsp.Biquad(*dsp.bandpass(sr, 600.0, 4.5))
        self.body_lp = dsp.OnePoleLP()
        self.partials = cfg.partials
        self.phase = np.zeros(len(cfg.partials))
        self._am_phase = 0.0

    def _amp(self, state):
        cfg = self.cfg
        base = envelopes.envelope(cfg.env, state, attack=cfg.attack,
                                  attack_in=(cfg.attack_in or cfg.attack),
                                  inhale_level=cfg.inhale_level,
                                  exhale_level=cfg.exhale_level)
        return cfg.floor + (1.0 - cfg.floor) * base

    def render(self, frames, s0, s1):
        cfg = self.cfg
        a0, a1 = self._amp(s0), self._amp(s1)
        amp = np.linspace(a0, a1, frames)
        em = 0.5 * (a0 + a1)
        cutoff = (cfg.bright_base + cfg.bright_mod * em) * s0.tone_mod
        pf = 2.0 ** (s0.pitch_mod / 12.0)        # naturalness: timbre + pitch
        x = self.noise.generate(frames)
        self.bp.update(*dsp.bandpass(self.sr, cutoff, 4.5))
        whoosh = self.bp.process(x) * 1.8
        body = self.body_lp.process(x, cutoff, self.sr) * 0.4
        idx = np.arange(1, frames + 1)
        pad = np.zeros(frames)
        for i, (ratio, pamp) in enumerate(self.partials):
            inc = dsp.TWO_PI * self.base_freq * pf * ratio / self.sr
            ph = self.phase[i] + inc * idx
            pad += pamp * np.sin(ph)
            self.phase[i] = float(ph[-1] % dsp.TWO_PI)
        mono = (whoosh + body) * (1.0 - cfg.voicing) + pad * cfg.voicing * 2.0
        mono *= amp
        if cfg.am_rate > 0.0:
            inc = dsp.TWO_PI * cfg.am_rate / self.sr
            t = self._am_phase + inc * idx
            self._am_phase = float(t[-1] % dsp.TWO_PI)
            mono *= 1.0 - cfg.am_depth * 0.5 * (1.0 + np.sin(t))
        mono *= cfg.gain
        return np.column_stack([mono, mono])


class MorphTrack:
    """Blend two voice tracks. ``amount_fn()`` in 0..1 selects A (0) -> B (1)."""

    def __init__(self, track_a, track_b, amount_fn):
        self.a = track_a
        self.b = track_b
        self.amount_fn = amount_fn

    def render(self, frames, s0, s1):
        m = self.amount_fn()
        m = 0.0 if m < 0.0 else 1.0 if m > 1.0 else m
        if m <= 0.001:
            return self.a.render(frames, s0, s1)
        if m >= 0.999:
            return self.b.render(frames, s0, s1)
        return (self.a.render(frames, s0, s1) * (1.0 - m)
                + self.b.render(frames, s0, s1) * m)


class PhaseGateTrack:
    """Wrap a track so it only sounds during one breath phase.

    Used for separate inhale/exhale voices: the inhale voice is gated to the
    inhale, the exhale voice to the exhale (smooth edges avoid clicks)."""

    def __init__(self, track, phase):
        self.track = track
        self.phase = phase                 # "inhale" or "exhale"

    def _gate(self, state):
        return envelopes.window(state.phase, self.phase, state.progress, "smooth")

    def render(self, frames, s0, s1):
        out = self.track.render(frames, s0, s1)
        gate = np.linspace(self._gate(s0), self._gate(s1), frames)[:, None]
        return out * gate


class BreathWordTrack:
    """Voice a spoken word once on each exhale, *time-warped to the breath*.

    The engine pre-stretches the word (off the audio thread) to the exhale
    length and exposes the buffer via ``buf_fn``; this track plays it once per
    exhale. ``match_fn`` (0..1) sets how strongly the breath then shapes the
    word: at 0 it plays flat (its own recorded shape), at 1 its loudness rides
    the exhale **airflow** (swells in, fades out) and it darkens as the breath
    empties — so the word sounds spoken on that breath."""

    def __init__(self, sr: int, buf_fn, match_fn):
        self.sr = sr
        self.buf_fn = buf_fn            # () -> mono ndarray to voice this exhale
        self.match_fn = match_fn        # () -> 0..1 breath-shaping amount
        self.buf = None
        self.pos = 0
        self.playing = False
        self._last_phase = None
        self._lp = dsp.OnePoleLP()

    def render(self, frames, s0, s1):
        if s0.phase == PHASE_EXHALE and self._last_phase != PHASE_EXHALE:
            self.buf = self.buf_fn()                # capture this exhale's clip
            self.pos = 0
            self.playing = self.buf is not None and len(self.buf) > 0
        self._last_phase = s0.phase
        out = np.zeros((frames, 2))
        if not self.playing or self.buf is None:
            return out
        end = min(self.pos + frames, len(self.buf))
        seg = np.zeros(frames)
        seg[:end - self.pos] = self.buf[self.pos:end]
        self.pos = end
        if self.pos >= len(self.buf):
            self.playing = False
        m = float(self.match_fn())
        if m > 0.0:
            af = np.linspace(s0.airflow, s1.airflow, frames)
            seg = seg * ((1.0 - m) + m * af)        # ride the breath's loudness
            cutoff = 2200.0 + 5200.0 * float(af.mean())  # darken as breath fades
            seg = seg * (1.0 - m) + self._lp.process(seg, cutoff, self.sr) * m
        out[:, 0] = seg
        out[:, 1] = seg
        return out


class GainTrack:
    """Scale a wrapped track by a live gain in 0..1, ramped across the block to
    avoid zipper noise. The gain is read each block from ``gain_fn`` so a slider
    (e.g. the word blend) can move it without rebuilding the track."""

    def __init__(self, track, gain_fn):
        self.track = track
        self.gain_fn = gain_fn
        self._last = float(gain_fn())

    def render(self, frames, s0, s1):
        g = float(self.gain_fn())
        ramp = np.linspace(self._last, g, frames)[:, None]
        self._last = g
        return self.track.render(frames, s0, s1) * ramp


class ExhaleDuckTrack:
    """Duck a track *during the exhale* by a live factor (0..1), leaving the
    inhale and holds at full. Lets a spoken word blend over (factor near 1) or
    fully override (factor 0) the voice that would otherwise sound on the
    exhale; edges ramp across the phase change so there is no click."""

    def __init__(self, track, factor_fn):
        self.track = track
        self.factor_fn = factor_fn

    def _g(self, state):
        return float(self.factor_fn()) if state.phase == PHASE_EXHALE else 1.0

    def render(self, frames, s0, s1):
        out = self.track.render(frames, s0, s1)
        gate = np.linspace(self._g(s0), self._g(s1), frames)[:, None]
        return out * gate


def build_track(cfg: VoiceConfig, sr: int, persona=None, transpose: float = 1.0):
    if cfg.kind == "vocal":
        from .vocal import VocalTrack
        return VocalTrack(cfg, sr, persona=persona, transpose=transpose)
    if cfg.kind == "synth":
        return SynthBreathTrack(cfg, sr, transpose=transpose)
    if cfg.kind == "rhythm":
        from .rhythm import RhythmTrack
        return RhythmTrack(cfg, sr)
    if cfg.kind == "texture":
        from .textures import TextureTrack
        return TextureTrack(cfg, sr)
    if cfg.kind == "tonal":
        return TonalTrack(cfg, sr, transpose=transpose)
    if cfg.kind == "sample":
        return SampleTrack(cfg, sr)
    return NoiseTrack(cfg, sr)
