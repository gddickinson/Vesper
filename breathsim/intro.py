"""A brief, gentle "settle in" lead-in shown as the first session begins.

Pure + testable. ``schedule(cycle_seconds, lines=None)`` lays a few calm
preparatory lines across roughly the first breath cycle, so the very first
inhale isn't abrupt; ``line_at(sched, t)`` returns the line to show at elapsed
time *t* (``None`` once the lead-in is over) and ``duration(sched)`` its length.
It's just a gentle on-screen lead-in -- no audio, no timing change, no claims.
"""
from __future__ import annotations

DEFAULT_LINES = [
    "Settle in.",
    "Find a comfortable position.",
    "Let your shoulders soften.",
    "We'll begin together.",
]


def schedule(cycle_seconds, lines=None, min_total=8.0, max_total=12.0):
    """[(start, end, text), ...] spanning ~one breath cycle (clamped to a calm,
    readable span). Each line shows in turn; the last ends as the lead-in does.
    Pure -- given only the breath-cycle length and the lines to show."""
    lines = list(DEFAULT_LINES if lines is None else lines)
    n = len(lines)
    if n == 0:
        return []
    try:
        cyc = float(cycle_seconds)
    except (TypeError, ValueError):
        cyc = 0.0
    total = min(max(cyc, float(min_total)), float(max_total))
    step = total / n
    return [(round(i * step, 3), round((i + 1) * step, 3), lines[i])
            for i in range(n)]


def duration(sched):
    """Total length of the lead-in (0.0 when there is none)."""
    return sched[-1][1] if sched else 0.0


def line_at(sched, t):
    """The lead-in line active at elapsed time *t*, or ``None`` once it's done."""
    if not sched:
        return None
    if t < 0:
        return sched[0][2]
    for start, end, text in sched:
        if start <= t < end:
            return text
    return None
