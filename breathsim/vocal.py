"""Vocal-tract track: the full range of human breath and voice sounds.

A :class:`VocalTrack` blends a glottal *buzz* source and *aspiration* noise
(by a voicing amount), shapes them through a formant bank (a vowel or breath
colour), and applies a flexible breath envelope. This covers nose/mouth
breaths of varying openness, sighs (falling pitch), explosive breaths, "haa"
breathing, vowel chants, hums and lip trills.
"""
from __future__ import annotations

import math

import numpy as np

from . import articulation, dsp, envelopes
from .formants import build_formants
from .patterns import PHASE_EXHALE, PHASE_INHALE
from .personas import DEFAULT as DEFAULT_PERSONA
from .voices import VoiceConfig

TWO_PI = 2.0 * math.pi

_MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11, 12]
_ARPEGGIO = [0, 4, 7, 12, 7, 4]


def _raised_cos(p: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, p)))


class BuzzSource:
    """Glottal source: a stack of harmonics with vibrato and pitch glide."""

    def __init__(self, sr: int, base: float, n_harm: int = 18):
        self.sr = sr
        self.phi = 0.0
        self.vphi = 0.0
        amps = []
        for k in range(1, n_harm + 1):
            amps.append(0.0 if k * base > 0.45 * sr else 1.0 / k)
        total = sum(amps) or 1.0
        self.amps = np.array(amps) / total
        self.k = np.arange(1, n_harm + 1)

    def render(self, frames, base, glide0, glide1, vib_rate, vib_depth):
        vinc = TWO_PI * vib_rate / self.sr
        vph = self.vphi + vinc * np.arange(1, frames + 1)
        self.vphi = float(vph[-1] % TWO_PI)
        glide = np.linspace(glide0, glide1, frames)
        f0 = base * glide * (1.0 + vib_depth * np.sin(vph))
        phi = self.phi + np.cumsum(TWO_PI * f0 / self.sr)
        self.phi = float(phi[-1] % TWO_PI)
        out = np.zeros(frames)
        for amp, k in zip(self.amps, self.k):
            if amp > 0.0:
                out += amp * np.sin(k * phi)
        return out


