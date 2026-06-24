"""Pick a random bedtime lecture from one branch (category), avoiding repeats.

Pure + testable. `pick_in_branch(category, recent, rng)` looks up the lecture
names in *category* and defers to :func:`breathsim.tonight.pick` to choose one,
preferring a name not in *recent* and deterministic when given a seeded *rng*.
It just picks a lecture at random within a theme -- no claims.
"""
from __future__ import annotations

from . import lectures, tonight


def names_in_branch(category):
    """The lecture names in *category*, or an empty list for an unknown branch."""
    if not category:
        return []
    try:
        return list(lectures.names(category))
    except Exception:
        return []


def pick_in_branch(category, recent=(), rng=None):
    """A random lecture name from *category*, avoiding *recent* when possible.

    Returns None when the branch is empty or unknown. Deterministic when *rng*
    is a seeded ``random.Random``."""
    return tonight.pick(names_in_branch(category), recent, rng)
