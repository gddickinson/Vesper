"""Human-voice voices: the full range of breath and vocal sounds.

Registered into the shared registry on import (see the bottom of voices.py).
All use ``kind="vocal"`` and are rendered by :class:`breathsim.vocal.VocalTrack`.
Gains are calibrated so every voice peaks at a similar, headroom-safe level.
"""
from __future__ import annotations

from .voices import GROUP_VOCAL, VoiceConfig, register


def _v(name, **kw):
    register(VoiceConfig(name, GROUP_VOCAL, kind="vocal", **kw))


# --- breaths: nose / mouth, varying openness -------------------------------

_v("Nose Breath", source="noise", vowel="nose", env="airflow", air=0.15,
   gain=0.43, description="Quiet breathing in and out through the nose.")

_v("Mouth Breath (soft)", source="noise", vowel="mouth_slight", env="airflow",
   air=0.2, gain=0.27,
   description="Relaxed breathing through a slightly open mouth.")

_v("Mouth Breath (open)", source="noise", vowel="mouth_open", env="airflow",
   air=0.25, gain=0.26,
   description="Full open-mouthed breath, warm and audible.")

_v("Pursed-Lip Exhale", source="noise", vowel="pursed", env="exhale", air=0.1,
   gain=0.45, description="A long, narrow pursed-lip exhale.")

_v("Haa Breath (warm)", source="mix", voicing=0.3, vowel="ah", env="exhale",
   pitch=115.0, pitch_glide=-2.0, air=0.35, gain=0.30,
   description="The warm 'haa' breath, like fogging up a mirror.")

_v("Ujjayi Throat", source="noise", vowel="throat", env="airflow", air=0.1,
   gain=0.46, description="Whispered ocean-throat breath, in and out.")


# --- sighs -----------------------------------------------------------------

_v("Gentle Sigh", source="mix", voicing=0.4, vowel="uh", env="exhale",
   pitch=200.0, pitch_glide=-5.0, air=0.35, vibrato_rate=5.0,
   vibrato_depth=0.006, gain=0.32,
   description="A soft, breathy sigh that drifts downward.")

_v("Deep Sigh (relief)", source="mix", voicing=0.5, vowel="ah", env="exhale",
   pitch=130.0, pitch_glide=-7.0, air=0.3, gain=0.34,
   description="A long sigh of relief on a falling pitch.")


# --- explosive / forceful --------------------------------------------------

_v("Explosive Exhale", source="noise", vowel="mouth_open", env="exhale",
   attack="explosive", air=0.2, gain=0.39,
   description="A sharp, forceful burst of breath outward.")

_v("Sharp Sniff (in)", source="noise", vowel="nose", env="inhale",
   attack="explosive", air=0.15, gain=0.51,
   description="A quick, sharp sniff inward.")

_v("Forceful Ha", source="mix", voicing=0.4, vowel="ah", env="exhale",
   attack="explosive", pitch=150.0, air=0.3, gain=0.42,
   description="A punchy voiced 'HA!' on the out-breath.")


# --- vowel intonations / chants --------------------------------------------

_v("Chant: Ah", source="buzz", voicing=1.0, vowel="ah", env="exhale",
   pitch=130.0, vibrato_rate=5.0, vibrato_depth=0.008, gain=2.19,
   description="Sustained 'aah' toning on the exhale.")

_v("Chant: Oo", source="buzz", voicing=1.0, vowel="oo", env="exhale",
   pitch=120.0, vibrato_rate=5.0, vibrato_depth=0.008, gain=2.10,
   description="Sustained 'ooo' toning on the exhale.")

_v("Chant: Ee", source="buzz", voicing=1.0, vowel="ee", env="exhale",
   pitch=140.0, vibrato_rate=5.0, vibrato_depth=0.008, gain=1.69,
   description="Sustained 'eee' toning on the exhale.")

_v("Chant: Oh", source="buzz", voicing=1.0, vowel="oh", env="exhale",
   pitch=125.0, vibrato_rate=5.0, vibrato_depth=0.008, gain=2.05,
   description="Sustained 'ooh' toning on the exhale.")

_v("Chant: Om", source="mix", voicing=0.92, vowel="om", env="exhale",
   pitch=120.0, pitch_glide=-1.0, vibrato_rate=5.0, vibrato_depth=0.006,
   air=0.05, gain=1.05, description="The 'OM' / 'AUM' chant with a nasal close.")

_v("Hum (Mmm)", source="buzz", voicing=1.0, vowel="mm", env="exhale",
   pitch=130.0, vibrato_rate=5.0, vibrato_depth=0.006, gain=1.58,
   description="A closed-mouth hum, bhramari 'bee breath' style.")


# --- other human noises ----------------------------------------------------

_v("Lip Trill (Brrr)", source="mix", voicing=0.6, vowel="mouth_slight",
   env="exhale", pitch=90.0, am_rate=28.0, am_depth=0.85, air=0.2, gain=0.40,
   description="A relaxing lip trill / 'brrr' on the out-breath.")
