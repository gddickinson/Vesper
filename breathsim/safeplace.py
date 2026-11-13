"""A Safe and Peaceful Place -- a spoken guided-imagery meditation toward rest.

The classic relaxation technique of building and inhabiting an imagined peaceful
place, engaging one sense at a time -- what you see, hear, feel, and smell there --
until the body lets go and the mind has somewhere safe to rest.  Guided imagery
("safe place" / "special place" visualisation) is a classic relaxation technique
that many people find calming at bedtime, and it is distinct from the body
relaxation of Autogenic Training / Body-Scan / PMR, the breath of Yoga Nidra, and the
warmth of Loving-Kindness: here the listener *builds a place* and rests inside it.

Pure data + a generator of narrator units (the same ``{text, pause, phase, kind}``
shape the storyteller uses); the shared soft sleep drift is reused from
:mod:`breathsim.hypnosis`.  Offline + testable.
"""
from __future__ import annotations

import random

NAME = "A Safe and Peaceful Place"
AMBIENCE = "Forest Wind"           # a soft, open natural hush that fits any place

_SETTLE = [
    "Let yourself settle now, lying back, your weight sinking into the bed.",
    "Let your eyes close, and let your breathing slow all by itself.",
    "There is nowhere you need to be, and nothing you need to do.",
    "With each slow breath out, let a little more of the day drain away.",
    "We are going to visit a place that is entirely safe, and entirely yours.",
]

# Let the place choose itself -- no right answer, no need to see it sharply.
_CHOOSE = [
    "Let a peaceful place begin to form, softly, in your mind's eye.",
    "It can be somewhere you know and love, or somewhere you simply imagine.",
    "Perhaps a quiet beach, a warm cabin, a sunlit meadow, a room beside a fire.",
    "There is no right choice, so let the place choose itself, whatever feels safe.",
    "Do not strain to see it clearly -- just let it be there, the way a dream is there.",
    "This is your place, made only for you, and no one comes here unless you wish.",
]
_SEE = [
    "Begin to look around your peaceful place, slowly, in no hurry at all.",
    "Notice the light here -- soft and golden, or cool and silver, however it falls.",
    "Notice the colours, near and far, gentle and easy on your eyes.",
    "Let your gaze rest on something close by, and stay with it for a moment.",
    "Then drift out to the furthest edge of the place, its soft and quiet horizon.",
    "It is beautiful here, in an unhurried way, and it asks nothing of you.",
]
_HEAR = [
    "Now let the sounds of this place come to you, soft and far away.",
    "Perhaps water, or leaves, or a warm fire, or simply a deep and easy hush.",
    "There are no sharp sounds here, nothing sudden, nothing that could startle you.",
    "Listen to the nearest sound, and then to the wide silence underneath it.",
    "The quiet of this place settles over you like a soft, warm blanket.",
]
_FEEL = [
    "Feel the air of your place, its gentle warmth resting on your skin.",
    "Perhaps a soft breeze, or the heat of the sun, or the glow of a fire nearby.",
    "Feel what holds you here -- warm sand, soft grass, a deep chair, a bed of moss.",
    "It supports you completely, so every muscle can let go and grow heavy.",
    "In your mind, reach out and touch something near, and feel how real it is.",
]
# Scent + the heart of it: this place is safe, and nothing troubling can follow.
_BELONG = [
    "Breathe in, and notice the air of this place, its clean and gentle scent.",
    "Perhaps salt, or pine, or woodsmoke, or rain, or simply fresh open air.",
    "With every breath, this place fills you, and you sink more deeply into it.",
    "You belong here completely; you are safe here in a way nothing can undo.",
    "No worry can follow you in -- they all wait, small and far, outside the edge.",
    "Here there is only peace, and warmth, and you, exactly as you are.",
]
_REST = [
    "Now simply rest in your peaceful place, doing nothing, holding nothing.",
    "Know that this place is always here, and you may return any night you wish.",
    "Carry a small token of it with you -- a colour, a sound, a warmth -- as you go.",
    "Let the place soften at its edges now, and blur, and hold you as you drift.",
    "You are safe, and warm, and carried, and there is nothing left to do but rest.",
]


def _u(text, pause, phase=None, kind="imagery"):
    return {"text": text, "pause": pause, "phase": phase, "kind": kind}


def units(rng=None, guidance=True):
    """The full guided-imagery arc -- settle, let a safe place form, then move
    through sight, sound, touch and scent, settle into belonging, rest -- and then
    the shared endless drift into sleep.  ``guidance`` keeps a few breath-paced
    breaths near the start (dropped when false)."""
    rng = rng or random.Random()
    for line in _SETTLE:
        yield _u(line, 3600)
    if guidance:
        for _ in range(3):
            yield _u("Breathe in, slowly...", 4000, phase="in", kind="guide")
            yield _u("and let it go.", 6000, phase="out", kind="guide")
    for line in _CHOOSE:
        yield _u(line, 4800)
    for block in (_SEE, _HEAR, _FEEL, _BELONG):
        for line in block:
            yield _u(line, 5200)
    for line in _REST:
        yield _u(line, 5600)
    from . import hypnosis                       # reuse the shared soft sleep tail
    yield from hypnosis.drift_tail(rng)
