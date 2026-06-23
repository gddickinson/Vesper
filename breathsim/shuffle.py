"""Cognitive Shuffle: a sleep-onset aid (serial diverse imagining).

Beaudoin's *cognitive shuffle* gently occupies the mind with a stream of random,
unrelated, neutral, concrete objects -- picturing each for a moment, then letting
it go. The very *diversity* (each item unrelated to the last) blocks the coherent,
anxious trains of thought that keep us awake and mimics the drifting micro-imagery
of sleep onset. Here it is narrated: a soft letter is chosen, a few ordinary
things beginning with it are named slowly with long, breath-paced gaps to picture
each, then a new letter -- on and on, monotone and low-arousal.

Pure data + ``random`` (unit-testable). Surfaced as a Sleep storyteller option via
:mod:`breathsim.stories` (``story_units`` dispatches here by :data:`NAME`).
"""
from __future__ import annotations

import random

NAME = "Cognitive Shuffle"
AMBIENCE = "Brown Noise"          # a steady, neutral masking bed

# Neutral, concrete, easily-pictured everyday objects, grouped by first letter.
# Deliberately ordinary and unemotional; nature/weather words are avoided so the
# steady bed isn't pulled around by the soundscape cue-matcher.
WORDS = {
    "a": ["acorn", "apron", "anchor", "archway", "almond", "antler", "awning",
          "apple"],
    "b": ["button", "basket", "balloon", "bicycle", "blanket", "bottle",
          "bookcase", "barrel", "beanbag", "biscuit"],
    "c": ["cushion", "crayon", "canoe", "chair", "clock", "comb", "carrot",
          "cabin", "cardigan", "compass"],
    "d": ["doorway", "drum", "dish", "daisy", "domino", "drawer", "dune",
          "doorknob", "dumpling"],
    "e": ["envelope", "easel", "eggcup", "eel", "elm", "escalator", "eraser",
          "earring"],
    "f": ["feather", "fountain", "ferry", "fern", "flute", "fork", "flag",
          "frame", "funnel", "footstool"],
    "g": ["glove", "globe", "gate", "ginger", "goose", "gondola", "grape",
          "guitar", "gourd"],
    "h": ["hammock", "hat", "harp", "hill", "hinge", "honey", "hoop",
          "handbag", "helmet"],
    "i": ["igloo", "island", "ink", "iris", "icicle", "ivy"],
    "j": ["jar", "jacket", "jug", "jigsaw", "jelly", "jasmine", "jewel"],
    "k": ["key", "kayak", "knapsack", "knoll", "kiosk", "kimono"],
    "l": ["lantern", "ladder", "lemon", "log", "loom", "lily", "ladle",
          "lampshade"],
    "m": ["marble", "mitten", "mug", "mushroom", "mill", "mast", "mailbox",
          "mandolin"],
    "n": ["nest", "needle", "napkin", "notebook", "nutmeg", "nook",
          "necklace"],
    "o": ["orchard", "otter", "oar", "oven", "olive", "onion", "ottoman"],
    "p": ["pebble", "pillow", "parasol", "pail", "pear", "plum", "pony",
          "puddle", "pumpkin", "parcel"],
    "q": ["quilt", "quill", "quince", "quiver"],
    "r": ["ribbon", "raft", "ring", "rope", "reed", "rooftop", "radish",
          "rug"],
    "s": ["spoon", "sail", "sled", "saucer", "satchel", "stone", "swing",
          "slipper", "sandal", "sweater"],
    "t": ["teapot", "tent", "thimble", "tugboat", "tulip", "towel", "trolley",
          "tray", "teaspoon"],
    "u": ["umbrella", "urn"],          # few u-words read cleanly as 'an ...'
    "v": ["vase", "violin", "vine", "vest", "velvet", "van"],
    "w": ["wagon", "wheelbarrow", "willow", "whistle", "walnut", "wreath",
          "wardrobe", "waistcoat"],
    "y": ["yarn", "yacht", "yurt"],
    "z": ["zipper", "zither"],
}

_INTRO = [
    "Let's play a quiet game to help you drift off.",
    "I'll name a few simple, ordinary things, one at a time.",
    "Picture each one for a moment, just as you see it, then let it go.",
    "There's no story, and nothing to remember. Only gentle pictures.",
]

_NUDGES = [
    "Don't try to connect them. Just see each one, and let it fade.",
    "If your mind wanders, that's fine. Drift back whenever you like.",
    "There is no need to hold on to any of them.",
    "Let each picture form softly, then dissolve.",
    "Slower now, and softer.",
]

_VOWELS = set("aeiou")
_LEADS = [None, None, None, None, "now", "and then", "then", "next"]


def _u(text, pause, kind="shuffle"):
    return {"text": text, "pause": pause, "phase": None, "kind": kind}


def _item(word, rng):
    """A gentle one-object line, e.g. 'A lantern.' or 'And then, an acorn.'"""
    art = "an" if word[0] in _VOWELS else "a"
    s = f"{art} {word}"
    lead = rng.choice(_LEADS)
    if lead:
        s = f"{lead}, {s}"
    return s[0].upper() + s[1:] + "."


def units(rng=None, guidance=True):
    """Endless stream of cognitive-shuffle narration units.

    A soft intro, then forever: pick a random letter, name 3-5 ordinary things
    beginning with it (long picture-it pauses), and now and then a quiet nudge.
    When ``guidance`` is false, the intro/nudges are dropped (objects only).
    """
    rng = rng or random.Random()
    if guidance:
        for line in _INTRO:
            yield _u(line, 2200, kind="guide")
    letters = list(WORDS)
    while True:
        bag = WORDS[rng.choice(letters)][:]
        rng.shuffle(bag)
        for word in bag[:rng.randint(3, 5)]:
            yield _u(_item(word, rng), rng.randint(3600, 5200))
        if guidance and rng.random() < 0.45:
            yield _u(rng.choice(_NUDGES), 2600, kind="guide")
