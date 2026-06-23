"""The Cat voice family (group "Cat").

Cat sounds you can pick like any other voice: a small cat's **breath**, a
contented **sigh**, a soft **meow**, and a steady **purr**. The sigh and meow are
gated to the out-breath (``env="exhale"``), so the cat answers each exhale; the
breath is airflow-driven (both phases); the purr is a steady bed. Registered into
the voices registry on import (see the bottom of voices.py). Gains are calibrated.
"""
from __future__ import annotations

from .voices import GROUP_CAT, VoiceConfig, register

register(VoiceConfig(
    "Cat Breath", GROUP_CAT, noise="pink",
    filt=("bandpass", 820.0, 1.1), bright_base=1600.0, bright_mod=1800.0,
    exhale_mul=0.8, gain=0.36, width=0.2,
    description="A small cat's soft, quick breathing."))

register(VoiceConfig(
    "Cat Sigh", GROUP_CAT, noise="pink", env="exhale",
    filt=("bandpass", 560.0, 0.8), bright_base=900.0, bright_mod=1500.0,
    attack="swell", gain=0.40, width=0.25,
    description="A soft, contented cat sigh on each out-breath."))

register(VoiceConfig(
    "Meow", GROUP_CAT, kind="vocal", env="exhale", source="mix", voicing=0.85,
    vowel="ee", vowel_to="oh", pitch=440.0, pitch_glide=4.0, glide_shape="updown",
    attack="smooth", air=0.15, n_harm=26, gain=0.70, width=0.2,
    description="The cat meows softly on each out-breath."))

register(VoiceConfig(
    "Cat Purr", GROUP_CAT, kind="texture", texture="purr", env="volume",
    floor=1.0, gain=0.18,
    description="A steady, soothing cat purr that rises and falls with the breath."))
