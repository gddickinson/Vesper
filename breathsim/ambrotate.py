"""Ambience auto-rotate: slowly cycle through a few calm nature beds.

Pure + testable. `next_ambience(beds, elapsed, period)` returns which bed should
be active at a given session elapsed-time -- deterministic, wrapping, and
tolerant of an empty or single-bed list. The window crossfades to it via the
existing ambience crossfade every *period* seconds, so the soundscape gently
evolves over a long session instead of looping one bed. It just rotates the bed.
"""
from __future__ import annotations

DEFAULT_PERIOD = 360.0          # seconds per bed (~6 minutes)

# A curated set of calm, continuous GROUP_NATURE beds to cycle through.
BEDS = ["Ocean Waves", "Distant Surf (night)", "Gentle Rain", "Forest Wind",
        "Mountain Stream", "Night Crickets", "Soft Rainstorm"]


def next_ambience(beds, elapsed, period=DEFAULT_PERIOD):
    """The bed for *elapsed* seconds in: beds[(elapsed // period) % n]."""
    beds = [b for b in (beds or []) if b]
    if not beds:
        return None
    if period <= 0:
        return beds[0]
    idx = int(max(0.0, float(elapsed)) // period) % len(beds)
    return beds[idx]
