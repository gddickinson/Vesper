"""A Wandering Haibun: prose woven with haiku, in the spirit of Basho.

A *haibun* is a short prose travel-sketch punctuated by a haiku -- the form
Matsuo Basho used in *The Narrow Road to the Deep North*. Here a slow, wandering
first-person prose passage (assembled from the same themed scene vocabulary the
procedural stories use, in :mod:`breathsim.stories`) is crystallised every few
lines by a season haiku from :func:`breathsim.haiku.compose`, then the walk eases
on. There is no destination -- the point is a gentle, plotless wander toward
sleep, prose breathing out into a single still image and back again.

All text is **original** (assembled from original fragments / generated haiku);
deterministic with an injected, seeded RNG -> unit-testable. Surfaced as a Sleep
storyteller option via :mod:`breathsim.stories`.
"""
from __future__ import annotations

import random
import re

from . import haiku, stories

NAME = "A Wandering Haibun"
AMBIENCE = "Wind in Pines"          # a soft travelling-night bed

# Outdoor, walkable scenes from the story vocabulary suit a wander.
_SCENES = ["Riverside", "Seaside", "Night Meadow"]

# First-person, present-tense, wandering prose templates. They draw from the
# shared + scene pools (place/thing/sound_src/soft_thing/light/creature, plus the
# shared opener/sa/gv/body/heavy/calm), so any fill reads as a quiet step.
_PROSE = [
    "I follow the {place} as the {light} {gv} {sa}.",
    "The {sound_src} {gv} {sa}; I stop a while, and listen.",
    "Here the {thing} is {heavy}, and there is nowhere I must reach tonight.",
    "No one passes. A {creature} {gv} once, then the {place} is {heavy} again.",
    "I rest my {body}, and let the {soft_thing} hold me {sa}.",
    "The path goes on, {sa}, into the {heavy} dark, and I go with it.",
    "I do not hurry. The {sound_src} {gv} on, and that is enough.",
    "The {light} {gv} over the {thing}; I breathe, and walk a little further.",
    "Mist gathers at the {place}. I let my {body} grow {heavy} and slow.",
    "I set down what I was carrying, here by the {thing}, and feel lighter.",
]

# Quiet closing lines after each haiku, to ease back into the walk / toward sleep.
_CLOSE = [
    "I breathe, and walk on, a little slower than before.",
    "I let the small picture go, and the path continues.",
    "The night holds me gently, and I follow it down.",
    "There is nothing to keep. I wander on toward sleep.",
    "I close my eyes a moment, and the road grows soft.",
]


def _u(text, pause, kind="story"):
    return {"text": text, "pause": pause, "phase": None, "kind": kind}


def _prose_line(scene, rng, last=[None]):
    pools = {**stories._SHARED, **scene.pools}
    tmpl = rng.choice([t for t in _PROSE if t != last[0]])
    last[0] = tmpl
    s = tmpl.format_map(stories._Pick(pools, rng))
    s = s[0].upper() + s[1:]
    s = re.sub(r"\b([Aa]) (?=[aeiou])", lambda m: m.group(1) + "n ", s)  # a -> an
    if s[-1] not in ".?!":
        s += "."
    return s


def units(rng=None, guidance=True):
    """Endless haibun: a few wandering prose lines, then a season haiku, then a
    soft closing line and a longer rest, wandering on forever."""
    rng = rng or random.Random()
    if guidance:
        yield _u("A slow wandering, with a small poem here and there, toward sleep.",
                 2800, kind="guide")
    last = [None]
    while True:
        scene = stories.SCENES[rng.choice(_SCENES)]
        for _ in range(rng.randint(3, 4)):           # wandering prose
            yield _u(_prose_line(scene, rng, last), rng.randint(2600, 3400))
        for ln in haiku.compose(rng):                # the haiku, crystallising it
            yield _u(ln, 2500, kind="poem")
        yield _u(rng.choice(_CLOSE), 5200)           # ease on, long rest
