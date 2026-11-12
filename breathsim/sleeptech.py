"""Guided sleep sessions -- the desktop mirror of the iOS ``SleepAids``
additions.  Four short spoken sessions whose ideas come from techniques used in
CBT-I and sleep hypnosis (relaxation aids, not treatment), each a stream of soft narrator units (the same
``{text, pause, phase, kind}`` shape the storyteller uses), closing on the shared
soft drift into sleep (:func:`breathsim.hypnosis.drift_tail`):

* **Let Go of Trying** -- based on *paradoxical intention*: gently giving up
  the effort to fall asleep, so there is less pressure to "get it right".
* **Deeper Sleep** -- a slow, permissive *"sleep deeper" suggestion*, in the
  style of the sleep-hypnosis scripts used in research by Cordi & Rasch (2014).
* **Awake in the Night** -- *stimulus control* / the quarter-hour rule, made kind,
  for the 3 a.m. waking: strengthen the bed-sleep bond without clock-watching.
* **Put the Day to Rest** -- *constructive worry*: naming tomorrow's tasks
  before bed so they can be set down (the idea behind Scullin et al., 2018).

Pure data + generators; offline + testable.  Registered as Sleep storyteller
options via :func:`breathsim.stories.extra_names`.
"""
from __future__ import annotations

import random

NAME_PARADOX = "Let Go of Trying"
NAME_DEEPER = "Deeper Sleep"
NAME_AWAKE = "Awake in the Night"
NAME_WORRY = "Put the Day to Rest"

NAMES = [NAME_PARADOX, NAME_DEEPER, NAME_AWAKE, NAME_WORRY]

_AMBIENCE = {
    NAME_PARADOX: "Brown Noise",
    NAME_DEEPER: "Deep Sleep (Pink Noise)",
    NAME_AWAKE: "Brown Noise",
    NAME_WORRY: "Mountain Stream",
}


def names():
    return list(NAMES)


def has(name):
    return name in NAMES


def ambience(name):
    return _AMBIENCE.get(name)


def _u(text, pause, phase=None, kind="calm"):
    return {"text": text, "pause": pause, "phase": phase, "kind": kind}


# --- the four scripts ------------------------------------------------------

_PARADOX = [
    "For these few minutes, you have permission to give up trying to sleep.",
    "You do not have to fall asleep tonight. You only have to rest.",
    "Sleep is not something you can force. It comes on its own, when you stop reaching for it.",
    "So let go of the effort entirely. Let your body lie here, simply awake and calm.",
    "If you happen to stay awake, that is completely fine. Resting is enough.",
    "Notice how it feels to stop chasing sleep. The pressure begins to ease.",
    "There is nothing to achieve, nothing to fix, nowhere to get to.",
    "Just your breath, moving in and out, and your body, heavy and still.",
    "Let the wish to sleep float away. You are content simply to lie here.",
    "And in that letting go, with no effort at all, sleep is free to find you.",
    "Rest easy. Stay as awake as you like. There is all the time in the world.",
]

_DEEPER = [
    "Let your breathing slow, and let every word settle gently into your body.",
    "With each breath out, you drift a little further down, into deeper rest.",
    "Your mind is growing calm and quiet, like a still lake at night.",
    "Imagine yourself sinking, slowly and safely, into soft, deep water.",
    "Down, and down, each layer warmer and more peaceful than the last.",
    "As you sink, your sleep grows deeper. Long, slow waves of deep sleep.",
    "Your body knows how to do this. Let it carry you into deep, restoring sleep.",
    "Deeper now. Slower. Heavier. Wonderfully calm.",
    "Let tonight's sleep be deep and easy, and let the morning come gently.",
    "Every breath takes you deeper. Down into the slow, restful depths of sleep.",
    "Let yourself go completely. Deep, deep sleep, all through the night.",
    "Drifting down, deeper, and deeper, into a full and restful sleep.",
]

_AWAKE = [
    "Waking in the night is normal. Everyone does it. Nothing has gone wrong.",
    "There is no need to check the time. Knowing it will only stir the mind.",
    "You don't have to fall back asleep right now. Just rest, and breathe.",
    "Let your body stay soft and warm under the covers, eyes gently closed.",
    "Breathe out slowly, a little longer than you breathe in. Let it lengthen.",
    "If your thoughts start to race, that's alright. Let them pass like clouds.",
    "If you've been lying awake a long while and feel tense or frustrated,",
    "it's okay to slip out of bed for a few minutes, somewhere dim and quiet,",
    "and do something gentle until you feel sleepy again. Then return to bed.",
    "Your bed is a place for rest. Sleep will come back; it always does.",
    "For now, simply breathe, and let your body be heavy, and wait without waiting.",
    "Soft, and slow, and patient. Rest is already happening.",
]

_WORRY = [
    "Before you sleep, let's set the day down, so your mind can rest.",
    "Bring to mind anything still turning over: a worry, a task, a loose end.",
    "You don't need to solve it now. Night is not the time for solving.",
    "Picture a small notebook by your bed. In it, you place each concern.",
    "For each one, name the single next small step, and then set it on the page.",
    "It is written down now. It will keep until morning. You can let it go.",
    "One by one, lay each thought into the notebook, and close the cover.",
    "Tomorrow has been given what it needs. Tonight has only rest.",
    "Whatever is left undone can wait. The day is complete, just as it is.",
    "Let your shoulders drop. The carrying is finished for today.",
    "Your mind is lighter now, the loops are closed, the page is full.",
    "There is nothing left to hold. Let yourself sink softly into sleep.",
]

_SCRIPT = {
    NAME_PARADOX: _PARADOX,
    NAME_DEEPER: _DEEPER,
    NAME_AWAKE: _AWAKE,
    NAME_WORRY: _WORRY,
}


def units(name, rng=None, guidance=True):
    """Yield the chosen session's narrator units, then the shared soft drift to
    sleep.  ``guidance`` keeps a couple of breath-paced breaths near the start
    (dropped when false), matching the other guided sessions."""
    rng = rng or random.Random()
    lines = _SCRIPT.get(name)
    if not lines:
        return
    yield _u(lines[0], 3600)
    if guidance:
        for _ in range(2):
            yield _u("Breathe in, slowly...", 4000, phase="in", kind="guide")
            yield _u("and let it go.", 6000, phase="out", kind="guide")
    for line in lines[1:]:
        yield _u(line, 4600)
    from . import hypnosis                          # the shared endless drift into sleep
    yield from hypnosis.drift_tail(rng)
