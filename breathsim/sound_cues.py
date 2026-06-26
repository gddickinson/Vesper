"""Match imagery in narrated text to a soothing ambient sound.

Lets the bedtime storyteller's soundscape gently *follow the words*: when a line
speaks of rain, waves, wind, a hearth, stars... the ambience bed crossfades to a
matching sound, holding it through the imagery and easing back to the story's base
ambience over abstract passages. All targets are always-registered procedural
GROUP_NATURE voices, so this works with no downloaded assets. Pure + testable.
"""
from __future__ import annotations

import re

_WORD = re.compile(r"[a-z]+")

# (keywords, ambient voice). First match wins; ordered most- to least-specific.
# Single-word keys match a WHOLE word (or its simple +s/+es plural), so a key never
# fires on a longer unrelated word ("rain" not "train", "wind" not "window", "star"
# not "start", "surf" not "surface"); keys containing a space match as a phrase.
_CUES = [
    (("thunder", "storm", "lightning", "tempest"), "Distant Thunder"),
    (("purr", "purring", "a cat", "the cat", "kitten", "tabby", "whiskers"),
     "Purr"),
    (("wind chime", "wind chimes"), "Wind Chimes"),
    (("temple bell", "church bell", "the bells", "bell rang", "bell tolled",
      "singing bowl", "gong", "chimes", "a chime", "tolling"), "Singing Bowl"),
    (("cricket", "fireflies", "firefly", "summer night", "night insects",
      "chirp"), "Night Crickets"),
    (("campfire", "bonfire", "fireplace", "fireside", "hearth", "crackle",
      "crackling", "the flames", "candlelight", "candle flame", "glowing coals",
      "lantern", "diya", "oil lamp", "the lamps", "paper lantern",
      "festival of light"), "Campfire"),
    (("on the roof", "against the window", "against the pane", "under the eaves",
      "the eaves", "patter of rain", "rain on the"), "Rain on a Roof"),
    (("wave", "ocean", "tide", "surf", "seashore", "breaker", "the surf"),
     "Ocean Waves"),
    (("rain", "drizzle", "downpour", "rainfall"), "Soft Rainstorm"),
    (("river", "stream", "brook", "creek", "waterfall", "current of water",
      "meltwater", "rapids", "babbling", "trickle", "trickling", "dripping",
      "drip of", "fountain", "spring water"), "Mountain Stream"),
    (("birdsong", "dawn chorus", "the birds", "sparrow", "a robin", "a wren",
      "nightingale", "wind", "breeze", "forest", "meadow", "rustle", "leaves",
      "branches", "in the grass", "pine"), "Forest Wind"),
    (("cafe", "coffee house", "teahouse", "kettle", "the cup", "a cup",
      "murmur of voices", "lamplit"), "Cafe Murmur"),
    (("star", "galaxy", "galaxies", "cosmos", "the cosmos", "outer space",
      "the void", "abyss", "deep ocean", "the deep sea", "night sky",
      "the heavens", "interstellar"), "Brown Noise"),
    (("snow", "glacier", "the ice", "icy", "frozen", "hush", "stillness",
      "silence"), "Pink Noise"),
]


def match_themes(text, themes):
    """First label in *themes* (a list of ``(triggers, label)``) whose imagery
    appears in *text*, else ``None``. A single-word trigger matches a **whole word**
    (or its simple +s/+es plural), so it never fires on a longer unrelated word
    ("rain" not "train"); a trigger containing a space matches as a phrase
    (substring). Shared by ``cue_for_text`` (ambience beds) and the GUI's
    ``story_bg.bg_for_text`` (backdrops), so both match imagery the same way."""
    if not text:
        return None
    low = str(text).lower()
    words = set(_WORD.findall(low))
    for triggers, label in themes:
        for t in triggers:
            if " " in t:
                if t in low:
                    return label
            elif t in words or (t + "s") in words or (t + "es") in words:
                return label
    return None


def cue_for_text(text):
    """Return an ambient voice name matching the imagery in *text*, or None."""
    return match_themes(text, _CUES)


def next_bed(current, base, cue, pending):
    """Pick the next text-following target after a narrated line, with anti-thrash
    hysteresis. Shared by the **ambience bed** (a nature voice) and the **story
    backdrop** (a named background) -- the logic is the same for both.

    *current* = the target in use (the cued one or the story's *base*), *cue* = the
    target this line's imagery calls for (or ``None``), *pending* = a candidate left
    over from the previous line. Returns ``(new_current, new_pending)``.

    A first cue **blooms in** from the base immediately (nice), but switching from
    one cued bed to a *different* one requires the new bed to recur on the next
    cueing line -- so a single stray image (e.g. one "fire" line amid water
    imagery) never thrashes the bed back and forth with crossfades. ``cue=None``
    leaves the bed alone (the caller eases home over a run of abstract lines)."""
    if not cue:
        return current, None
    if cue == current:
        return current, None
    if current is None or current == base:
        return cue, None                       # bloom the imagery in from the base
    if cue == pending:
        return cue, None                       # the new image persisted -> switch beds
    return current, cue                        # first sight of a new image -> hold, remember it
