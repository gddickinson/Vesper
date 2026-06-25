"""Loving-Kindness (Metta) -- a spoken guided meditation toward rest.

A gentle audio version of the classic loving-kindness (metta) practice: a few
soft, repeated good wishes -- *may you be safe, may you be happy, may you be
healthy, may you live with ease* -- offered first to yourself, then to someone
you love, to someone neutral, to someone difficult, and at last to all beings
everywhere.  The slow, repeated phrasing is the whole point: warmth practised on
purpose, which the research links to calmer mood, more positive feeling and an
easier settling at night.  A genuinely evidence-based practice, alongside
Autogenic Training / Body-Scan / PMR / NSDR / Hypnosis.

Pure data + a generator of narrator units (the same ``{text, pause, phase, kind}``
shape the storyteller uses); the shared soft sleep drift is reused from
:mod:`breathsim.hypnosis`.  Offline + testable.
"""
from __future__ import annotations

import random

NAME = "Loving-Kindness (Metta)"
AMBIENCE = "Singing Bowl"          # a warm, resonant heart-centred bed

_SETTLE = [
    "Let yourself settle now, lying back, comfortable and supported.",
    "Let your eyes close, and let the day grow quiet around you.",
    "Rest one hand, if you like, lightly over the centre of your chest.",
    "Feel the small warmth there, the gentle rise and fall beneath your hand.",
    "There is nothing to fix and no one to become -- only a little warmth to share.",
]

# The four classic wishes, offered in widening circles.  Each round repeats the
# same soft phrases, the way the practice asks, so the kindness has time to land.
_SELF = [
    "Begin with yourself, the one person who is always here.",
    "Quietly, inwardly, offer these gentle wishes, like a hand on your own heart.",
    "May I be safe.  May I be safe, and held, and at ease.",
    "May I be happy.  May my heart be light and untroubled.",
    "May I be healthy.  May my body rest and mend through the night.",
    "May I live with ease.  May the day's weight slip from my shoulders.",
    "Let the words settle, slow and warm, and simply mean them, softly.",
]
_LOVED = [
    "Now bring to mind someone you love, someone easy to care for.",
    "See their face, or simply sense them near, and let your warmth turn toward them.",
    "May you be safe.  May you be safe, and well, and at peace.",
    "May you be happy.  May your heart be light, wherever you are tonight.",
    "May you be healthy.  May you rest, and wake gently in the morning.",
    "May you live with ease.  May your way be soft and kind.",
    "Feel how the wishing warms you too, the two of you held in the same calm.",
]
_NEUTRAL = [
    "Now picture someone you barely know -- a face passed in the street, a quiet stranger.",
    "They have a whole life, hopes and tiredness much like your own.",
    "May you be safe.  May you, too, be safe, and sheltered, and well.",
    "May you be happy.  May some small good thing find you today.",
    "May you be healthy.  May you be eased of whatever you carry.",
    "May you live with ease.  May your night be gentle and your rest deep.",
    "Notice how the circle widens, and your heart with it, soft and open.",
]
_DIFFICULT = [
    "And now, only if it feels gentle, bring to mind someone you find difficult.",
    "No need to forgive or to fix anything -- just to wish them, lightly, well.",
    "May you be safe.  May you, too, be free from harm.",
    "May you be happy.  May whatever troubles you ease, a little, tonight.",
    "May you be peaceful.  May the hardness between us soften and rest.",
    "If it is too much, let them go, and return the warmth to your own heart.",
    "Either way, you are practising a kindness that asks nothing back.",
]
_ALL = [
    "Now let the warmth spread outward, with no edges at all.",
    "To everyone in this house, and the next, and the sleeping street beyond.",
    "To every tired traveller, every restless heart, every creature in the dark.",
    "May all beings be safe.  May all beings be happy.",
    "May all beings be healthy.  May all beings live with ease.",
    "The whole breathing world, held for a moment in the same quiet wish.",
    "And you, somewhere within it, warm and small and entirely at peace.",
]
_CLOSE = [
    "Let the words dissolve now, and only the warmth remain.",
    "There is nothing left to do, and nowhere at all to be.",
    "Rest in the kindness you have made, and let it hold you as you drift.",
]


def _u(text, pause, phase=None, kind="metta"):
    return {"text": text, "pause": pause, "phase": phase, "kind": kind}


def units(rng=None, guidance=True):
    """The full loving-kindness arc -- settle at the heart, then the widening
    circles (self, a loved one, a neutral person, a difficult one, all beings),
    a soft close -- then the shared endless drift into sleep.  ``guidance`` keeps
    a few breath-paced breaths near the start (dropped if false)."""
    rng = rng or random.Random()
    for line in _SETTLE:
        yield _u(line, 3400)
    if guidance:
        for _ in range(3):
            yield _u("Breathe in, gently...", 4000, phase="in", kind="guide")
            yield _u("and let it soften.", 6000, phase="out", kind="guide")
    for block in (_SELF, _LOVED, _NEUTRAL, _DIFFICULT, _ALL):
        for line in block:
            yield _u(line, 5000)
    for line in _CLOSE:
        yield _u(line, 5200)
    from . import hypnosis                       # reuse the shared soft sleep tail
    yield from hypnosis.drift_tail(rng)
