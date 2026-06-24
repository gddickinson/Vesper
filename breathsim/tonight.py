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
