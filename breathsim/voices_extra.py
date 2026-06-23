"""Additional breaths, chants and singing voices (comprehensive expansion).

Registered on import (bottom of voices.py). Breaths and chants join the Human
Voice group; singing voices join the Singing group. Gains are calibrated.
"""
from __future__ import annotations

from .voices import GROUP_SING, GROUP_VOCAL, VoiceConfig, register


def _v(name, **kw):                       # breath / human voice
    register(VoiceConfig(name, GROUP_VOCAL, kind="vocal", **kw))


def _c(name, **kw):                       # sustained chant
    for k, v in dict(source="buzz", voicing=1.0, env="exhale",
                     vibrato_rate=5.0, vibrato_depth=0.008).items():
        kw.setdefault(k, v)
    register(VoiceConfig(name, GROUP_VOCAL, kind="vocal", **kw))


def _s(name, **kw):                       # singing voice
    for k, v in dict(source="buzz", voicing=1.0, env="exhale").items():
        kw.setdefault(k, v)
    register(VoiceConfig(name, GROUP_SING, kind="vocal", **kw))


# --- more breaths ----------------------------------------------------------

_v("Yawn", source="mix", voicing=0.4, vowel="ah", env="exhale", pitch=140.0,
   glide_shape="updown", pitch_glide=5.0, air=0.4, gain=0.28,
   description="A long, relaxing yawn.")

_v("Gasp (in)", source="mix", voicing=0.25, vowel="ah", env="inhale",
   attack="explosive", pitch=200.0, air=0.4, gain=0.38,
   description="A sharp, surprised intake of breath.")

_v("Pant", source="noise", vowel="mouth_open", env="airflow", air=0.3,
   gain=0.26, description="Quick, light panting (use a fast pattern).")

_v("Snore", source="mix", voicing=0.3, noise="brown", vowel="nose",
   env="inhale", am_rate=18.0, am_depth=0.7, pitch=70.0, air=0.3, gain=0.46,
   description="A rumbling snore on the inhale - playful for Sleep.")

_v("Sitkari (Teeth)", source="noise", vowel="sss", env="inhale", air=0.1,
   gain=0.62, description="A cooling hiss inhaled through the teeth.")

_v("Content Sigh", source="mix", voicing=0.35, vowel="uh", env="exhale",
   pitch=150.0, pitch_glide=-3.0, air=0.4, vibrato_rate=4.0,
   vibrato_depth=0.005, gain=0.25, description="A soft, contented sigh.")

_v("Shaky Breath", source="mix", voicing=0.2, vowel="ah", env="exhale",
   am_rate=8.0, am_depth=0.5, pitch=150.0, air=0.4, gain=0.31,
   description="A trembling, emotional exhale.")

_v("Muffled Breath", source="noise", noise="brown", vowel="mouth_slight",
   env="airflow", air=0.15, gain=0.40,
   description="A soft, dark breath - as if through a scarf.")


# --- more chants (incl. real vowel glides) ---------------------------------

_c("Chant: Eh", vowel="eh", pitch=130.0, gain=2.37,
   description="Sustained 'eh' toning.")

_c("Chant: Aum (glide)", source="mix", voicing=0.95, vowel="ah", vowel_to="mm",
   pitch=118.0, pitch_glide=-1.0, air=0.05, gain=1.21,
   description="A true AUM that opens on 'aah' and closes to 'mmm'.")

_c("Chant: Aa-Oo (glide)", vowel="ah", vowel_to="oo", pitch=125.0, gain=2.17,
   description="Toning that opens from 'ah' to 'oo'.")

_c("Chant: Ee-Ah (glide)", vowel="ee", vowel_to="ah", pitch=132.0, gain=2.0,
   description="Toning that brightens from 'ee' to 'ah'.")


# --- more singing ----------------------------------------------------------

_s("Falsetto Ah", vowel="ah_sing", pitch=260.0, n_harm=8, vibrato_rate=6.0,
   vibrato_depth=0.012, air=0.05, gain=1.23,
   description="A light, high falsetto tone.")

_s("Belt Eh", vowel="eh", pitch=180.0, vibrato_rate=5.5, vibrato_depth=0.015,
   gain=2.12, description="A strong, bright belted note.")

_s("Overtone Drone", vowel="ee", pitch=110.0, vibrato_rate=3.0,
   vibrato_depth=0.003, gain=1.93,
   description="A low drone with a ringing high overtone.")

_s("Lullaby Hum", vowel="mm", pitch=200.0, pitch_glide=-2.0, vibrato_rate=4.5,
   vibrato_depth=0.01, gain=1.86, description="A soft, descending hummed lullaby.")

_s("Mantra Drone", vowel="om", pitch=100.0, vibrato_rate=0.0,
   vibrato_depth=0.0, gain=1.57, description="A steady, low mantra drone.")

_s("Choir Ooh", vowel="oo", pitch=140.0, vibrato_rate=5.0, vibrato_depth=0.009,
   gain=1.88, description="A warm, open choral 'ooh'.")
