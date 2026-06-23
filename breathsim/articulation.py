"""Consonant articulation for sung syllables (Klatt-style onsets).

Each consonant is rendered as a short *onset* before the vowel:

* **stops** (p/t/k/b/d/g) -- a brief closure (silence) then an abrupt noise
  burst, shaped by place of articulation;
* **fricatives** (s/sh/f/th/v) -- band-limited noise turned on gradually;
* **nasals** (m/n/ng) -- a voiced low murmur with a place formant;
* **aspiration** (h) -- breathy, vowel-shaped noise;
* **approximants** (l/r/w/y) -- a brief voiced formant target gliding to the
  vowel.

This is approximate (formant synthesis, not recorded speech), but gives sung
syllables recognisable attacks. See :mod:`breathsim.vocal` for rendering.
"""
from __future__ import annotations

# kind: noise | voiced | aspirate     shape: burst | fric | murmur | glide | aspirate
# formant: a key in formants._ALL (None => use the following vowel, for h)
C = {
    # nasals
    "m": dict(kind="voiced", shape="murmur", formant="nas_m", dur=0.10, level=0.55),
    "n": dict(kind="voiced", shape="murmur", formant="nas_n", dur=0.09, level=0.55),
    "ng": dict(kind="voiced", shape="murmur", formant="nas_ng", dur=0.09, level=0.5),
    # fricatives
    "s": dict(kind="noise", shape="fric", formant="sss", dur=0.12, level=0.42),
    "sh": dict(kind="noise", shape="fric", formant="shh", dur=0.12, level=0.42),
    "f": dict(kind="noise", shape="fric", formant="fff", dur=0.10, level=0.4),
    "th": dict(kind="noise", shape="fric", formant="th", dur=0.09, level=0.35),
    "v": dict(kind="voiced", shape="murmur", formant="fff", dur=0.07, level=0.4),
    "h": dict(kind="aspirate", shape="aspirate", formant=None, dur=0.08, level=0.4),
    # stops (closure `pre` then burst)
    "p": dict(kind="noise", shape="burst", formant="burst_p", pre=0.03, dur=0.05,
              level=0.45),
    "t": dict(kind="noise", shape="burst", formant="burst_t", pre=0.03, dur=0.04,
              level=0.45),
    "k": dict(kind="noise", shape="burst", formant="burst_k", pre=0.03, dur=0.05,
              level=0.45),
    "b": dict(kind="noise", shape="burst", formant="burst_p", pre=0.02, dur=0.05,
              level=0.4),
    "d": dict(kind="noise", shape="burst", formant="burst_t", pre=0.02, dur=0.04,
              level=0.4),
    "g": dict(kind="noise", shape="burst", formant="burst_k", pre=0.02, dur=0.05,
              level=0.4),
    # approximants / liquids
    "l": dict(kind="voiced", shape="glide", formant="appr_l", dur=0.06, level=0.6),
    "r": dict(kind="voiced", shape="glide", formant="appr_r", dur=0.06, level=0.6),
    "w": dict(kind="voiced", shape="glide", formant="appr_w", dur=0.05, level=0.6),
    "y": dict(kind="voiced", shape="glide", formant="appr_y", dur=0.05, level=0.6),
}


def spec(consonant: str):
    return C.get(consonant)


def total_dur(consonant: str) -> float:
    s = C.get(consonant)
    if not s:
        return 0.0
    return s.get("pre", 0.0) + s["dur"]
