"""'Tonight's pick': choose a bedtime lecture at random, gently avoiding repeats.

Pure + testable: `pick(names, recent, rng)` returns a name from *names*, avoiding
those in *recent* when it can, and is deterministic when given a seeded rng. It
just picks a lecture at random -- no claims.
"""
from __future__ import annotations

import random


def pick(names, recent=(), rng=None):
    """A random name from *names*, preferring one not in *recent*.

    Falls back to the full list if every name is recent; returns None if there
    are no names at all. Deterministic when *rng* is a seeded random.Random."""
    pool = [n for n in (names or []) if n]
    if not pool:
        return None
    rng = rng or random.Random()
    fresh = [n for n in pool if n not in set(recent or ())]
    return rng.choice(fresh or pool)


def pick_any(lectures, extras, recent=(), rng=None, extra_chance=0.34):
    """Pick a random bedtime experience across the WHOLE storyteller library -- a
    lecture, or (about *extra_chance* of the time) one of the *extras* (the small,
    special set of guided sessions + poetry).

    The bias keeps those ~20 sessions/poems from being drowned out by the hundreds
    of lectures, so 'Surprise me' actually surfaces them once in a while. Avoids
    *recent* like :func:`pick`, deterministic with a seeded *rng*, falls back
    across pools, and returns None only if both are empty."""
    rng = rng or random.Random()
    lec = [n for n in (lectures or []) if n]
    ext = [n for n in (extras or []) if n]
    if ext and (not lec or rng.random() < extra_chance):
        return pick(ext, recent, rng) or pick(lec, recent, rng)
    return pick(lec, recent, rng) or pick(ext, recent, rng)
