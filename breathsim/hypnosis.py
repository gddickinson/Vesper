"""Sleep Hypnosis: a slow, permissive guided hypnosis script for sleep onset.

Evidence-grounded structure (the classic hypnotherapy arc, e.g. Cordi & Rasch,
2014, who found hypnotic suggestion can deepen slow-wave sleep): **induction**
(settle + slow breath + progressive head-to-toe relaxation) -> **deepening** (a
10->1 countdown and a gentle descent image, with long silences as deepeners) ->
**permissive sleep suggestions** -> **drift into sleep** (no re-alerting -- unlike
clinical hypnosis, a sleep script simply lets you go). Delivery is slow and
*permissive* ("let...", "you may notice...") rather than commanding, with long
pauses between lines.

Honest framing: this is guided relaxation + gentle suggestion. The evidence is
promising (strongest for people who are highly open to suggestion); it is a sleep
aid, not a cure. Delivered through the ordinary storyteller (narration + the
talking-head lip-sync + a steady ambience bed); surfaced as a Sleep option via
:mod:`breathsim.stories` (``story_units`` dispatches here by :data:`NAME`).
"""
from __future__ import annotations

import random

NAME = "Sleep Hypnosis"
AMBIENCE = "Soft Rainstorm"        # a steady, soft masking bed

_SETTLE = [
    "Let yourself get as comfortable as you can, and let your eyes gently close.",
    "There is nothing you need to do now, and nowhere you need to be.",
    "This is simply a time to let go, and to be carried gently down toward sleep.",
    "You stay in control the whole time; you can follow my voice, or let it drift "
    "into the background.",
    "Let the bed take your full weight, and let your body begin to soften.",
]

# Progressive relaxation, head to toe.
_RELAX = [
    "Let the muscles of your forehead smooth out, and the space between your brows "
    "grow soft.",
    "Let your eyes rest heavy, and your jaw loosen, your teeth a little apart.",
    "Let your shoulders drop, down and away from your ears.",
    "Feel your arms grow heavy, all the way to your hands and the tips of your "
    "fingers.",
    "Let your chest soften, each breath slower and quieter than the last.",
    "Let your belly rise and fall on its own, soft and easy.",
    "Feel your hips and your legs grow heavy, sinking into the bed.",
    "And let your feet grow warm and still, all the way to your toes.",
]

# Deepening countdown, 10 -> 1, permissive.
_COUNT = [
    "Ten. Letting go, drifting gently down.",
    "Nine. Heavier, and calmer, with every word.",
    "Eight. Softer and softer, nothing to hold on to.",
    "Seven. Sinking deeper, warm and safe.",
    "Six. Your thoughts slowing, growing quiet and dim.",
    "Five. Halfway down now, deeply at ease.",
    "Four. Heavier still, your whole body resting.",
    "Three. Drifting, the way a leaf settles to the ground.",
    "Two. Softer, and further away.",
    "One. All the way down, deeply, peacefully relaxed.",
]

_STAIRS = [
    "Picture a few soft steps leading gently downward, into deeper rest.",
    "With each step you take, you sink a little further, a little safer.",
    "Down, and down, each step warmer and quieter than the one before.",
    "And at the bottom, a place that is soft, and dim, and entirely your own.",
]

_SUGGEST = [
    "Here, there is nothing to solve, and nothing to carry.",
    "If a thought drifts by, let it float past like a cloud, and come back to the "
    "quiet.",
    "With every slow breath, sleep feels a little closer, and more inviting.",
    "Your body already knows how to sleep; you need only allow it.",
    "Let the warmth and the heaviness deepen, and let the quiet hold you.",
]

_DRIFT = [
    "There is nothing left to do now but rest.",
    "Let my voice fade softly into the background, like rain on a far-off roof.",
    "Drifting, sinking, softly letting go.",
    "Down, and down, into a deep and easy sleep.",
]

# An endless, sparse tail so the session never stops abruptly -- it simply thins
# out into long silences as the wind-down fades the volume away.
_TAIL = [
    "Deeper, and softer, and further away.",
    "Resting now, completely at ease.",
    "Letting go, drifting down into sleep.",
    "Soft, and warm, and heavy, and still.",
    "Nothing to do now, but drift.",
]


def _u(text, pause, phase=None, kind="hypnosis"):
    return {"text": text, "pause": pause, "phase": phase, "kind": kind}


def units(rng=None, guidance=True):
    """The full hypnosis arc, then an endless soft drift tail. ``guidance`` keeps
    the breath-cued induction breaths (dropped if false)."""
    rng = rng or random.Random()
    for line in _SETTLE:
        yield _u(line, 3200)
    yield _u("Let your breathing slow, all on its own.", 2600)
    if guidance:
        for _ in range(4):                       # a few breath-paced breaths
            yield _u("Breathe in, slowly...", 4000, phase="in", kind="guide")
            yield _u("and let it all go.", 6500, phase="out", kind="guide")
    yield _u("Now let a wave of softness move slowly down through your body.", 3400)
    for line in _RELAX:
        yield _u(line, 3800)
    yield _u("Your whole body, heavy and warm, sinking gently down.", 4200)
    yield _u("In a moment I'll count from ten down to one, and with each number "
             "you can drift twice as deep.", 3600)
    for line in _COUNT:
        yield _u(line, 5400)
    for line in _STAIRS:
        yield _u(line, 4400)
    for line in _SUGGEST:
        yield _u(line, 4400)
    for line in _DRIFT:
        yield _u(line, 5200)
    while True:                                  # endless, ever-sparser drift
        yield _u(rng.choice(_TAIL), rng.randint(9000, 14000))
