"""Pranayama / breathwork technique voices (realistic).

Registered on import (see the bottom of voices.py). These use the per-phase
``env="breath"`` mode so the inhale and exhale can have different character,
attack and loudness -- essential for techniques like breath of fire (forceful
exhale, passive inhale) and sitali (cooling hiss in, soft nose out).

Pair each with its matching pattern in the Pattern menu.
"""
from __future__ import annotations

from .voices import GROUP_TECHNIQUE, VoiceConfig, register


def _t(name, **kw):
    register(VoiceConfig(name, GROUP_TECHNIQUE, kind="vocal", env="breath", **kw))


# Breath of fire / kapalabhati: sharp forceful exhale, soft passive inhale.
_t("Breath of Fire", source="noise", vowel="nose", attack="explosive",
   attack_in="smooth", exhale_level=1.0, inhale_level=0.35, air=0.12,
   gain=0.70, description="Kapalabhati: rapid, sharp nasal exhales with passive "
                         "inhales. Use the Breath of Fire pattern.")

# Bhastrika / bellows: forceful BOTH directions, equal and strong.
_t("Bhastrika (Bellows)", source="noise", vowel="nose", attack="explosive",
   attack_in="explosive", exhale_level=1.0, inhale_level=0.9, air=0.12,
   gain=0.67, description="Forceful, equal bellows breaths in and out through "
                         "the nose. Pair with the Bhastrika pattern.")

# Tummo / inner fire: deep, full, warm and slightly forceful.
_t("Tummo (Inner Fire)", source="mix", voicing=0.18, vowel="throat",
   attack="smooth", attack_in="smooth", exhale_level=1.0, inhale_level=0.95,
   air=0.18, pitch=95.0, gain=0.41,
   description="Deep, warm vase-breathing for inner-fire practice. Pair with "
               "the Tummo pattern.")

# Wim Hof: deep, full, audible breaths both ways.
_t("Wim Hof Breath", source="noise", vowel="mouth_open", attack="smooth",
   attack_in="smooth", exhale_level=1.0, inhale_level=1.0, air=0.28,
   gain=0.23, description="Big, full, audible power-breaths. Pair with the Wim "
                         "Hof pattern; stop if you feel light-headed.")

# Sitali: cooling hiss inhale through curled tongue, soft nasal exhale.
_t("Sitali (Cooling)", source="noise", vowel="nose", vowel_in="sitali",
   attack="smooth", attack_in="smooth", exhale_level=0.7, inhale_level=1.0,
   air=0.1, gain=0.57, description="Cooling breath: a long tongue-hiss inhale, "
                                  "soft exhale through the nose.")
