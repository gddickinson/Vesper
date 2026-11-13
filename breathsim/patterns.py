"""Breath pattern definitions and breath-cycle envelope math.

A :class:`BreathPattern` is four phase durations in seconds::

    inhale -> hold_full -> exhale -> hold_empty

From a time position inside the cycle we derive two envelopes:

``volume`` -- lung fullness in 0..1. Drives the visual breathing circle.
``airflow`` -- normalised |d(volume)/dt| in 0..1. Drives breath-sound
loudness (turbulent airflow is loudest mid-inhale / mid-exhale and silent
during holds), matching how real breath sounds behave.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import renames

PHASE_INHALE = "inhale"
PHASE_HOLD_FULL = "hold_full"
PHASE_EXHALE = "exhale"
PHASE_HOLD_EMPTY = "hold_empty"

PHASE_LABELS = {
    PHASE_INHALE: "Breathe In",
    PHASE_HOLD_FULL: "Hold",
    PHASE_EXHALE: "Breathe Out",
    PHASE_HOLD_EMPTY: "Hold",
}

# Friendlier wording for spoken cues on the empty hold.
PHASE_SPEECH = {
    PHASE_INHALE: "Breathe in",
    PHASE_HOLD_FULL: "Hold",
    PHASE_EXHALE: "Breathe out",
    PHASE_HOLD_EMPTY: "Rest",
}


@dataclass(frozen=True)
class BreathPattern:
    """Four-phase breathing pattern (durations in seconds)."""

    name: str
    inhale: float
    hold_full: float
    exhale: float
    hold_empty: float
    description: str = ""

    @property
    def cycle(self) -> float:
        total = self.inhale + self.hold_full + self.exhale + self.hold_empty
        return max(0.001, total)

    def phases(self):
        return (
            (PHASE_INHALE, self.inhale),
            (PHASE_HOLD_FULL, self.hold_full),
            (PHASE_EXHALE, self.exhale),
            (PHASE_HOLD_EMPTY, self.hold_empty),
        )

    def summary(self) -> str:
        parts = [f"{d:g}" for _, d in self.phases()]
        return "-".join(parts)


@dataclass(frozen=True)
class BreathState:
    """Snapshot of the breath cycle at one instant."""

    phase: str
    progress: float       # 0..1 within current phase
    remaining: float      # seconds left in current phase
    volume: float         # lung fullness 0..1 (visual size)
    airflow: float        # 0..1 turbulent-airflow loudness
    cycle_index: int      # number of completed cycles
    label: str
    cycle_frac: float = 0.0   # 0..1 position through the whole cycle (guide dot)
    pitch_mod: float = 0.0    # naturalness: per-breath pitch offset (semitones)
    tone_mod: float = 1.0     # naturalness: per-breath brightness multiplier


def _raised_cos(p: float) -> float:
    """Smooth 0 -> 1 ramp (raised cosine)."""
    return 0.5 - 0.5 * math.cos(math.pi * p)


def _volume(phase: str, p: float) -> float:
    if phase == PHASE_INHALE:
        return _raised_cos(p)
    if phase == PHASE_HOLD_FULL:
        return 1.0
    if phase == PHASE_EXHALE:
        return _raised_cos(1.0 - p)
    return 0.0


def _airflow(phase: str, p: float) -> float:
    # |d/dt| of a raised-cosine volume curve is a sine bump: 0 at the
    # turn-arounds, peak mid-phase. Holds have no airflow -> silence.
    if phase in (PHASE_INHALE, PHASE_EXHALE):
        return math.sin(math.pi * p)
    return 0.0


def state_at(pattern: BreathPattern, t: float) -> BreathState:
    """Compute the :class:`BreathState` of *pattern* at time *t* seconds."""
    cycle = pattern.cycle
    if t < 0:
        t = 0.0
    cycle_index = int(t // cycle)
    pos = t - cycle_index * cycle

    acc = 0.0
    chosen = None
    last_nonzero = None
    for phase, dur in pattern.phases():
        if dur <= 0:
            continue
        last_nonzero = (phase, dur, acc)
        if pos < acc + dur:
            chosen = (phase, dur, acc)
            break
        acc += dur
    if chosen is None:  # floating-point edge: fall back to last real phase
        chosen = last_nonzero or (PHASE_INHALE, cycle, 0.0)

    phase, dur, start = chosen
    p = (pos - start) / dur if dur > 0 else 0.0
    p = min(max(p, 0.0), 1.0)
    return BreathState(
        phase=phase,
        progress=p,
        remaining=dur * (1.0 - p),
        volume=_volume(phase, p),
        airflow=_airflow(phase, p),
        cycle_index=cycle_index,
        label=PHASE_LABELS[phase],
        cycle_frac=min(1.0, max(0.0, pos / cycle)),
    )


# --- Preset library: a wide range of speeds, durations and styles ----------

PRESETS = [
    BreathPattern("Coherent 5.5 (Resonance)", 5.5, 0, 5.5, 0,
                  "Equal 5.5s in/out (~5.5 breaths/min). A slow, steady rhythm "
                  "many people find relaxing, often called resonance breathing."),
    BreathPattern("Box Breathing 4-4-4-4", 4, 4, 4, 4,
                  "Equal inhale, hold, exhale, hold, also called square "
                  "breathing. An even, steady rhythm for settling and focus."),
    BreathPattern("4-7-8 Relaxing", 4, 7, 8, 0,
                  "The 4-7-8 count popularised by Dr Andrew Weil. The long "
                  "exhale makes it a gentle way to wind down."),
    BreathPattern("Calming 4-6 (Long Exhale)", 4, 0, 6, 0,
                  "Exhale longer than inhale: an easy, unhurried rhythm many "
                  "people find calming."),
    BreathPattern("Equal 4-4 (Sama Vritti)", 4, 0, 4, 0,
                  "Even inhale and exhale. Simple, steadying, good for "
                  "beginners."),
    BreathPattern("Deep Box 6-6-6-6", 6, 6, 6, 6,
                  "Slower square breathing for deeper relaxation and breath "
                  "control."),
    BreathPattern("Triangle 4-4-4", 4, 4, 4, 0,
                  "Inhale, hold, exhale in equal counts. A gentle step up "
                  "from equal breathing."),
    BreathPattern("Ujjayi Slow 6-6", 6, 0, 6, 0,
                  "Slow ocean breath pace for yoga and meditation."),
    BreathPattern("Energising 6-2", 6, 0, 2, 0,
                  "Long inhale, quick exhale to feel alert and awake."),
    BreathPattern("Quick Calm 3-5", 3, 0, 5, 0,
                  "Faster cycle with a longer exhale for on-the-spot calming."),
    BreathPattern("Extended 7-11", 7, 0, 11, 0,
                  "Very slow 7-in / 11-out. Deeply relaxing once you are warm."),
    BreathPattern("Wim Hof Rapid", 1.6, 0, 1.6, 0,
                  "Fast, full breaths (~19/min) in the Wim Hof style. Energising "
                  "- stop if light-headed."),
    BreathPattern("Sigh Release 2-7", 2, 0, 7, 0,
                  "Short inhale, long sighing exhale. Pairs well with the Sigh "
                  "and Haa voices to release tension."),
    BreathPattern("Physiological Sigh", 2.5, 1, 6, 0,
                  "A full inhale, a brief top-up catch, then a long slow exhale "
                  "(a 4-phase take on the double inhale). A quick way to pause."),
    BreathPattern("OM Chant 3-9", 3, 0, 9, 0,
                  "A long exhale for toning. Pair with a Chant or Hum voice and "
                  "let the sound carry the out-breath."),
    BreathPattern("Sharp 2-2", 2, 0, 2, 0,
                  "Brisk in and out for explosive/forceful breath voices. "
                  "Invigorating - keep it gentle at first."),
    BreathPattern("Long Tone 2-12 (Singers)", 2, 0, 12, 0,
                  "Quick breath in, long steady exhale. For vocal exercises - "
                  "sustained tones, sirens, scales and breath-control hisses."),
    BreathPattern("Breath of Fire", 0.45, 0, 0.45, 0,
                  "Rapid kapalabhati pumping (~65/min). Pair with the Breath of "
                  "Fire voice. Gentle and brief to start."),
    BreathPattern("Bhastrika (Bellows)", 0.7, 0, 0.7, 0,
                  "Forceful equal bellows breaths (~43/min). Pair with the "
                  "Bhastrika voice."),
    BreathPattern("Tummo (Vase)", 5, 6, 6, 0,
                  "Deep inhale, held vase breath, long exhale for inner-fire "
                  "practice. Pair with the Tummo voice."),
    BreathPattern("Sitali (Cooling)", 5, 1, 6, 0,
                  "Slow cooling tongue-hiss inhale, soft exhale. Pair with the "
                  "Sitali voice."),
    BreathPattern("Wim Hof Power", 2, 0, 2, 0,
                  "Deep, full power-breaths. Pair with the Wim Hof voice; "
                  "practise sitting or lying down."),
]

DEFAULT_PATTERN = PRESETS[0]


def preset_by_name(name: str) -> BreathPattern | None:
    name = renames.canonical(name)                  # old (renamed) names still resolve
    for p in PRESETS:
        if p.name == name:
            return p
    return None


def pattern_for_bpm(bpm: float, long_exhale: bool = False) -> BreathPattern:
    """A smooth, hold-free pattern at *bpm* breaths/minute (for paced/resonance
    breathing). ``long_exhale`` biases the cycle 40/60 toward the out-breath."""
    cycle = 60.0 / max(1.0, float(bpm))
    inh = cycle * (0.4 if long_exhale else 0.5)
    exh = cycle - inh
    note = "longer exhale" if long_exhale else "even"
    return BreathPattern("Custom", round(inh, 2), 0.0, round(exh, 2), 0.0,
                         f"Paced breathing at {bpm:g}/min ({note}).")


def add_pattern(p: BreathPattern) -> BreathPattern:
    """Add/replace a pattern in the shared PRESETS list (in place)."""
    for i, existing in enumerate(PRESETS):
        if existing.name == p.name:
            PRESETS[i] = p
            return p
    PRESETS.append(p)
    return p
