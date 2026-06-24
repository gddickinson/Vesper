"""Curated metadata for the XTTS-v2 studio voices, so the picker can group them
and show gender + timbre + a quality star instead of bare names.

Gender + timbre were derived by **measuring** a rendered line from every speaker
(median F0 -> gender, spectral centroid -> warm/clear/bright); a few obvious
pitch-tracker octave slips were hand-corrected against the clearly-gendered voice.
XTTS studio voices speak fairly neutral English, so we label gender + timbre
(honest + measurable) rather than claim a specific regional accent. ``recommended``
marks the cleanest, most natural ones (shown starred). Pure data; no imports.
"""
from __future__ import annotations

# (speaker, gender 'f'/'m', timbre, recommended)
_VOICES = [
    ("Daisy Studious", "f", "warm", True),
    ("Gracie Wise", "f", "warm", True),
    ("Alison Dietlinde", "f", "clear", True),
    ("Claribel Dervla", "f", "warm", True),
    ("Sofia Hellen", "f", "bright", True),
    ("Tammie Ema", "f", "warm", False),
    ("Annmarie Nele", "f", "clear", False),
    ("Alexandra Hisakawa", "f", "clear", False),
    ("Brenda Stern", "f", "warm", False),
    ("Ana Florence", "f", "bright", False),
    ("Henriette Usha", "f", "bright", False),
    ("Tanja Adelina", "f", "warm", False),
    ("Damien Black", "m", "deep", True),
    ("Aaron Dreschner", "m", "deep", True),
    ("Royston Min", "m", "clear", True),
    ("Dionisio Schuyler", "m", "deep", False),
    ("Viktor Eka", "m", "warm", False),
    ("Luis Moray", "m", "warm", False),
    ("Damjan Chapman", "m", "deep", False),
    ("Kumar Dahl", "m", "warm", False),
    ("Marcos Rudaski", "m", "warm", False),
    ("Ludvig Milivoj", "m", "clear", False),
]

_META = {n: (g, t, r) for n, g, t, r in _VOICES}
_GENDER_WORD = {"f": "female", "m": "male"}


def curated():
    """Curated speaker names, female-first then male (picker order)."""
    return [n for n, *_ in _VOICES]


def known(name):
    return name in _META


def gender(name):
    return _META.get(name, ("?",))[0]


def is_recommended(name):
    m = _META.get(name)
    return bool(m and m[2])


def label(name):
    """e.g. ``Daisy Studious - warm female``; bare name if uncurated."""
    m = _META.get(name)
    if not m:
        return name
    g, timbre, _ = m
    return f"{name} - {timbre} {_GENDER_WORD.get(g, '')}".rstrip()


def by_gender():
    """``{'f': [names], 'm': [names]}`` over the curated set, in picker order."""
    out = {"f": [], "m": []}
    for n, g, *_ in _VOICES:
        out.setdefault(g, []).append(n)
    return out
