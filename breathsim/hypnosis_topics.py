"""Themed self-help sleep-hypnosis sessions (stress, confidence, focus...).

Each session reuses the same arc as :mod:`breathsim.hypnosis`
(induction -> deepening countdown -> permissive suggestions -> drift into sleep),
swapping only the **suggestion block** for a gentle, present/future-tense theme.
Because this is a *sleep* app, every theme is written to settle you and to wind
down -- even "confidence" or "focus" are framed as something that quietly takes
root overnight and is simply there for you tomorrow, never as alerting or
energising language. All suggestions are *permissive* ("you may notice...",
"you can let...") rather than commanding.

Honest framing: this is guided relaxation + gentle suggestion delivered as you
fall asleep. It is a soothing self-help aid, not therapy or a cure. Surfaced
through the ordinary storyteller (narration + lip-sync +
a steady masking bed); listed as Sleep options via :mod:`breathsim.stories`.
"""
from __future__ import annotations

import random

from . import hypnosis

_PREFIX = "Sleep Hypnosis: "

# Each: key NAME (without prefix) -> (ambience, [permissive suggestion lines]).
# 7-9 lines, second person, permissive, always compatible with drifting to sleep.
_TOPICS = {
    "Letting Go of Stress": ("Soft Rainstorm", [
        "The day is over now, and it has carried all of itself away with it.",
        "You can set every task and every worry down at the edge of the bed.",
        "They will keep until morning; not one of them needs you tonight.",
        "With each slow breath out, a little more of the day's tightness dissolves.",
        "Feel your jaw, your shoulders, your hands letting go of what they were holding.",
        "Whatever happened today, it is finished, and you are safe, and you are here.",
        "There is nothing to fix and nothing to carry into this quiet.",
        "You are allowed, right now, to simply rest, and to be held by the dark.",
        "Let the calm settle deeper than the stress ever reached.",
    ]),
    "Quiet Confidence": ("Wind in Pines", [
        "As you rest, a quiet steadiness is settling somewhere deep inside you.",
        "You are enough, exactly as you are, and you have always been enough.",
        "You have met hard days before, and you are still here, and still whole.",
        "You can let go of needing to prove anything to anyone, tonight or ever.",
        "While you sleep, this calm sureness takes root, gently, on its own.",
        "Tomorrow it will simply be there, steady and warm, like ground beneath you.",
        "You can trust yourself to meet the next day, in its own good time.",
        "For now there is nothing to do but rest in that quiet, kindly strength.",
        "Let it hold you, soft and sure, as you drift further down.",
    ]),
    "Calm Focus": ("Brown Noise", [
        "Your mind is growing still now, like a lake when the wind dies down.",
        "All the scattered thoughts of the day are settling, slowly, to the bottom.",
        "You do not have to follow any of them; you can let them drift and fade.",
        "A clear, quiet mind is its own kind of rest, and it is yours tonight.",
        "While you sleep, your mind sorts and settles everything, all on its own.",
        "You may notice, tomorrow, that things feel simpler, one calm thing at a time.",
        "There is nothing to hold in mind right now, nothing to keep track of.",
        "Let the quiet gather, soft and deep, until only stillness remains.",
        "And let that stillness carry you gently down into sleep.",
    ]),
    "Letting Go of Worry": ("Gentle Rain", [
        "If a worried thought drifts by, you do not have to hold on to it.",
        "Let each one float past like a leaf carried gently on a slow stream.",
        "You can picture setting tomorrow's problems in a box by the door.",
        "They will wait there safely; morning is soon enough to open it.",
        "The night asks nothing of you but to rest, and to let the worries thin.",
        "Breathe in the quiet, and breathe the restlessness slowly away.",
        "Underneath every anxious thought is a deep, calm stillness, and you are sinking into it now.",
        "There is nowhere you need to be but here, soft and safe and still.",
        "Let the worries grow distant and dim, and let the calm grow.",
    ]),
    "Deep Self-Acceptance": ("Ocean Waves", [
        "Just as you are, right now, you are worthy of rest and of kindness.",
        "You can let go of every harsh word you have said to yourself today.",
        "Speak to yourself the way you would soothe someone you love into sleep.",
        "You do not have to earn this rest; it is simply yours.",
        "You are allowed to be unfinished, and still be wholly enough.",
        "Let a warm acceptance settle over you, soft as a blanket, head to toe.",
        "While you sleep, let yourself be held, exactly as you are.",
        "There is nothing to change tonight, only to rest, and to be at peace.",
        "Let that gentleness carry you all the way down.",
    ]),
    "Peaceful Gratitude": ("Singing Bowl", [
        "As you settle, let one small good thing from today come quietly to mind.",
        "Perhaps a warm drink, a kind word, a moment of light through a window.",
        "You do not have to search; let it surface softly, and rest on it.",
        "A quiet thankfulness warms the chest, slow and easy, like a low fire.",
        "There is enough, in this moment, and you have enough, and you are enough.",
        "Let the small good things of the day settle around you like soft snow.",
        "A grateful heart is a calm heart, and yours is growing calm and full.",
        "Let that warmth deepen as everything else grows quiet and dim.",
        "And let it carry you, content and peaceful, down into sleep.",
    ]),
}


def names():
    """The themed session NAMEs, e.g. 'Sleep Hypnosis: Calm Focus'."""
    return [_PREFIX + k for k in _TOPICS]


def _key(name):
    return name[len(_PREFIX):] if name.startswith(_PREFIX) else name


def has(name):
    return _key(name) in _TOPICS


def ambience(name):
    t = _TOPICS.get(_key(name))
    return t[0] if t else hypnosis.AMBIENCE


def units(name, rng=None, guidance=True):
    """The shared induction + this theme's suggestions + the drift into sleep."""
    rng = rng or random.Random()
    suggest = _TOPICS.get(_key(name), (None, hypnosis._SUGGEST))[1]
    yield from hypnosis.induction(rng, guidance)
    for line in suggest:
        yield hypnosis._u(line, 4400, kind="hypnosis")
    yield from hypnosis.drift_tail(rng)
