"""A Gentle Journey Downstream -- a spoken guided-imagery meditation toward rest.

A classic relaxation visualisation built on *being carried*: you lie back in a
small boat on a calm, slow river and let the current take you, with nothing to
steer, nothing to reach for, and nothing to do but watch the soft banks slip by
and let go.  Its theme is **letting go of effort and control** -- the water does
the work -- which makes it distinct from the *static* "Safe and Peaceful Place",
the body relaxation of Autogenic Training / Body-Scan / PMR, and the breath of
Yoga Nidra: here the listener is gently *moved*, and surrenders the steering.

Pure data + a generator of narrator units (the same ``{text, pause, phase, kind}``
shape the storyteller uses); the shared soft sleep drift is reused from
:mod:`breathsim.hypnosis`.  Offline + testable.
"""
from __future__ import annotations

import random

NAME = "A Gentle Journey Downstream"
AMBIENCE = "Mountain Stream"        # the calm, ever-present voice of the river

_SETTLE = [
    "Let yourself settle now, lying back, your weight sinking into the bed.",
    "Let your eyes close, and let your breathing slow all by itself.",
    "There is nowhere you need to be tonight, and nothing you need to do.",
    "With each slow breath out, let a little more of the day drain quietly away.",
    "We are going to take a slow journey down a calm river, and let it carry you.",
]

# Step into the boat: the start of letting something else hold you.
_EMBARK = [
    "Picture a wide, slow river at dusk, its surface smooth and softly glowing.",
    "At the bank, a small wooden boat waits for you, lined with soft blankets.",
    "You step in gently and lie back, and the boat holds you without a sound.",
    "Someone unties the rope for you, so there is nothing for you to arrange.",
    "With the faintest push, the boat slips out onto the open water.",
    "You do not need to row, or steer, or decide; the river will do all of that.",
]
# The heart of it: the current carries you, and you let go of effort.
_DRIFT = [
    "The current takes the boat now, slow and certain, and begins to carry you down.",
    "You feel a gentle, steady movement, smooth as a long breath, going only one way.",
    "There are no oars to pull and no wheel to hold, so your hands simply rest.",
    "Let your whole body grow heavy in the boat, carried along without any effort.",
    "Wherever the river goes, you go; you can trust it completely to hold your way.",
    "Each time you breathe out, you sink a little deeper into the soft, moving boat.",
]
# Watching the world pass, with nothing to reach for.
_BANKS = [
    "The soft banks begin to slip slowly by, and you simply watch them pass.",
    "Tall reeds lean and nod at the water's edge, and willows trail their leaves.",
    "A quiet meadow drifts past, then a still pool, then a low and sleeping field.",
    "You see a heron standing in the shallows, perfectly calm, and then it is behind you.",
    "Nothing on the banks asks anything of you; it is all simply there, and then gone.",
    "There is no need to hold on to any of it; the river carries you gently onward.",
]
# Letting go: set down whatever you are still carrying.
_LETGO = [
    "If you are still holding anything tonight, you can let the river take it now.",
    "Picture setting each small worry on the water, like a leaf, beside the boat.",
    "Watch it float for a moment, then fall slowly behind you, growing small and far.",
    "One by one, let them go onto the current, until your hands and chest feel light.",
    "The river carries them away downstream so that you do not have to carry them at all.",
    "Lighter now, and lighter still, you sink more deeply into the drifting boat.",
]
# The river slows to stillness, and the journey eases to rest.
_REST = [
    "Slowly, the river begins to widen, and to slow, opening into a calm, dark lagoon.",
    "The banks fall away on either side, and the water grows smooth and very still.",
    "The boat eases to a gentle stop among soft reeds, rocking the faintest amount.",
    "You are held here on the quiet water, warm and safe, with the journey done.",
    "There is nothing more to travel toward, and nothing left to do but rest.",
    "You may return to this river any night you wish, and let it carry you again.",
]


def _u(text, pause, phase=None, kind="imagery"):
    return {"text": text, "pause": pause, "phase": phase, "kind": kind}


def units(rng=None, guidance=True):
    """The full guided-journey arc -- settle, step into the boat, drift on the
    current, watch the banks pass, let your worries go onto the water, ease to
    rest -- and then the shared endless drift into sleep.  ``guidance`` keeps a
    few breath-paced breaths near the start (dropped when false)."""
    rng = rng or random.Random()
    for line in _SETTLE:
        yield _u(line, 3600)
    if guidance:
        for _ in range(3):
            yield _u("Breathe in, slowly...", 4000, phase="in", kind="guide")
            yield _u("and let it go.", 6000, phase="out", kind="guide")
    for line in _EMBARK:
        yield _u(line, 4800)
    for block in (_DRIFT, _BANKS, _LETGO):
        for line in block:
            yield _u(line, 5200)
    for line in _REST:
        yield _u(line, 5600)
    from . import hypnosis                       # reuse the shared soft sleep tail
    yield from hypnosis.drift_tail(rng)
