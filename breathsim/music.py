"""Tiny music helpers: note names <-> frequency and semitone math.

Used by the chant drone / shruti, the singing reference pitch and the live
pitch monitor. Equal temperament, A4 = 440 Hz. No dependencies.
"""
from __future__ import annotations

import math

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
A4 = 440.0
_A4_MIDI = 69


def note_to_midi(name: str) -> int:
    """'A4' / 'C#3' / 'Db3' -> MIDI number (C4 = 60)."""
    name = name.strip()
    i = 1
    if len(name) > 1 and name[1] in "#b":
        i = 2
    pitch, octave = name[:i], int(name[i:])
    pitch = pitch.replace("Db", "C#").replace("Eb", "D#").replace(
        "Gb", "F#").replace("Ab", "G#").replace("Bb", "A#")
    return 12 * (octave + 1) + NOTE_NAMES.index(pitch)


def midi_to_hz(midi: float) -> float:
    return A4 * 2.0 ** ((midi - _A4_MIDI) / 12.0)


def note_to_hz(name: str) -> float:
    return midi_to_hz(note_to_midi(name))


def hz_to_note(hz: float):
    """Return (name, cents_off) for the nearest equal-tempered note."""
    if hz <= 0:
        return ("--", 0.0)
    midi = _A4_MIDI + 12.0 * math.log2(hz / A4)
    nearest = round(midi)
    cents = (midi - nearest) * 100.0
    name = NOTE_NAMES[int(nearest) % 12] + str(int(nearest) // 12 - 1)
    return (name, cents)


def semitones(from_hz: float, to_hz: float) -> float:
    """Semitone interval from one frequency to another."""
    return 12.0 * math.log2(to_hz / from_hz)


def note_range(lo: str = "C2", hi: str = "C6"):
    """List of note names from *lo* to *hi* inclusive."""
    return [NOTE_NAMES[m % 12] + str(m // 12 - 1)
            for m in range(note_to_midi(lo), note_to_midi(hi) + 1)]
