"""A gentle breathing-coach count cue: names the phase and counts through it.

Pure + testable. `cue(phase, phase_elapsed, phase_len)` returns the words to
show for the current breath phase, counting up the seconds within it -- e.g.
"Breathe in 3", "Hold 2", "Breathe out 2", "Rest 1". A zero-length phase (e.g.
no hold) returns "". It just narrates the pattern's timing -- no claims.
"""
from __future__ import annotations

_LABEL = {"inhale": "Breathe in", "hold_full": "Hold",
          "exhale": "Breathe out", "hold_empty": "Rest"}


def cue(phase, phase_elapsed, phase_len):
    if phase_len is None or phase_len <= 0.05:
        return ""
    label = _LABEL.get(phase)
    if not label:
        return ""
    n = int(max(0.0, phase_elapsed)) + 1          # 1-based count of the second you're in
    n = max(1, min(n, max(1, round(phase_len))))   # never exceed the phase length
    return f"{label} {n}"
