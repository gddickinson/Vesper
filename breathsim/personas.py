"""Voice bodies (personas): male/female, age and deep/high distinctions.

A persona scales two independent things that define who is making the sound:

* ``pitch_mul``     -- glottal fundamental. Lower = deeper/older/male.
* ``formant_scale`` -- vocal-tract length. Smaller tract (female/child) raises
  all formants; larger tract (male/deep) lowers them.

Scaling *both* is what separates a genuine female/child voice from a sped-up
male one. Personas combine with any vocal voice (especially chants), so we get
e.g. a female "Aah" or a child "OM" without multiplying the voice list.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    name: str
    pitch_mul: float
    formant_scale: float
    voicing_mul: float = 1.0
    air_mul: float = 1.0
    vib_mul: float = 1.0
    description: str = ""


# Base vocal voices are tuned to an adult-male reference (pitch_mul 1.0).
# Ordered low -> high so the menu reads naturally.
PERSONAS = [
    Persona("Giant", 0.55, 0.82,
            description="Enormous and cavernous - very low and wide."),
    Persona("Deep Male (bass)", 0.70, 0.90,
            description="Very low, resonant chest voice."),
    Persona("Baritone", 0.82, 0.95,
            description="Warm, low male voice."),
    Persona("Male", 1.0, 1.0,
            description="Adult male reference voice."),
    Persona("Tenor", 1.12, 1.03,
            description="Higher, brighter male voice."),
    Persona("Androgynous", 1.2, 1.06,
            description="An ambiguous mid-range voice."),
    Persona("Alto", 1.3, 1.08,
            description="A lower female voice."),
    Persona("Female", 1.5, 1.14,
            description="Adult female: higher pitch and shorter vocal tract."),
    Persona("Boy", 1.75, 1.22,
            description="A young boy's voice."),
    Persona("High Female (soprano)", 1.85, 1.22,
            description="Bright, high female voice."),
    Persona("Child", 2.25, 1.35,
            description="Small body, high pitch and high formants."),
    Persona("Sprite", 2.7, 1.5,
            description="Tiny, sparkling and very high."),
    Persona("Elder", 0.92, 1.0, voicing_mul=0.85, air_mul=1.5, vib_mul=1.3,
            description="Older voice: breathier with a gentle tremor."),
    Persona("Monotone", 1.0, 1.0, vib_mul=0.0,
            description="Flat and steady - no vibrato, slightly robotic."),
]

_BY_NAME = {p.name: p for p in PERSONAS}
DEFAULT = _BY_NAME["Male"]       # neutral reference


def names():
    return [p.name for p in PERSONAS]


def get(name: str) -> Persona:
    return _BY_NAME.get(name, DEFAULT)
