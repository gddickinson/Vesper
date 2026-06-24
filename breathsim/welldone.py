"""A brief, kind closing line shown when a real sit completes.

Pure + testable: `message(minutes, streak)` turns the finished sit's length and
the current streak into one short, warm, non-clinical sentence. The window shows
it (silently) in the status bar after a session; it just acknowledges a finished
sit -- no claims.
"""
from __future__ import annotations


def message(minutes, streak=0):
    """A gentle one-liner, or None for a too-short sit (< ~0.5 min)."""
    if minutes is None or minutes < 0.5:
        return None
    mm = max(1, int(round(minutes)))
    unit = "minute" if mm == 1 else "minutes"
    out = f"Session complete - {mm} {unit}."
    if streak and streak >= 2:
        out += f" {int(streak)} days in a row."
    out += " Be well."
    return out
