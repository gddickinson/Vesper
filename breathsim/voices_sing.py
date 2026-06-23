"""Realistic singing / chanting voices.

Registered on import (see the bottom of voices.py). These build on the chant
voices with a singer's-formant vowel (the ~2.9 kHz 'ring'), fuller vibrato and
a gentle pitch-glide onset for a more natural, sung quality. Combine with the
Voice Body personas for male/female/child singers, and with the Morph and
session controls for evolving vocal pieces.
"""
from __future__ import annotations

from .voices import GROUP_SING, VoiceConfig, register


def _s(name, **kw):
    register(VoiceConfig(name, GROUP_SING, kind="vocal", source="buzz",
                         voicing=1.0, env="exhale", **kw))


_s("Sing: Ah (vibrato)", vowel="ah_sing", pitch=130.0, vibrato_rate=5.5,
   vibrato_depth=0.013, pitch_glide=0.5, gain=2.17,
   description="A warm sustained 'ah' with singer's ring and natural vibrato.")

_s("Sing: Oh (vibrato)", vowel="oh_sing", pitch=120.0, vibrato_rate=5.5,
   vibrato_depth=0.012, pitch_glide=0.5, gain=1.87,
   description="A rounded sung 'oh' with vibrato.")

_s("Operatic Ah", vowel="ah_sing", pitch=150.0, vibrato_rate=6.0,
   vibrato_depth=0.02, air=0.04, gain=1.48,
   description="A bright, ringing operatic tone with strong vibrato.")

_s("Soft Croon (Oo)", vowel="oo", pitch=125.0, vibrato_rate=4.5,
   vibrato_depth=0.008, air=0.08, gain=1.09,
   description="A gentle, breathy crooning 'oo'.")

_s("Gregorian Aah", vowel="ah", pitch=110.0, vibrato_rate=3.5,
   vibrato_depth=0.004, gain=2.10,
   description="A plain, steady chant tone with minimal vibrato.")
