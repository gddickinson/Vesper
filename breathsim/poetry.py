"""Poetry: soft, sleepy nocturnes recited slowly to carry the listener down.

A small collection of *original* calming poems (written for Vesper, so there are
no copyright concerns) on night, rest, the sea, rain, stars and letting go. The
storyteller speaks one line at a time with breath-length pauses, a longer rest at
each stanza break and a long silence between poems, cycling endlessly in a shuffled
order. Pure data + ``random`` -- unit-testable.

Surfaced as a Sleep storyteller option via :mod:`breathsim.stories` (``story_units``
dispatches here by :data:`NAME`). Lines carry ``kind="poem"`` so the GUI holds the
ambience bed steady rather than chasing the shifting imagery.
"""
from __future__ import annotations

import random

NAME = "Pure Poetry: English Nocturnes"
ALIAS = "Poetry"                   # backward-compat: the old saved/menu name
AMBIENCE = "Soft Rainstorm"        # a steady, soft bed under the verses

# (title, lines). An empty string is a stanza break (a longer pause).
POEMS = [
    ("The Last Light", [
        "The day has folded up its gold,",
        "and laid it gently down;",
        "the hills go blue, the windows warm,",
        "and quiet fills the town.",
        "",
        "There is nothing left to carry now,",
        "no road you have to keep;",
        "the evening leans against the glass",
        "and asks you only: sleep.",
    ]),
    ("Tide", [
        "Far out, the sea is breathing,",
        "slow as a sleeping chest,",
        "drawing the long waves over the stones",
        "and letting them go to rest.",
        "",
        "In, and the shore is silver;",
        "out, and the foam grows thin;",
        "and somewhere in that endless hush",
        "your own slow breath fits in.",
    ]),
    ("Rain at Night", [
        "Listen: the rain has come to stay",
        "a while upon the roof,",
        "a hundred soft and silver feet",
        "that ask for nothing, prove",
        "",
        "nothing, and mean nothing, but to fall,",
        "and fall, and fall, and fall,",
        "until the small cares of the day",
        "are washed beyond recall.",
    ]),
    ("The Night Train", [
        "Somewhere a train is going home",
        "across the sleeping land,",
        "its little lighted windows passing",
        "fields too dark to understand.",
        "",
        "Let it carry your thoughts away,",
        "car by quiet car,",
        "until the only thought that's left",
        "is how soft the distances are.",
    ]),
    ("Stars", [
        "The stars do not need watching;",
        "they keep their slow parade",
        "whether your eyes are open wide",
        "or softly, softly laid.",
        "",
        "So close them now. The sky will turn,",
        "the old lights wheel and gleam,",
        "and you may set the whole night down",
        "and slip into a dream.",
    ]),
    ("Snowfall", [
        "The snow comes down without a word,",
        "unhurried, cool and deep,",
        "folding the rooftops one by one",
        "in blankets meant for sleep.",
        "",
        "No footprints yet, no morning yet,",
        "no need to rise or roam;",
        "only the slow and certain falling",
        "of the quiet coming home.",
    ]),
    ("Lullaby for the Restless Mind", [
        "Lay it down, the heavy day,",
        "the things you did not say;",
        "the morning keeps its own affairs,",
        "and dawn is far away.",
        "",
        "Lay it down, the turning thought,",
        "the knot you could not free;",
        "the dark is wide and patient here,",
        "and rest is all you need.",
    ]),
    ("The River", [
        "The river does not hurry,",
        "though it travels through the night;",
        "it only gives itself away",
        "to gravity and light.",
        "",
        "So be the river: ask no questions,",
        "hold no cold stone long,",
        "and let the current take you down",
        "as gentle as a song.",
    ]),
]


def _u(text, pause, kind="poem"):
    return {"text": text, "pause": pause, "phase": None, "kind": kind}


def recite(poems, rng=None, guidance=True, intro=None):
    """Recite *poems* forever in a shuffled order, slowly, with rests at stanza
    breaks (an empty line) and long silences between poems. Shared by the world
    poetry traditions (:mod:`breathsim.poetry_world`)."""
    rng = rng or random.Random()
    if guidance and intro:
        yield _u(intro, 2800, kind="guide")
    order = list(range(len(poems)))
    while True:
        rng.shuffle(order)
        for idx in order:
            title, lines = poems[idx]
            last = max(i for i, ln in enumerate(lines) if ln.strip())
            yield _u(title + ".", 2800)
            for j, ln in enumerate(lines):
                if not ln.strip():
                    continue
                if j == last:
                    pause = 5200                     # long rest after the poem
                elif j + 1 < len(lines) and not lines[j + 1].strip():
                    pause = 3200                     # rest at a stanza break
                else:
                    pause = 2000
                yield _u(ln, pause)


def units(rng=None, guidance=True):
    """Recite the English nocturnes forever (see :func:`recite`)."""
    return recite(POEMS, rng, guidance,
                  intro="Let some quiet verses carry you gently down toward sleep.")
