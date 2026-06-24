"""Clock-aware theming helpers: a gentle time-of-day warmth + a launch mode hint.

Pure functions of the hour (0..23) so they are easy to test. The window applies a
small warm/dim overlay that is neutral by day and a little warmer and dimmer in the
evening and overnight (kinder on melatonin), and - only when no mode has been saved
- opens in a mode that suits the time of day.
"""
from __future__ import annotations

import datetime as _dt

_MAX = 0.22                      # cap the night warmth (kept subtle)


def now_hour() -> int:
    return _dt.datetime.now().hour


def clock_warm_for_hour(h: int) -> float:
    """Warm-overlay amount 0..~0.22: 0 by day, ramping up in the evening, full
    overnight, easing back before dawn."""
    h = h % 24
    if 6 <= h < 18:
        return 0.0
    if 18 <= h < 22:
        return round(_MAX * (h - 17) / 4.0, 3)       # 18 -> 0.055 .. 21 -> 0.22
    if h >= 22 or h < 4:
        return _MAX
    return round(_MAX * (6 - h) / 2.0, 3)            # 4 -> 0.22, 5 -> 0.11


def quiet_cap(h: int) -> float:
    """An upper bound on output volume by the clock: 1.0 by day/evening, easing
    down to a gentle ~0.6 in the small hours so a late session is never jarring.
    Never above 1.0, never fully mutes. Pure (pass the hour to test)."""
    h = h % 24
    return {22: 0.9, 23: 0.8, 0: 0.6, 1: 0.6, 2: 0.6, 3: 0.6, 4: 0.6,
            5: 0.7, 6: 0.85}.get(h, 1.0)


def suggested_mode_for_hour(h: int) -> str:
    """A fitting mode to open in, by the clock (only used when none is saved)."""
    h = h % 24
    if h >= 22 or h < 6:
        return "Sleep"
    if 6 <= h < 9:
        return "Meditate"
    if 9 <= h < 12:
        return "Breathwork"
    if 12 <= h < 17:
        return "Meditate"
    return "Relax"                                   # late afternoon / evening
