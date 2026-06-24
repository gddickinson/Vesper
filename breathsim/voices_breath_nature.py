"""Natural-sound breath voices: the breath *becomes* a soothing natural sound.

These are airflow-driven breath voices (``GROUP_BREATH``, ``kind="noise"``), so they
swell as you breathe in and out and fall silent on the holds -- the in-breath and
out-breath each take on a different character via ``exhale_mul`` (which brightens or
darkens the exhale) and the airflow-swept brightness (``bright_mod`` opens the filter
as the breath builds). Impressionistic, not field recordings: filtered coloured
noise shaped to *evoke* tides, rain, wind, fire, snow and a vast cosmic wind.

Imported by voices.py so each registers into the shared registry. Gains are
calibrated to ~0.7 peak (see SESSION_LOG / the calibration in this round).
"""
from __future__ import annotations

from .voices import GROUP_BREATH, VoiceConfig, register


def _b(name, desc, **kw):
    kw.setdefault("group", GROUP_BREATH)
    return register(VoiceConfig(name=name, description=desc, kind="noise", **kw))


# Ocean: a tide rolling in (the breath opens into a swelling roll) and drawing back
# out brighter, hissing through wet pebbles and foam.
_b("Tide & Pebbles",
   "An ocean tide: the in-breath rolls in and swells, the out-breath draws back, "
   "hissing bright through wet pebbles.",
   noise="pink", filt=("bandpass", 520.0, 1.1), bright_base=800.0,
   bright_mod=2000.0, exhale_mul=1.12, gain=0.389, width=0.5,
   pan_rate=0.03, pan_depth=0.22)

# Deep, slow surf heard from far off: a soft dark sea hush, the out-breath sinking.
_b("Deep Surf",
   "Distant surf: a deep, dark sea hush that rises softly and sinks away on the "
   "out-breath.",
   noise="brown", filt=("lowpass", 540.0, 0.7), bright_base=470.0,
   bright_mod=950.0, exhale_mul=0.68, gain=0.157, width=0.45,
   pan_rate=0.02, pan_depth=0.18)

# Soft rain: a fine high patter that fills out a little on the out-breath.
_b("Spring Rain",
   "Soft, fine rain: a gentle high patter that fills out a little as you breathe "
   "out.",
   noise="white", filt=("bandpass", 2500.0, 0.6), bright_base=4200.0,
   bright_mod=3200.0, exhale_mul=1.05, gain=0.311, width=0.55,
   pan_rate=0.05, pan_depth=0.3)

# Wind moving through pines: gusts that rise on the in-breath and sigh away,
# drifting across the stereo field.
_b("Pine Wind",
   "Wind through the pines: a gust rises as you breathe in and sighs away as you "
   "breathe out, drifting from side to side.",
   noise="pink", filt=("bandpass", 850.0, 0.9), bright_base=1400.0,
   bright_mod=2600.0, exhale_mul=0.8, gain=0.327, width=0.6,
   pan_rate=0.06, pan_depth=0.4)

# Fire: a low warm roar that flares up as the breath fans it, then settles down.
_b("Ember Glow",
   "A warm fire: the in-breath fans a low roar brighter, the out-breath lets it "
   "settle back to a glow.",
   noise="brown", filt=("bandpass", 300.0, 0.85), bright_base=560.0,
   bright_mod=2200.0, exhale_mul=0.62, gain=0.394, width=0.3)

# A vast, airy cosmic wind: high, wide and slowly drifting - the breath of space.
_b("Cosmic Wind",
   "A vast, airy wind among the stars: high and wide, drifting slowly across a "
   "great dark space.",
   noise="white", filt=("bandpass", 3200.0, 0.5), bright_base=5200.0,
   bright_mod=4200.0, exhale_mul=0.9, gain=0.233, width=0.85,
   pan_rate=0.04, pan_depth=0.5)

# Snowfall: an almost-silent, soft high hush - breathing the still air of a snowy
# night.
_b("Snowfall Hush",
   "The hush of falling snow: a soft, almost-silent high stillness on the still "
   "air of a winter night.",
   noise="pink", filt=("bandpass", 1900.0, 0.5), bright_base=3000.0,
   bright_mod=1600.0, exhale_mul=0.9, gain=0.296, width=0.5,
   pan_rate=0.04, pan_depth=0.28)
