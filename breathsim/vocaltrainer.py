"""Vocal-training target model: what note the singer should be aiming at now.

A *spec* describes the target pitch over time (a held note, a reciting tone, or
a scrolling exercise). :func:`target_at` returns the current (and upcoming)
target so the pitch visualization can draw a line to hit; :func:`range_hz` gives
the frequency window to plot. Pure + unit-testable (no audio, no GUI).
"""
from __future__ import annotations

from . import music

# Scale/exercise patterns as semitone offsets from a base note. Ordered to be
# sung along to: ascend then descend so the singer returns home.
SCALES = {
    "Major scale (do-re-mi)": [0, 2, 4, 5, 7, 9, 11, 12, 11, 9, 7, 5, 4, 2, 0],
    "Five-note (do-re-mi-fa-so)": [0, 2, 4, 5, 7, 5, 4, 2, 0],
    "Octave leap": [0, 12, 0, 12, 0],
    "Major arpeggio": [0, 4, 7, 12, 7, 4, 0],
    "Fifth slide": [0, 7, 0, 7, 0],
    "Minor scale": [0, 2, 3, 5, 7, 8, 10, 12, 10, 8, 7, 5, 3, 2, 0],
    "Octave siren": [0, 3, 5, 7, 9, 12, 9, 7, 5, 3, 0],
    "Sixth stretch": [0, 9, 0, 9, 0],
}
DEFAULT_SPN = 2.5                       # seconds per target step (scale tempo)


def hold_spec(note, label=None, spn=DEFAULT_SPN):
    return {"mode": "hold", "base": note, "steps": [0], "spn": spn,
            "label": label or f"Hold {note}"}


def scale_spec(name, base, spn=DEFAULT_SPN):
    return {"mode": "scale", "base": base, "steps": SCALES.get(name, [0]),
            "spn": spn, "label": name}


def target_at(spec, t):
    """(target_hz, next_hz | None, label) at session time *t*."""
    base = music.note_to_midi(spec["base"])
    steps = spec["steps"]
    if spec["mode"] == "hold" or len(steps) <= 1:
        return (music.midi_to_hz(base + steps[0]), None, spec["label"])
    i = int(t / spec["spn"]) % len(steps)
    nxt = steps[(i + 1) % len(steps)]
    return (music.midi_to_hz(base + steps[i]),
            music.midi_to_hz(base + nxt), spec["label"])


def range_hz(spec, pad=3):
    """(lo_hz, hi_hz): the pitch window to plot, padded around the spec's notes."""
    base = music.note_to_midi(spec["base"])
    steps = spec["steps"]
    return (music.midi_to_hz(base + min(steps) - pad),
            music.midi_to_hz(base + max(steps) + pad))
