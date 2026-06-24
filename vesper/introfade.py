"""A gentle one-time launch fade-in for the window opacity.

Pure + testable. `intro_opacity(elapsed, duration, floor)` returns a multiplier
that eases from *floor* up to 1.0 over *duration* seconds (smoothstep), then
stays at 1.0 forever after -- so the window arrives softly on launch and then
the normal opacity logic (Sleep dim / clock warmth / Sunrise) applies untouched.
It is a visual nicety, nothing more.
"""
from __future__ import annotations

INTRO_SECONDS = 1.1          # how long the launch fade-in lasts


def intro_opacity(elapsed, duration=INTRO_SECONDS, floor=0.0):
    """Multiplier in [floor, 1.0]; floor at t<=0, 1.0 once t>=duration, smooth between."""
    if elapsed >= duration:
        return 1.0
    if elapsed <= 0.0 or duration <= 0.0:
        return floor
    f = elapsed / duration
    eased = f * f * (3.0 - 2.0 * f)         # smoothstep
    return floor + (1.0 - floor) * eased
