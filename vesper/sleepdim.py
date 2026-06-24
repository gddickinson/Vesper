"""The Sleep wind-down's dimming curve, deepened into a gentle 'lights out'.

Pure + testable. `sleep_dim(prog)` is the window-opacity for a Sleep session at
progress *prog* (0..1): below the knee it is exactly the established wind-down
dim (1 - 0.3*prog); past the knee it eases further with a smoothstep toward a
floor, so the screen settles toward near-dark as you fall asleep -- but never
fully off (clamped to *floor*, around 0.55). It is a gentle visual dim, not a
real power-off, and it is fully reversible (a fresh start / reset recomputes it).
"""
from __future__ import annotations


def sleep_dim(prog, knee=0.85, floor=0.55):
    prog = max(0.0, min(1.0, prog))
    base = 1.0 - 0.3 * prog                 # the established wind-down dim
    if prog <= knee or knee >= 1.0:
        return base
    k0 = 1.0 - 0.3 * knee                   # opacity at the knee (continuous join)
    frac = (prog - knee) / (1.0 - knee)
    eased = frac * frac * (3.0 - 2.0 * frac)
    return k0 + (floor - k0) * eased
