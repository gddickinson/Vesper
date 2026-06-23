"""Synthetic breath voices -- clearly electronic, still recognisable as breaths.

Each is a swept resonant whoosh blended with a tonal pad, carried by the breath
envelope. They are the synthetic end of the human<->synthetic range: pick a
human voice as Voice A and one of these as Voice B, then use the Morph control.

Registered on import (see the bottom of voices.py). Rendered by
:class:`breathsim.tracks.SynthBreathTrack`. ``voicing`` blends whoosh->pad.
"""
from __future__ import annotations

from .voices import GROUP_SYNTH, VoiceConfig, register

_PAD = ((1.0, 0.5), (1.5, 0.3), (2.0, 0.2), (3.0, 0.1))
_CHORD = ((1.0, 0.45), (1.26, 0.3), (1.5, 0.3), (2.0, 0.2))   # root-M3-P5-oct
_COSMIC = ((1.0, 0.4), (2.0, 0.3), (3.0, 0.2), (5.0, 0.14), (8.0, 0.09))


def _s(name, **kw):
    register(VoiceConfig(name, GROUP_SYNTH, kind="synth", **kw))


_s("Synth Pad Breath", noise="pink", env="airflow", voicing=0.7,
   base_freq=130.0, partials=_PAD, bright_base=300.0, bright_mod=1800.0,
   gain=0.34, description="A soft synth pad that breathes in and out.")

_s("Whoosh (Filtered)", noise="white", env="airflow", voicing=0.05,
   base_freq=130.0, partials=_PAD, bright_base=350.0, bright_mod=3600.0,
   gain=0.26, description="A pure swept-resonance whoosh - airy and electronic.")

_s("Robot Respirator", noise="brown", env="airflow", voicing=0.25,
   base_freq=70.0, partials=_PAD, bright_base=200.0, bright_mod=1100.0,
   gain=0.4, description="Deep mechanical breathing, sci-fi respirator style.")

_s("Vocoder Breath", noise="pink", env="airflow", voicing=0.6,
   base_freq=110.0, partials=_CHORD, bright_base=400.0, bright_mod=1600.0,
   gain=0.31, description="Robotic, harmonised breath with a vocoder colour.")

_s("Cosmic Breath", noise="pink", env="airflow", voicing=0.8,
   base_freq=220.0, partials=_COSMIC, bright_base=800.0, bright_mod=2600.0,
   gain=0.42, description="A bright, weightless, otherworldly breath.")