class VocalTrack:
    def __init__(self, cfg: VoiceConfig, sr: int, persona=None,
                 transpose: float = 1.0):
        self.cfg = cfg
        self.sr = sr
        persona = persona or DEFAULT_PERSONA
        # Apply the voice body (male/female/age/deep/high) and any transpose.
        self._pmul = persona.pitch_mul
        self._fscale = persona.formant_scale
        self.sequence = None            # set for chant/song phrase voices
        self.seq_base = cfg.pitch
        self.style = "per_breath"       # per_breath | per_phrase
        self.groups = None              # breath-groups for per_phrase
        self._active_seg = None
        self._syll_t = 0                # samples since current syllable onset
        self._cons = None
        self._cons_bank = None
        self._cons_total = 0.0
        self._coda_spec = None          # closing consonant of the syllable
        self._coda_bank = None
        self._coda_total = 0.0
        self._slot_dur = 0.0            # seconds this syllable has to sound
        self._prev_phase = None
        self.pitch = cfg.pitch * persona.pitch_mul * transpose
        self.voicing = min(1.0, max(0.0, cfg.voicing * persona.voicing_mul))
        self.air = cfg.air * persona.air_mul
        self.vib_rate = cfg.vibrato_rate * persona.vib_mul
        self.formants = build_formants(sr, cfg.vowel, persona.formant_scale)
        self.formants_in = (build_formants(sr, cfg.vowel_in, persona.formant_scale)
                            if cfg.vowel_in else self.formants)
        self.formants_to = (build_formants(sr, cfg.vowel_to, persona.formant_scale)
                            if cfg.vowel_to else None)
        self.noise = dsp.Noise(cfg.noise, sr)
        self.buzz = (BuzzSource(sr, self.pitch, cfg.n_harm)
                     if cfg.source in ("buzz", "mix") else None)
        self.src_lp = dsp.OnePoleLP()
        self.body_lp = dsp.OnePoleLP()
        self.air_lp = dsp.OnePoleLP()
        self._am_phase = 0.0

    def set_sequence(self, segments, base_pitch, style="per_breath", groups=None,
                     monotone=False):
        """Drive this voice from a phrase. ``per_breath`` sings one segment per
        breath; ``per_phrase`` sings a whole breath-group across the exhale.
        ``monotone`` chants every syllable on the tonic with reduced vibrato -- a
        steady recitation tone (authentic Vedic/Gregorian chant practice)."""
        self.sequence = segments
        self.seq_base = base_pitch
        self.style = style
        self.groups = groups
        self.monotone = monotone
        self._active_seg = None
        self._prev_phase = None

    def _set_syllable(self, seg):
        self._active_seg = seg
        self.formants = build_formants(self.sr, seg.vowel, self._fscale)
        self.formants_to = (build_formants(self.sr, seg.vowel_to, self._fscale)
                            if seg.vowel_to else None)
        semis = 0.0 if getattr(self, "monotone", False) else seg.semitone
        self.pitch = self.seq_base * self._pmul * (2.0 ** (semis / 12.0))
        self._syll_t = 0
        onset = getattr(seg, "onset", "")
        self._cons = articulation.spec(onset) if onset else None
        if self._cons:
            key = self._cons.get("formant") or seg.vowel
            self._cons_bank = build_formants(self.sr, key, self._fscale)
            self._cons_total = articulation.total_dur(onset)
        else:
            self._cons_bank, self._cons_total = None, 0.0
        coda = getattr(seg, "coda", "")
        self._coda_spec = articulation.spec(coda) if coda else None
        if self._coda_spec:
            key = self._coda_spec.get("formant") or seg.vowel
            self._coda_bank = build_formants(self.sr, key, self._fscale)
            self._coda_total = articulation.total_dur(coda)
        else:
            self._coda_bank, self._coda_total = None, 0.0

    def _phrase_segment(self, cycle_index, p):
        groups = self.groups or [(0, len(self.sequence))]
        lo, hi = groups[cycle_index % len(groups)]
        seg_list = self.sequence[lo:hi]
        n = max(1, len(seg_list))
        slot = min(int(p * n), n - 1)
        return seg_list[slot], (p * n - slot)          # segment, local progress

    def _seq_position(self, st):
        """Return (sounding, syllable_progress) and update the active syllable."""
        if st.phase != PHASE_EXHALE:
            self._prev_phase = st.phase
            return False, 0.0
        exhale = st.remaining / max(1e-3, 1.0 - st.progress)   # full exhale (s)
        if self.style == "per_phrase":
            groups = self.groups or [(0, len(self.sequence))]
            lo, hi = groups[st.cycle_index % len(groups)]
            slot = exhale / max(1, hi - lo)
            seg, sp = self._phrase_segment(st.cycle_index, st.progress)
        else:
            seg = self.sequence[st.cycle_index % len(self.sequence)]
            sp = st.progress
            slot = exhale
        if seg is not self._active_seg or self._prev_phase != PHASE_EXHALE:
            self._set_syllable(seg)
            self._slot_dur = slot
        self._prev_phase = st.phase
        return True, sp

    def _consonant(self, local_t, noise, buzz):
        spec = self._cons
        if not spec:
            return 0.0
        src = buzz if spec["kind"] == "voiced" else noise
        out = self._apply_bank(self._cons_bank, src) if self._cons_bank else src
        pre, dur = spec.get("pre", 0.0), spec["dur"]
        shape = spec["shape"]
        if shape == "burst":
            e = (local_t >= pre) * np.exp(-np.maximum(local_t - pre, 0) / (dur * 0.5))
        elif shape == "fric":
            e = np.clip(local_t / (dur * 0.6), 0.0, 1.0)
        else:                                          # murmur / glide / aspirate
            e = np.clip(local_t / 0.02, 0.0, 1.0)
        e = e * np.clip((self._cons_total - local_t) / 0.02, 0.0, 1.0)
        return out * e * spec.get("level", 0.5)

    def _coda(self, local_t, noise, buzz):
        """Closing consonant at the end of the syllable's time, plus the gate that
        ducks the vowel out as it arrives. Returns (coda_signal, vowel_gate)."""
        spec = self._coda_spec
        if not spec or self._slot_dur <= 0.0:
            return 0.0, 1.0
        start = max(self._cons_total + 0.06, self._slot_dur - self._coda_total)
        ct = local_t - start                            # time into the coda
        src = buzz if spec["kind"] == "voiced" else noise
        out = self._apply_bank(self._coda_bank, src) if self._coda_bank else src
        dur, shape = spec["dur"], spec["shape"]
        if shape == "burst":
            e = np.exp(-np.maximum(ct, 0.0) / (dur * 0.5))
        elif shape == "fric":
            e = np.clip(ct / (dur * 0.5), 0.0, 1.0)
        else:                                           # murmur / glide
            e = np.clip(ct / 0.02, 0.0, 1.0)
        e = e * (ct >= -1e-4) * np.clip((self._slot_dur - local_t) / 0.03, 0.0, 1.0)
        duck = np.clip(1.0 - (local_t - start) / 0.05, 0.0, 1.0)   # vowel -> coda
        return out * e * spec.get("level", 0.5), duck

    def _render_sequence(self, frames, s0, s1):
        sounding, sp = self._seq_position(s0)
        if not sounding:
            self._syll_t += frames
            return np.zeros((frames, 2))
        pf = 2.0 ** (s0.pitch_mod / 12.0)        # naturalness: pitch + tone
        tone = s0.tone_mod
        # Reciting tone: a steadier, purer voice (much-reduced vibrato).
        vib_depth = self.cfg.vibrato_depth * (0.3 if getattr(self, "monotone",
                                                             False) else 1.0)
        noise = self.noise.generate(frames)
        buzz = (self.buzz.render(frames, self.pitch * pf, 1.0, 1.0, self.vib_rate,
                                 vib_depth)
                if self.buzz is not None else np.zeros(frames))
        local_t = (self._syll_t + np.arange(frames)) / self.sr
        src = self.voicing * buzz + (1.0 - self.voicing) * noise
        vowel = self._apply_bank(self.formants, src)
        if self.formants_to is not None:
            vowel = vowel * (1.0 - sp) + self._apply_bank(self.formants_to, src) * sp
        if self.buzz is not None and self.voicing > 0.0:
            vowel += self.voicing * 0.4 * self.body_lp.process(src, 1100.0, self.sr)
        # Breathiness is warm (low cutoff) noise that sits *within* the vowel's
        # body, so it reads as a soft breathy voice rather than the bright hiss
        # (formerly low-passed at 6.5 kHz) that used to sit on top of the word.
        if self.air > 0.0:
            vowel += self.air * self.air_lp.process(noise, 2400.0 * tone, self.sr)
        vgate = np.clip((local_t - self._cons_total) / 0.025, 0.0, 1.0)
        cons = self._consonant(local_t, noise, buzz)
        coda, duck = self._coda(local_t, noise, buzz)
        rel = 1.0 if sp < 0.88 else _raised_cos((1.0 - sp) / 0.12)
        mono = (cons + vowel * vgate * duck * rel + coda) * self.cfg.gain
        self._syll_t += frames
        return np.column_stack([mono, mono])

    # --- envelope ----------------------------------------------------------

    def _amp(self, state):
        cfg = self.cfg
        base = envelopes.envelope(
            cfg.env, state, attack=cfg.attack,
            attack_in=(cfg.attack_in or cfg.attack),
            inhale_level=cfg.inhale_level, exhale_level=cfg.exhale_level)
        return cfg.floor + (1.0 - cfg.floor) * base

    def _glide(self, state):
        cfg = self.cfg
        shape = cfg.glide_shape
        if shape == "linear" and cfg.pitch_glide == 0.0:
            return 1.0
        p = state.progress if state.phase == PHASE_EXHALE else 0.0
        if shape == "updown":               # siren: rise then fall
            semis = cfg.pitch_glide * (1.0 - abs(2.0 * p - 1.0))
        elif shape == "scale_up":           # walk up a major scale
            i = min(int(p * len(_MAJOR_SCALE)), len(_MAJOR_SCALE) - 1)
            semis = _MAJOR_SCALE[i]
        elif shape == "arp_up":             # major arpeggio up and back
            i = min(int(p * len(_ARPEGGIO)), len(_ARPEGGIO) - 1)
            semis = _ARPEGGIO[i]
        else:                               # linear sweep
            semis = cfg.pitch_glide * p
        return 2.0 ** (semis / 12.0)

    def _apply_bank(self, bank, src):
        out = np.zeros(len(src))
        for bq, gain in bank:
            out += bq.process(src) * gain
        return out

    # --- render ------------------------------------------------------------

    def render(self, frames, s0, s1):
        cfg = self.cfg
        if self.sequence:
            return self._render_sequence(frames, s0, s1)
        amp = np.linspace(self._amp(s0), self._amp(s1), frames)
        pf = 2.0 ** (s0.pitch_mod / 12.0)        # naturalness: pitch + tone
        tone = s0.tone_mod
        noise = self.noise.generate(frames)

        src = np.zeros(frames)
        if cfg.source in ("noise", "mix"):
            src += (1.0 - self.voicing) * noise
        if cfg.source in ("buzz", "mix") and self.buzz is not None:
            buzz = self.buzz.render(frames, self.pitch * pf, self._glide(s0),
                                    self._glide(s1), self.vib_rate,
                                    cfg.vibrato_depth)
            buzz = self.src_lp.process(buzz, 5200.0, self.sr)
            src += self.voicing * buzz

        bank = (self.formants_in if (s0.phase == PHASE_INHALE
                and self.formants_in is not self.formants) else self.formants)
        out = self._apply_bank(bank, src) if bank else src
        if self.formants_to is not None and bank is self.formants:
            p = s0.progress if s0.phase == PHASE_EXHALE else 0.0
            out = out * (1.0 - p) + self._apply_bank(self.formants_to, src) * p

        # Voiced sounds keep a low-passed "body" of the source so the
        # fundamental and chest resonance come through (not just thin formants).
        if self.buzz is not None and self.voicing > 0.0:
            out += self.voicing * 0.4 * self.body_lp.process(src, 1100.0, self.sr)

        if self.air > 0.0:
            out += self.air * self.air_lp.process(noise, 6500.0 * tone, self.sr)

        if cfg.am_rate > 0.0:
            inc = TWO_PI * cfg.am_rate / self.sr
            t = self._am_phase + inc * np.arange(1, frames + 1)
            self._am_phase = float(t[-1] % TWO_PI)
            out *= 1.0 - cfg.am_depth * 0.5 * (1.0 + np.sin(t))

        out *= amp * cfg.gain
        return np.column_stack([out, out])
