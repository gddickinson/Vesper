"""Vocalist / singer exercises -- for warm-ups, training and calibration.

Registered into the shared registry on import (see the bottom of voices.py).
These combine with the Voice Body personas too, so you can practise a female
siren, a child's scale, a deep-male sustained tone, and so on.

Calibration tip: the sustained "Sss/Shh/Fff" hisses and the steady Reference
Tone hold a constant level on the exhale, which makes them handy references for
checking breath support and setting playback volume.
"""
from __future__ import annotations

from .voices import GROUP_EXERCISE, VoiceConfig, register


def _v(name, **kw):
    register(VoiceConfig(name, GROUP_EXERCISE, kind="vocal", **kw))


# --- breath-control hisses (steady airflow -> great for calibration) -------

_v("Sustained Sss", source="noise", vowel="sss", env="exhale", gain=0.70,
   description="Even hissing 'sss' for breath-support practice.")

_v("Sustained Shh", source="noise", vowel="shh", env="exhale", gain=0.35,
   description="Steady 'shh' airflow exercise.")

_v("Sustained Fff", source="noise", vowel="fff", env="exhale", gain=0.35,
   description="Soft 'fff' for gentle, controlled exhalation.")


# --- sirens / glides -------------------------------------------------------

_v("Siren (Lip Trill)", source="mix", voicing=0.6, vowel="mouth_slight",
   env="exhale", pitch=110.0, glide_shape="updown", pitch_glide=12.0,
   am_rate=28.0, am_depth=0.85, air=0.15, gain=0.48,
   description="Lip-trill siren gliding up an octave and back.")

_v("Siren (Ng / Ee)", source="buzz", voicing=1.0, vowel="ee", env="exhale",
   pitch=130.0, glide_shape="updown", pitch_glide=12.0, gain=1.73,
   description="Voiced siren on 'ee' for smooth range connection.")


# --- tone / support exercises ----------------------------------------------

_v("Messa di Voce (Ah)", source="buzz", voicing=1.0, vowel="ah", env="exhale",
   attack="swell", pitch=130.0, vibrato_rate=5.0, vibrato_depth=0.008,
   gain=2.19, description="Crescendo then decrescendo on one sustained note.")

_v("Staccato Ha-Ha", source="mix", voicing=0.7, vowel="ah", env="exhale",
   pitch=130.0, am_rate=3.5, am_depth=1.0, air=0.15, gain=0.60,
   description="Diaphragm staccato 'ha-ha-ha' on the out-breath.")

_v("Straw Phonation (Oo)", source="buzz", voicing=1.0, vowel="oo", env="exhale",
   pitch=120.0, vibrato_rate=4.0, vibrato_depth=0.004, gain=2.11,
   description="Gentle semi-occluded 'oo' (straw/SOVT) warm-up.")


# --- pitch patterns --------------------------------------------------------

_v("Major Scale (Ah)", source="buzz", voicing=1.0, vowel="ah", env="exhale",
   pitch=110.0, glide_shape="scale_up", vibrato_rate=4.0, vibrato_depth=0.005,
   gain=2.05, description="Walk up a major scale across the exhale.")

_v("Arpeggio (Ah)", source="buzz", voicing=1.0, vowel="ah", env="exhale",
   pitch=110.0, glide_shape="arp_up", vibrato_rate=4.0, vibrato_depth=0.005,
   gain=2.05, description="Major arpeggio (do-mi-so-do) up and back.")

_v("Reference Tone (A)", source="buzz", voicing=1.0, vowel="ah", env="exhale",
   pitch=110.0, gain=2.11,
   description="Steady A2 (110 Hz) tone, no vibrato - a tuning/calibration "
               "reference (raises with the Voice Body).")
