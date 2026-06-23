"""Choir / multi-voice overlay: stack a chant or singing voice into a chord.

Drives up to ``N_SLOTS`` extra engine layers (``choir0``..``choirN``), each the
same voice transposed by a harmony interval (semitones), optionally with a
different voice body per note for a mixed-voice choir. Kept GUI-free so it can
be scripted or tested directly.
"""
from __future__ import annotations

from . import personas

HARMONIES = {
    "Off": [],
    "Unison (rich)": [-0.12, 0.0, 0.12],          # detuned chorus
    "Octaves": [-12.0, 0.0, 12.0],
    "Power (root + 5th)": [0.0, 7.0, 12.0],
    "Major triad": [0.0, 4.0, 7.0],
    "Minor triad": [0.0, 3.0, 7.0],
    "Sus2 / open": [0.0, 2.0, 7.0],
    "Major 7th (4 vox)": [0.0, 4.0, 7.0, 11.0],
}

# Bodies cycled across notes when "mixed voices" is on (low -> high).
_BODIES = ["Deep Male (bass)", "Male", "Female", "High Female (soprano)"]
N_SLOTS = 4


def names():
    return list(HARMONIES.keys())


def _slot(i):
    return f"choir{i}"


def _per_voice_level(level, n):
    # Keep total loudness sane as voices stack.
    return level / (max(1, n) ** 0.5)


def apply(engine, voice, harmony, level, mixed):
    """(Re)build the choir layers on *engine*."""
    intervals = HARMONIES.get(harmony, [])[:N_SLOTS]
    if not voice or voice == "None" or not intervals:
        clear(engine)
        return
    per = _per_voice_level(level, len(intervals))
    for i in range(N_SLOTS):
        if i < len(intervals):
            body = (personas.get(_BODIES[i % len(_BODIES)]) if mixed
                    else engine.persona)
            engine.set_layer(_slot(i), voice, level=per,
                             transpose=intervals[i], persona=body)
        else:
            engine.set_layer(_slot(i), None)


def set_level(engine, harmony, level):
    intervals = HARMONIES.get(harmony, [])[:N_SLOTS]
    per = _per_voice_level(level, len(intervals))
    for i in range(len(intervals)):
        engine.set_layer_level(_slot(i), per)


def clear(engine):
    for i in range(N_SLOTS):
        engine.set_layer(_slot(i), None)
