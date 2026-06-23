"""Formant tables and formant-filter construction for vocal synthesis.

A vowel/breath colour is a set of resonances ``(centre Hz, bandwidth Hz,
gain)``. Running a source (glottal buzz and/or aspiration noise) through a
parallel bank of bandpass resonators at these frequencies imposes the vowel,
exactly as the human vocal tract does.

Vowel formants are approximate adult values; breath shapes use wider
bandwidths (lower Q) to stay breathy rather than tonal. Nose vs mouth and
"mouth open amount" are captured by which shape is chosen.
"""
from __future__ import annotations

from . import dsp

# Sung/spoken vowels: (F1, F2, F3) with narrow bandwidths -> clear pitch.
VOWELS = {
    "ah": [(700, 110, 1.0), (1220, 90, 0.5), (2600, 120, 0.18)],
    "eh": [(560, 90, 1.0), (1700, 100, 0.5), (2500, 120, 0.2)],
    "ee": [(300, 70, 1.0), (2300, 110, 0.5), (3000, 130, 0.2)],
    "oh": [(460, 80, 1.0), (800, 90, 0.5), (2600, 120, 0.14)],
    "oo": [(320, 70, 1.0), (800, 90, 0.4), (2240, 120, 0.1)],
    "uh": [(500, 90, 1.0), (1350, 100, 0.45), (2500, 120, 0.16)],
    "om": [(300, 80, 1.0), (700, 100, 0.55), (1100, 110, 0.3)],   # nasal-ish
    "mm": [(250, 80, 1.0), (1100, 130, 0.22), (2400, 160, 0.08)],  # hum
    # Singing vowels add a "singer's formant" cluster near 2.9 kHz for ring.
    "ah_sing": [(700, 100, 1.0), (1220, 90, 0.55), (2600, 110, 0.3),
                (2950, 110, 0.4)],
    "oh_sing": [(460, 80, 1.0), (800, 90, 0.55), (2600, 110, 0.22),
                (2950, 120, 0.35)],
}

# Breath / whisper colours: wide bandwidths keep them airy, not pitched.
BREATH_SHAPES = {
    "nose": [(1100, 260, 1.0), (2200, 420, 0.4)],          # narrow nasal hiss
    "mouth_slight": [(520, 320, 1.0), (1500, 520, 0.5)],   # slightly open
    "mouth_open": [(760, 360, 1.0), (1180, 420, 0.6),      # open "haa" breath
                   (2600, 520, 0.22)],
    "pursed": [(2200, 520, 1.0), (3600, 700, 0.4)],        # bright pursed lips
    "throat": [(560, 130, 1.0), (1000, 220, 0.4)],         # Ujjayi ocean throat
    # Fricatives for singers' breath-control / calibration exercises.
    "sss": [(6500, 900, 1.0), (8500, 1400, 0.45)],         # bright sibilant
    "shh": [(2400, 1000, 1.0), (3800, 1300, 0.6)],         # broad "shh"
    "fff": [(1700, 1100, 1.0), (4000, 1600, 0.35)],        # soft "fff"
    "sitali": [(4200, 600, 1.0), (6000, 900, 0.4)],        # cooling tongue hiss
    "th": [(1700, 900, 1.0), (4000, 1500, 0.3)],           # dental fricative
    # consonant onsets (nasal murmurs, stop bursts, approximant targets)
    "nas_m": [(250, 80, 1.0), (1100, 160, 0.25)],          # labial nasal
    "nas_n": [(250, 80, 1.0), (1700, 180, 0.25)],          # alveolar nasal
    "nas_ng": [(250, 80, 1.0), (2300, 220, 0.2)],          # velar nasal
    "burst_p": [(700, 500, 1.0)],                          # diffuse low burst
    "burst_t": [(3600, 900, 1.0)],                         # high burst
    "burst_k": [(1700, 500, 1.0), (2300, 600, 0.7)],       # compact mid burst
    "appr_l": [(360, 90, 1.0), (1300, 160, 0.5), (2700, 220, 0.3)],
    "appr_r": [(350, 90, 1.0), (1050, 130, 0.5), (1600, 160, 0.5)],
    "appr_w": [(300, 90, 1.0), (720, 110, 0.4)],
    "appr_y": [(280, 90, 1.0), (2200, 160, 0.5)],
}

_ALL = {**VOWELS, **BREATH_SHAPES}


def shape_names():
    return list(_ALL.keys())


def build_formants(sr: int, key: str, scale: float = 1.0):
    """Return ``(Biquad, gain)`` resonators for *key*, formants scaled by
    *scale* (vocal-tract length: <1 lengthens/lowers, >1 shortens/raises)."""
    table = _ALL.get(key)
    if not table:
        return []
    bank = []
    for freq, bw, gain in table:
        f = float(freq) * scale
        q = max(0.5, f / max(bw * scale, 20.0))
        b, a = dsp.bandpass(sr, f, q)
        bank.append((dsp.Biquad(b, a), float(gain)))
    return bank
