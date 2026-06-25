"""Quiet Tales: gentle, conflict-free sleep stories in the kishotenketsu shape.

Most stories run on conflict and tension -- the opposite of what helps you sleep.
These follow the East-Asian **kishotenketsu** structure, which has **no conflict**:
ki (a quiet introduction), sho (a slow development), **ten** (a gentle *turn* -- a
soft shift of view, never a clash), and ketsu (a reconciliation that dissolves
toward rest). Each little tale sets a calm scene, lingers in it, quietly widens
the view, and then settles into stillness and sleep.

A distinct, gentle *narrative* storyteller class (separate from the factual
lectures). All original (no copyright); pure data + ``random`` with an injected,
seeded RNG -> deterministic + unit-testable. Surfaced as a Sleep storyteller
option via :mod:`breathsim.stories`. Lines carry ``kind="story"``.
"""
from __future__ import annotations

import random

NAME = "Quiet Tales"
AMBIENCE = "Soft Rainstorm"        # a steady, soft bed beneath the tales

# Each tale: (title, [ki, sho, ten, ketsu]) -- four movements, each a few lines.
# The TEN is a soft turn of view (a widening, a quiet realisation), not a clash.
TALES = [
    ("The Lamplighter", [
        ["At dusk, an old lamplighter walks the quiet streets.",
         "He carries a small flame on a long brass pole.",
         "One by one, he wakes the lamps along the lane."],
        ["A soft gold light blooms at each corner he passes.",
         "Shutters close, and kettles steam, and the town grows still.",
         "He is in no hurry, for the evening has all the time it needs."],
        ["From the hill above, the lit lamps look like a field of small warm stars.",
         "He does not push the darkness away, he only keeps it gentle company."],
        ["At last he lights the lamp by his own door, and goes inside.",
         "The town glows softly under the early night, and settles, and sleeps.",
         "And so, gently, may you."]]),
    ("The Still Lake", [
        ["A small wooden boat rests on a wide and still lake.",
         "There is no wind, and the water holds the evening like glass.",
         "An old fisher sits with his line, not really fishing."],
        ["The sky turns from gold to rose to a deep and quiet blue.",
         "A single ripple crosses the lake, then smooths away.",
         "He watches it go, and lets his thoughts go with it."],
        ["He notices he is not waiting for anything at all.",
         "The lake is not below him or beyond him, he is simply part of its evening."],
        ["He draws in the line, with nothing on it, and is content.",
         "The boat drifts a little, then rests, and the lake grows dark and calm.",
         "Let the stillness hold you the way it holds the lake."]]),
    ("Snow on the Village", [
        ["Snow begins to fall, very slowly, over a sleeping village.",
         "It comes without a sound, drifting past the lit windows.",
         "Roof by roof, the white grows soft and deep."],
        ["A baker's chimney breathes a little smoke into the dark.",
         "A cat watches from a sill, then curls and closes its eyes.",
         "Footprints fill in, and the lanes go smooth and quiet."],
        ["By midnight there is no hard edge left anywhere, only gentle white.",
         "The snow has not buried the village, it has tucked it in."],
        ["The last light in the last window dims, and goes out.",
         "The whole village rests beneath its soft white blanket.",
         "Let the quiet snow settle over you too, and rest."]]),
    ("The Old Gardener", [
        ["In the blue evening, an old gardener walks among her plants.",
         "She is not working now, only saying a soft goodnight.",
         "She touches a leaf here, a petal there, in passing."],
        ["The flowers have closed their faces for the night.",
         "Moths come to the pale blooms, and the air is cool and sweet.",
         "She sits on a worn bench and breathes the green dark in."],
        ["She thinks how the garden grows mostly while she sleeps.",
         "She does not make it grow, she only makes a little room, and waits."],
        ["She leaves the gate ajar for the night air, and goes in.",
         "The garden breathes on, slow and patient, under the first stars.",
         "Let yourself grow quiet the way a garden does, and rest."]]),
    ("The Tea House on the Hill", [
        ["High on a hill, a small tea house keeps a single lantern lit.",
         "The path up is long, and tonight no travelers come.",
         "The keeper sweeps the step, though no one will see it."],
        ["He sets out one cup, and warms the water just the same.",
         "Mist rolls up the slope and softens the dark pines.",
         "He listens to it all, the kettle, the wind, the far-off temple bell."],
        ["He understands the lantern is not only for guests.",
         "It is for the hillside itself, a small kindness to the dark."],
        ["He drinks his tea slowly, then lets the lantern burn low.",
         "The mist closes gently around the quiet house.",
         "Let your thoughts grow soft as mist, and settle, and sleep."]]),
    ("The Child and the Moon", [
        ["A child lies awake and watches the moon at the window.",
         "It is round and pale and does not seem to move.",
         "The house is dark, and warm, and breathing softly."],
        ["A thin cloud drifts across, and the moon goes dim, then bright.",
         "An owl calls once, far away, and the night holds still.",
         "The child's eyes grow heavy, then open, then heavy again."],
        ["The child sees the moon is not watching, only shining.",
         "It shines on the already-asleep and the not-yet-asleep all the same."],
        ["The cloud drifts on, and the moon pours soft light on the floor.",
         "The child's breathing slows, and deepens, and lets go.",
         "Let the same kind light fall over you now, and sleep."]]),
]


def _u(text, pause, kind="story"):
    return {"text": text, "pause": pause, "phase": None, "kind": kind}


def units(rng=None, guidance=True):
    """Recite the quiet tales forever in a shuffled order: each tale unfolds in
    four gentle movements (with a longer breath between them and a long rest after
    the tale), then the next begins -- endless and conflict-free."""
    rng = rng or random.Random()
    if guidance:
        yield _u("A few quiet tales, to wander through gently toward sleep.",
                 2800, kind="guide")
    order = list(range(len(TALES)))
    while True:
        rng.shuffle(order)
        for idx in order:
            title, movements = TALES[idx]
            yield _u(title + ".", 3000)
            for mi, lines in enumerate(movements):
                last_movement = mi == len(movements) - 1
                for li, ln in enumerate(lines):
                    last_line = li == len(lines) - 1
                    if last_movement and last_line:
                        pause = 6000                 # long rest after the tale
                    elif last_line:
                        pause = 3600                 # a breath between movements
                    else:
                        pause = 2800
                    yield _u(ln, pause)
