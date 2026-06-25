"""Autogenic Training -- a spoken guided relaxation toward sleep.

A gentle audio version of Johannes Schultz's classic autogenic training (1932):
a sequence of soft, repeated self-suggestions that the body is **heavy**, then
**warm**, the heartbeat **calm**, the breathing **easy**, the belly **warm** and
the brow **cool** -- the six "standard exercises". The slow, repeated phrasing is
the point: it quietly trains the relaxation response, easing the body toward rest.
A genuinely evidence-based wind-down, alongside Body-Scan / PMR / NSDR / Hypnosis.

Pure data + a generator of narrator units (the same ``{text, pause, phase, kind}``
shape the storyteller uses); the shared soft sleep drift is reused from
:mod:`breathsim.hypnosis`. Offline + testable.
"""
from __future__ import annotations

import random

NAME = "Autogenic Training"
AMBIENCE = "Soft Rainstorm"        # a steady, soft masking bed

_SETTLE = [
    "Let yourself settle now, lying back, comfortable and supported.",
    "Let your eyes close, and let the day go quiet around you.",
    "There is nothing to make happen here -- only to let go, a little at a time.",
    "Each of these words is a small permission to soften and rest.",
]

# The six standard exercises. Each is repeated slowly, the way the practice asks,
# so the quiet suggestion has time to settle into the body.
_HEAVY = [
    "Bring your gentle attention to your right arm.",
    "Your right arm is heavy.  Heavy, and warm, and still.",
    "Your right arm is heavy.  Letting go, sinking down.",
    "And now your left arm is heavy.  Heavy and loose and at rest.",
    "Both arms, heavy.  Resting their full weight on the bed.",
    "Now your right leg is heavy.  And your left leg is heavy.",
    "Both legs, heavy.  Sinking softly down.",
    "Your arms and legs are heavy, all of them, warm and still.",
    "Your whole body is heavy now, held gently by the bed beneath you.",
]
_WARM = [
    "And as you rest, a soft warmth begins to spread.",
    "Your right arm is warm.  A gentle, easy warmth, as if held in sunlight.",
    "Your left arm is warm.  The warmth flows down, into your hands.",
    "Both arms, heavy and warm.  Soft and glowing and calm.",
    "Your legs are warm too, the warmth moving slowly down to your feet.",
    "A pleasant warmth fills your arms and legs, head to foot.",
    "Heavy, and warm, and wonderfully at ease.",
]
_HEART = [
    "Now let your attention rest, softly, near your heart.",
    "Your heartbeat is calm and regular.  Calm, and steady, and slow.",
    "There is no need to count it or change it -- only to notice how calm it is.",
    "Calm and regular, beating quietly beneath the warmth.",
    "With every beat, you sink a little deeper into rest.",
]
_BREATH = [
    "And now your breath, soft and slow, all on its own.",
    "It breathes you.  You do not have to do anything; the breath simply comes and goes.",
    "Calm and even, the gentle tide of your breathing.",
    "Each breath out lets you settle a little further down.",
    "Your breathing is calm.  It breathes you, slow and deep.",
]
_BELLY = [
    "Let a soft warmth gather in the centre of you, behind your belly.",
    "Your belly is warm.  A quiet, comfortable warmth, like a small sun within.",
    "Warm and soft and loose, the whole centre of you at ease.",
    "That warmth spreads outward, until your whole middle is calm and warm.",
]
_BROW = [
    "And your forehead is cool.  Cool and smooth and clear.",
    "A gentle coolness across your brow, easy and untroubled.",
    "Your face softens -- your jaw, your eyes, the space between your brows.",
    "Cool and clear above, warm and heavy below, and all of you at peace.",
]
_CLOSE = [
    "Heavy.  Warm.  Calm.  Easy.  Your whole body resting, deeply at ease.",
    "There is nothing left to do, and nowhere at all to be.",
    "You can let these quiet words go now, and simply drift.",
]


def _u(text, pause, phase=None, kind="autogenic"):
    return {"text": text, "pause": pause, "phase": phase, "kind": kind}


def units(rng=None, guidance=True):
    """The full autogenic arc -- settle, the six standard exercises, a soft close
    -- then the shared endless drift into sleep. ``guidance`` keeps a few
    breath-paced breaths near the start (dropped if false)."""
    rng = rng or random.Random()
    for line in _SETTLE:
        yield _u(line, 3400)
    if guidance:
        for _ in range(3):
            yield _u("Breathe in, slowly...", 4000, phase="in", kind="guide")
            yield _u("and let it go.", 6000, phase="out", kind="guide")
    for block in (_HEAVY, _WARM, _HEART, _BREATH, _BELLY, _BROW):
        for line in block:
            yield _u(line, 5000)
    for line in _CLOSE:
        yield _u(line, 5200)
    from . import hypnosis                       # reuse the shared soft sleep tail
    yield from hypnosis.drift_tail(rng)
