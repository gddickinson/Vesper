"""Procedural bedtime "stories": endless, plotless, soothing narration.

There is no plot on purpose -- the point is to gently occupy and quiet the mind.
A :class:`Scene` carries themed vocabulary and a matching ambience; ``story_units``
yields an endless stream of *units* (a line + how long to pause after it),
weaving in gentle **breathwork**, **body-scan** and **relaxation** interludes at
intervals. The :class:`~breathsim.narration.Narrator` speaks the units, softly,
fading as the session winds down. Pure data + ``random`` -- unit-testable.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

# A library book can be narrated as a Sleep storyteller option ("Book: <title>").
# It plays under the same wind-down + fade-out as any lecture, and resumes by
# sentence index. Books carry no ambience of their own, so use one calm bed.
BOOK_PREFIX = "Book: "
BOOK_AMBIENCE = "Soft Rainstorm"

# Shared vocabulary used by every scene's templates.
_SHARED = {
    "opener": ["Somewhere", "For a while", "Slowly", "And so", "Outside",
               "Nearby", "Little by little", "After a time", "Here", "Just now"],
    "sa": ["softly", "slowly", "gently", "quietly", "without hurry",
           "ever so slowly", "again and again", "in no hurry at all"],
    "gv": ["drifts", "settles", "murmurs", "sways", "breathes", "rests", "hums",
           "ripples", "fades", "lingers", "turns", "sighs"],
    "body": ["shoulders", "eyes", "hands", "breath", "thoughts", "jaw",
             "whole body"],
    "heavy": ["heavy", "soft", "still", "warm", "quiet", "calm", "at ease",
              "peaceful", "drowsy"],
    "calm": ["calm", "still", "far away", "unhurried", "soft", "gentle"],
}

_TEMPLATES = [
    "{opener}, the {sound_src} {gv} {sa}.",
    "The {thing} {gv} {sa}, and the {place} is {heavy}.",
    "You let your {body} grow {heavy}, while the {light} {gv} {sa}.",
    "{opener} a {creature} {gv} near the {thing}, then is {heavy} again.",
    "There is nothing to do here but listen to the {sound_src}.",
    "The {light} {gv}, and the {soft_thing} feels {heavy} beneath you.",
    "Time drifts {sa} here, as the {sound_src} {gv} on and on.",
    "{opener}, everything is {heavy} and {calm} -- the {thing}, the {place}.",
    "Somewhere the {creature} has gone to sleep, and the {light} {gv} {sa}.",
    "You breathe in the quiet of the {place}, and let it grow {heavy}.",
    "The {sound_src} {gv}, {sa}, and there is nowhere else to be.",
    "A {thing}, a {light}, the {soft_thing} -- all of it {heavy} and {calm}.",
]


@dataclass
class Scene:
    name: str
    ambience: str
    pools: dict = field(default_factory=dict)


SCENES = {
    "Rainy Cottage": Scene("Rainy Cottage", "Soft Rainstorm", {
        "place": ["cottage", "little room", "warm kitchen", "old house"],
        "thing": ["window", "kettle", "blanket", "teacup", "clock", "curtain"],
        "sound_src": ["rain", "rainfall", "soft patter of rain",
                      "wind in the eaves"],
        "soft_thing": ["blanket", "armchair", "quilt", "rug", "pillow"],
        "light": ["lamp", "fire", "embers", "candle", "glow of the lamp"],
        "creature": ["cat", "old dog", "moth", "robin in the eaves"]}),
    "Seaside": Scene("Seaside", "Ocean Waves", {
        "place": ["shore", "quiet beach", "little harbour", "bay", "headland"],
        "thing": ["tide", "driftwood", "scattered shells", "old boat", "pier"],
        "sound_src": ["waves", "sea", "tide", "gentle surf", "swell"],
        "soft_thing": ["warm sand", "dune grass", "towel", "smooth rock"],
        "light": ["moon", "lighthouse", "stars", "last of the light"],
        "creature": ["distant gull", "small crab", "seal", "sandpiper"]}),
    "Riverside": Scene("Riverside", "Mountain Stream", {
        "place": ["riverbank", "willow grove", "little bridge", "river meadow"],
        "thing": ["river", "smooth stones", "reeds", "ripples", "old bridge"],
        "sound_src": ["river", "stream", "current", "water over the stones",
                      "brook"],
        "soft_thing": ["moss", "soft grass", "mossy bank", "heather"],
        "light": ["moon", "evening light", "sunlight on the water", "fireflies"],
        "creature": ["fish", "heron", "frog", "damselfly"]}),
    "Quiet Cafe": Scene("Quiet Cafe", "Cafe Murmur", {
        "place": ["cafe", "corner table", "little coffee house", "window seat"],
        "thing": ["cup", "saucer", "window", "open book", "spoon", "steam"],
        "sound_src": ["murmur of voices", "hush of the room",
                      "soft hiss of the machine", "quiet chatter",
                      "rain on the window"],
        "soft_thing": ["worn cushion", "booth seat", "armchair",
                       "blanket over your knees"],
        "light": ["lamp", "streetlight outside", "warm light",
                  "glow of the counter"],
        "creature": ["quiet stranger", "old waiter", "sleepy cat by the door"]}),
    "Night Meadow": Scene("Night Meadow", "Forest Wind", {
        "place": ["meadow", "hillside", "open field", "quiet valley"],
        "thing": ["grass", "wildflowers", "old fence", "tall reeds", "hay"],
        "sound_src": ["breeze", "wind in the grass", "crickets",
                      "rustle of the grass", "night air"],
        "soft_thing": ["soft grass", "warm earth", "blanket", "heather"],
        "light": ["moon", "stars", "fireflies", "the milky way", "moonlight"],
        "creature": ["owl", "cricket", "field mouse", "fox far away"]}),
}


def scene_names():
    return list(SCENES.keys())


def book_names():
    """'Book: <title>' for each book in the local library (empty if none). These
    surface in the Sleep story picker and narrate under the Sleep wind-down."""
    try:
        from . import books
        return [BOOK_PREFIX + b.get("title", "Untitled") for b in books.list_books()]
    except Exception:
        return []


def book_id_for(name):
    """Resolve a 'Book: <title>' picker name back to a library book id, or None."""
    if not isinstance(name, str) or not name.startswith(BOOK_PREFIX):
        return None
    title = name[len(BOOK_PREFIX):]
    try:
        from . import books
        for b in books.list_books():
            if b.get("title") == title:
                return b.get("id")
    except Exception:
        pass
    return None


def extra_names():
    """Special non-templated storyteller generators (Cognitive Shuffle, Sleep
    Hypnosis + themed self-help hypnosis sessions, Poetry)."""
    from . import (autogenic, haibun, haiku, hypnosis, hypnosis_topics, journey,
                   lovingkindness, poetry, poetry_world, safeplace, shuffle, tales)
    return ([shuffle.NAME, hypnosis.NAME, autogenic.NAME, lovingkindness.NAME,
             safeplace.NAME, journey.NAME]
            + hypnosis_topics.names()
            + [poetry.NAME] + poetry_world.names()
            + [haiku.NAME, haibun.NAME, tales.NAME])


def lecture_names(category=None):
    """Names of the soothing-lecture sources, optionally one branch only."""
    from . import lectures
    return lectures.names(category)


def lecture_categories():
    """The lecture branches (e.g. The Cosmos, Histories), in picker order."""
    from . import lectures
    return lectures.categories()


def ambience_for(name):
    """Ambience voice for a scene *or* a lecture (None if unknown, e.g. Random)."""
    if isinstance(name, str) and name.startswith(BOOK_PREFIX):
        return BOOK_AMBIENCE
    from . import (autogenic, hypnosis, hypnosis_topics, journey, lovingkindness,
                   poetry, poetry_world, safeplace, shuffle)
    if name == shuffle.NAME:
        return shuffle.AMBIENCE
    if name == journey.NAME:
        return journey.AMBIENCE
    if name == hypnosis.NAME:
        return hypnosis.AMBIENCE
    if name == autogenic.NAME:
        return autogenic.AMBIENCE
    if name == lovingkindness.NAME:
        return lovingkindness.AMBIENCE
    if name == safeplace.NAME:
        return safeplace.AMBIENCE
    if hypnosis_topics.has(name):
        return hypnosis_topics.ambience(name)
    if name in (poetry.NAME, poetry.ALIAS):
        return poetry.AMBIENCE
    if poetry_world.has(name):
        return poetry_world.ambience(name)
    from . import haibun, haiku, tales
    if name == haiku.NAME:
        return haiku.AMBIENCE
    if name == haibun.NAME:
        return haibun.AMBIENCE
    if name == tales.NAME:
        return tales.AMBIENCE
    sc = SCENES.get(name)
    if sc:
        return sc.ambience
    from . import lectures
    return lectures.ambience(name)


class _Pick:
    def __init__(self, pools, rng):
        self.pools, self.rng = pools, rng

    def __getitem__(self, key):
        return self.rng.choice(self.pools[key])


def _u(text, pause=950, phase=None, kind="story"):
    return {"text": text, "pause": pause, "phase": phase, "kind": kind}


def _fill(scene, rng, tmpl):
    """Fill a template from the shared + scene pools, capitalise + punctuate."""
    s = tmpl.format_map(_Pick({**_SHARED, **scene.pools}, rng))
    s = s[0].upper() + s[1:]
    if s[-1] not in ".?!":
        s += "."
    return s


def _sentence(scene, rng, last=[None], fade=1.0):
    """One scene sentence. *fade* (>=1) lengthens the pause as the session
    deepens -- part of the slow zoom-out-and-fade toward sleep."""
    tmpl = rng.choice([t for t in _TEMPLATES if t != last[0]])
    last[0] = tmpl
    return _u(_fill(scene, rng, tmpl), pause=int(rng.randint(650, 1150) * fade))


# --- guidance interludes ---------------------------------------------------

def _breath(rng):
    yield _u("Let's take a few slow breaths together.", 1100, kind="guide")
    for _ in range(rng.randint(3, 5)):
        yield _u("Breathe in...", 4000, phase="in", kind="guide")
        yield _u("and softly let it go.", 6000, phase="out", kind="guide")
    yield _u("Let your breath settle into its own slow rhythm.", 1600,
             kind="guide")


_PARTS = ["feet", "legs", "hips", "belly", "back", "hands", "arms",
          "shoulders", "neck", "jaw", "face", "eyes"]


def _bodyscan(rng):
    yield _u("Now let your attention drift slowly through your body.", 1800,
             kind="guide")
    start = rng.randint(0, max(0, len(_PARTS) - 6))
    for part in _PARTS[start:start + rng.randint(4, 6)]:
        yield _u(f"Notice your {part}... and let them grow heavy, and soft.",
                 3200, kind="guide")
    yield _u("The whole body, sinking down, completely at rest.", 2600,
             kind="guide")


_RELAX = [
    "Feel the gentle weight of your body, held and supported.",
    "There is nothing you need to do, and nowhere you need to be.",
    "Let the sounds wash over you, and through you.",
    "Each breath a little slower, a little softer than the last.",
    "If a thought drifts by, just let it float away.",
    "Let your face soften, and the space between your brows grow smooth.",
]


def _relax(rng):
    yield _u("Take a moment now, just to rest.", 1600, kind="guide")
    for line in rng.sample(_RELAX, rng.randint(2, 3)):
        yield _u(line, 3000, kind="guide")


# Occasional contemplative lines, in the spirit of mono no aware (transience),
# the Taoist watercourse way, and Stoic night-counsel -- woven in as a fourth
# interlude alongside the breath / body-scan / relaxation ones.
_REFLECT = [
    "Nothing here will last, and that is what makes it lovely; let it pass, and rest.",
    "This quiet moment will not come again, and so it is enough, just as it is.",
    "Be soft now, like water, which yields to everything and yet wears the hardest stone.",
    "Water always finds the low, still place, and settles there; settle there too.",
    "The world turns on its own tonight -- the tides, the stars, your breath -- and needs no help from you.",
    "Whatever the day held is behind you now; this night asks only that you rest.",
    "Let what is not yours to carry rest outside the door, soft and harmless in the dark.",
]


def _contemplate(rng):
    yield _u(rng.choice(_REFLECT), 4400, kind="guide")


_INTERLUDES = [_breath, _bodyscan, _relax, _contemplate]

# A gentle recurring refrain, built once per session and repeated softly at the
# close of each pass (a lullaby-like comfort). Scene-flavoured via the pools.
_REFRAINS = [
    "And the {sound_src} goes on, {sa}, on and on.",
    "Still the {sound_src} {gv}, {sa}, and you drift a little deeper.",
    "And everything here is {heavy}, and {calm}, and far away.",
    "The {place} keeps its quiet, and holds you, and holds you.",
]

# As the session deepens, the view slowly widens and dims -- a soft zoom-out.
_WIDEN = [
    "The {place} grows wider, and dimmer, and softer now.",
    "Everything is drifting further away, and growing quiet.",
    "The edges blur, the details fade, and only the calm remains.",
    "Smaller and softer now, the whole {place} settling into the dark.",
]


def story_units(scene_name, rng=None, guidance=True, run=11, start_section=0):
    """Narration units for *scene_name*.

    A soothing **lecture** (finite, authored) if the name is one; otherwise an
    endless procedural scene: ~``run`` story sentences, then (if ``guidance``) one
    interlude -- breath / body-scan / relaxation, cycling -- then repeats forever.
    """
    rng = rng or random.Random()
    if isinstance(scene_name, str) and scene_name.startswith(BOOK_PREFIX):
        from . import bookreader, books
        bid = book_id_for(scene_name)
        book = books.load(bid) if bid else None
        if book:                                 # resume by sentence; finite stream
            yield from bookreader.resume_units(book)
        return
    from . import (autogenic, hypnosis, hypnosis_topics, journey, lovingkindness,
                   poetry, poetry_world, safeplace, shuffle)
    if scene_name == shuffle.NAME:
        yield from shuffle.units(rng, guidance)
        return
    if scene_name == journey.NAME:
        yield from journey.units(rng, guidance)
        return
    if scene_name == hypnosis.NAME:
        yield from hypnosis.units(rng, guidance)
        return
    if scene_name == autogenic.NAME:
        yield from autogenic.units(rng, guidance)
        return
    if scene_name == lovingkindness.NAME:
        yield from lovingkindness.units(rng, guidance)
        return
    if scene_name == safeplace.NAME:
        yield from safeplace.units(rng, guidance)
        return
    if hypnosis_topics.has(scene_name):
        yield from hypnosis_topics.units(scene_name, rng, guidance)
        return
    if scene_name in (poetry.NAME, poetry.ALIAS):
        yield from poetry.units(rng, guidance)
        return
    if poetry_world.has(scene_name):
        yield from poetry_world.units(scene_name, rng, guidance)
        return
    from . import haibun, haiku, tales
    if scene_name == haiku.NAME:
        yield from haiku.units(rng, guidance)
        return
    if scene_name == haibun.NAME:
        yield from haibun.units(rng, guidance)
        return
    if scene_name == tales.NAME:
        yield from tales.units(rng, guidance)
        return
    from . import lectures
    if scene_name in lectures.names():
        yield from lectures.units(scene_name, rng, guidance, start_section)
        return
    scene = SCENES.get(scene_name) or rng.choice(list(SCENES.values()))
    last = [None]
    turn = 0
    refrain = _fill(scene, rng, rng.choice(_REFRAINS))   # a recurring soft refrain
    while True:
        fade = min(2.2, 1.0 + 0.12 * turn)          # slow zoom-out: pauses lengthen
        cur_run = max(4, run - turn)                # ... and fewer sentences over time
        for _ in range(cur_run):
            yield _sentence(scene, rng, last, fade)
        if turn >= 3:                               # the view widens + dims as it deepens
            yield _u(_fill(scene, rng, rng.choice(_WIDEN)),
                     int(2200 * fade), kind="guide")
        yield _u(refrain, int(1800 * fade), kind="guide")   # the gentle recurring refrain
        if guidance:
            yield from _INTERLUDES[turn % len(_INTERLUDES)](rng)
        turn += 1
