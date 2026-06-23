"""Modes: one-click presets that configure the whole app for a situation.

Selecting a mode sets the pattern, voice, ambience, effect, voice body, choir,
visual scene, spoken-cue style, volume and session at once -- the easy,
soothing path. The detailed panels remain for fine-tuning afterwards.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mode:
    name: str
    description: str
    pattern: str
    voice: str
    voice_out: str | None = None         # separate exhale voice (None = same)
    scene: str = "orb"
    ambience: str | None = None
    effect: str | None = None
    persona: str = "Male"
    cue_style: str = "Off"
    choir: tuple | None = None          # (voice, harmony, level, mixed)
    volume: float = 0.7
    session: int = 0
    sleep: tuple | None = None          # (duration_s, start_pattern, end_pattern)


MODES = [
    Mode("Meditate", "Calm, balanced breathing with a glowing orb.",
         "Coherent 5.5 (Resonance)", "Deep Calm", scene="orb",
         cue_style="Off", volume=0.7),
    Mode("Breathwork", "Box breathing: in through the nose, out through pursed "
         "lips.", "Box Breathing 4-4-4-4", "Nose Breath",
         voice_out="Pursed-Lip Exhale", scene="orb", cue_style="Standard",
         volume=0.75),
    Mode("Chant", "Toning OM with a choir and resonant ripples.",
         "OM Chant 3-9", "Chant: Om", scene="ripple",
         choir=("Chant: Om", "Major triad", 0.6, True), volume=0.7),
    Mode("Sing", "Sustained singing tones over a long exhale.",
         "Long Tone 2-12 (Singers)", "Sing: Ah (vibrato)", scene="ripple",
         persona="Female", volume=0.7),
    Mode("Relax", "Gentle long-exhale breathing over ocean waves.",
         "Calming 4-6 (Long Exhale)", "Ocean Breath (Ujjayi)", scene="wave",
         ambience="Ocean Waves", volume=0.7),
    Mode("Sleep", "Breath slows and fades under rain, a heartbeat and stars.",
         "Calming 4-6 (Long Exhale)", "Sleepy Warm", scene="night",
         ambience="Soft Rainstorm", effect="Heartbeat (slow)", cue_style="Off",
         volume=0.6, session=1200,
         sleep=(1200, "Calming 4-6 (Long Exhale)", "Extended 7-11")),
]

DEFAULT = "Meditate"
_BY_NAME = {m.name: m for m in MODES}


def names():
    return [m.name for m in MODES]


def get(name: str) -> Mode | None:
    return _BY_NAME.get(name)
