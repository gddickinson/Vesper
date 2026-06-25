"""Drifting Haiku: an endless, season-aware haiku / tanka generator.

A tiny grammar that assembles gentle verse in the spirit of the Japanese short
forms from curated image fragments, organised by season (the *kigo*, or season
word, is built into the banks). Each poem is composed from a short opening image,
a slightly longer middle, and a quiet closing turn (a haiku); sometimes two more
reflective lines are added to make a tanka. The seasons drift slowly through the
year, announced softly, so the listener wanders an endless, low-arousal almanac
of small still images toward sleep.

These are assembled *in the spirit of* haiku (short / longer / short), not strict
5-7-5 syllable counts, and every fragment is **original** (no copyright). Pure
data + ``random`` with an injected, seeded RNG -> deterministic + unit-testable.
Surfaced as a Sleep storyteller option via :mod:`breathsim.stories`.
"""
from __future__ import annotations

import random

NAME = "Drifting Haiku"
AMBIENCE = "Night Crickets"        # a soft autumn-evening bed under the verses

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]

# Per season: an opening image, a middle development, and a quiet closing turn.
# Any l1 + l2 + l3 should read as a small, self-contained, soothing haiku.
_BANK = {
    "Spring": {
        "l1": ["plum blossom opening", "thin spring mist", "the first warm rain",
               "melting snow", "a returning bird", "soft green on the hill",
               "cherry petals fall", "the pond unfreezing"],
        "l2": ["one petal on the still water", "the orchard breathing slowly",
               "a slow warmth in the evening air", "the field letting go of winter",
               "mist settling in the valley", "the quiet after the rain",
               "willow leaves just unfolding", "the river finding its voice again"],
        "l3": ["nothing in a hurry", "the day grows soft", "all is unhurried",
               "the dusk comes gently", "and i breathe slower", "the world grows tender",
               "and the light goes blue", "everything at rest"],
    },
    "Summer": {
        "l1": ["the last cicada", "deep green shade", "a cool evening breeze",
               "one early firefly", "moon on the reeds", "warm rain at dusk",
               "the lotus closing", "still summer water"],
        "l2": ["the heat letting go of the day", "fireflies drifting over the grass",
               "the long light fading from the hills", "a single cloud, then none",
               "the garden cooling into night", "moonlight loose upon the pond",
               "the breeze turning the leaves over", "the evening growing wide and soft"],
        "l3": ["the night grows kind", "and all is cool", "the dark comes slow",
               "nothing left to do", "and i let go", "the quiet deepens",
               "everything slows", "and the day is done"],
    },
    "Autumn": {
        "l1": ["the harvest moon", "one red leaf", "the cricket's last song",
               "first frost coming", "wild geese going south", "cool dew at dusk",
               "a thinning garden", "the long blue evening"],
        "l2": ["leaves letting go of the still branch", "the moon clear over cooling fields",
               "a small voice thinning in the grass", "frost gathering at the window",
               "the orchard giving up its gold", "mist low along the quiet river",
               "the last warmth leaving the stones", "geese fading into the grey"],
        "l3": ["and the year lets go", "all softly falling", "nothing held too long",
               "the night grows cool", "and i grow still", "the quiet settles",
               "and the dark is kind", "everything eases"],
    },
    "Winter": {
        "l1": ["snow on the bare branch", "the long night", "a single lantern",
               "still frozen pond", "breath in the cold air", "plum in the snow",
               "the quiet of white", "the year's deep rest"],
        "l2": ["snow softening every rooftop", "the world hushed and folded in white",
               "one warm light in the cold dark", "the long night holding everything",
               "frost flowers closing on the glass", "no footprint on the new snow yet",
               "the still pond sleeping under ice", "the cold blue evening growing deep"],
        "l3": ["and all is silent", "nothing stirs at all", "the world lies still",
               "and the night is deep", "everything sleeps", "the dark is gentle",
               "and i sink to rest", "all softly folded"],
    },
}

# Two extra reflective lines that turn a haiku into a tanka (season-agnostic).
_TANKA_TAIL = [
    ["and i let the long day go", "soft into the quiet dark"],
    ["my thoughts grow few and slow", "and i drift toward sleep"],
    ["i loosen my tired hands", "and the night asks nothing more"],
    ["nothing left for me to hold", "only this slow breathing in"],
    ["i forget what i was keeping", "and rest comes over me"],
    ["the stillness fills me slowly", "and i let it carry me down"],
]


def _u(text, pause, kind="poem"):
    return {"text": text, "pause": pause, "phase": None, "kind": kind}


def _compose(rng, season, tanka=False):
    b = _BANK[season]
    lines = [rng.choice(b["l1"]), rng.choice(b["l2"]), rng.choice(b["l3"])]
    if tanka:
        lines = lines + list(rng.choice(_TANKA_TAIL))
    return lines


def compose(rng=None, season=None, tanka=False):
    """Public: compose one haiku (or tanka) for *season* (random if None).
    Reused by the haibun storyteller to crystallise a wandering passage."""
    rng = rng or random.Random()
    return _compose(rng, season or rng.choice(SEASONS), tanka)


def units(rng=None, guidance=True):
    """Endlessly recite drifting haiku (and the occasional tanka), wandering
    slowly through the four seasons, with breath-length pauses and a longer rest
    after each poem."""
    rng = rng or random.Random()
    if guidance:
        yield _u("Small still pictures, drifting by, to carry you toward sleep.",
                 2800, kind="guide")
    si = rng.randrange(len(SEASONS))
    n = 0
    while True:
        season = SEASONS[si]
        if n % 5 == 0:                                # name the season softly
            yield _u(season + ".", 3000, kind="guide")
        tanka = (rng.random() < 0.3)                  # ~30% are tanka
        lines = _compose(rng, season, tanka)
        last = len(lines) - 1
        for j, ln in enumerate(lines):
            yield _u(ln, 5400 if j == last else 2500)
        n += 1
        if n % 5 == 0:                                # drift to the next season
            si = (si + 1) % len(SEASONS)
