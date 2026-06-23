"""Rhythmic sound effects: realistic heartbeats and gentle drums.

A :class:`RhythmTrack` (``kind="rhythm"``) plays tempo-based hits independent
of the breath, as a soothing background layer. Hits are scheduled on a beat
grid (quantised to the audio block, which is inaudibly tight for these soft
sounds) and rendered as short decaying low tones with a pitch drop and a touch
of noise -- a "lub-dub" for the heart, a soft kick/tap for drums.

Registered into the voices registry on import (see the bottom of voices.py).
"""
from __future__ import annotations

import numpy as np

from . import dsp
from .voices import GROUP_EFFECTS, VoiceConfig, register

_RNG = np.random.default_rng(7)


class _Hit:
    """A short percussive hit: low body + 2nd harmonic + a bright attack click.

    The click and 2nd harmonic give energy in the 100 Hz-3 kHz range so the hit
    is clearly audible on laptop speakers (which roll off the sub-60 Hz
    fundamental of a real heartbeat / kick)."""

    def __init__(self, sr, freq, decay, amp, drop=0.0, harm2=0.0, click=0.0):
        self.sr = sr
        self.freq = freq
        self.decay = decay
        self.amp = amp
        self.drop = drop
        self.harm2 = harm2
        self.click = click
        self.elapsed = 0
        self.phase = 0.0
        self.dead = False

    def render(self, frames):
        n = np.arange(frames)
        t = (self.elapsed + n) / self.sr
        env = np.exp(-t / self.decay)
        freq = self.freq * (1.0 + self.drop * np.exp(-t * 22.0))   # pitch drop
        ph = self.phase + np.cumsum(dsp.TWO_PI * freq / self.sr)
        self.phase = float(ph[-1])
        out = (np.sin(ph) + self.harm2 * np.sin(2.0 * ph)) * env
        if self.click > 0.0:                          # bright attack transient
            out = out + self.click * np.exp(-t * 75.0) * _RNG.standard_normal(frames)
        out *= self.amp
        self.elapsed += frames
        if env[-1] < 1e-3:
            self.dead = True
        return out


def _heart_hits(_beat_index):
    return [(0.0, dict(freq=60.0, decay=0.22, amp=1.0, drop=0.5, harm2=0.6,
                       click=0.16)),
            (0.20, dict(freq=50.0, decay=0.17, amp=0.62, drop=0.5, harm2=0.6,
                        click=0.12))]


def _drum_hits(beat_index):
    m = beat_index % 4
    if m == 0:
        spec = dict(freq=86.0, decay=0.24, amp=1.0, drop=0.7, harm2=0.4, click=0.5)
    elif m == 2:
        spec = dict(freq=82.0, decay=0.20, amp=0.72, drop=0.7, harm2=0.4,
                    click=0.42)
    else:
        spec = dict(freq=190.0, decay=0.10, amp=0.45, harm2=0.2, click=0.7)
    hits = [(0.0, spec)]
    if m in (1, 3):                                  # gentle off-beat tap
        hits.append((0.5, dict(freq=240.0, decay=0.07, amp=0.26, click=0.85)))
    return hits


class RhythmTrack:
    def __init__(self, cfg: VoiceConfig, sr: int):
        self.cfg = cfg
        self.sr = sr
        self.beat = 60.0 / max(20.0, cfg.bpm)
        self._gen = _heart_hits if cfg.rhythm == "heartbeat" else _drum_hits
        self.t = 0.0
        self.next_beat = 0.0
        self.beat_index = 0
        self.pending: list[tuple[float, dict]] = []
        self.hits: list[_Hit] = []

    def render(self, frames, s0, s1):
        end = self.t + frames / self.sr
        while self.next_beat < end:
            for frac, spec in self._gen(self.beat_index):
                self.pending.append((self.next_beat + frac * self.beat, spec))
            self.beat_index += 1
            self.next_beat += self.beat
        still = []
        for when, spec in self.pending:
            if when <= end:
                self.hits.append(_Hit(self.sr, **spec))
            else:
                still.append((when, spec))
        self.pending = still
        self.t = end

        out = np.zeros(frames)
        alive = []
        for h in self.hits:
            out += h.render(frames)
            if not h.dead:
                alive.append(h)
        self.hits = alive
        out *= self.cfg.gain
        return np.column_stack([out, out])


def _e(name, **kw):
    register(VoiceConfig(name, GROUP_EFFECTS, kind="rhythm", env="free", **kw))


_e("Heartbeat (resting)", rhythm="heartbeat", bpm=60.0, gain=0.42,
   description="A steady resting heartbeat (60 bpm).")
_e("Heartbeat (calm)", rhythm="heartbeat", bpm=66.0, gain=0.42,
   description="A gentle heartbeat (66 bpm).")
_e("Heartbeat (slow)", rhythm="heartbeat", bpm=48.0, gain=0.44,
   description="A slow, calming heartbeat (48 bpm) - good for winding down.")
_e("Gentle Drum", rhythm="drum", bpm=60.0, gain=0.30,
   description="A soft, slow drum pulse.")
_e("Frame Drum", rhythm="drum", bpm=72.0, gain=0.36,
   description="A gentle hand-drum rhythm.")
_e("Tabla Pulse", rhythm="drum", bpm=84.0, gain=0.34,
   description="A light, brisk hand-drum pulse.")
