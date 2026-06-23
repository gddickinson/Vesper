"""Match imagery in narrated text to a soothing ambient sound.

Lets the bedtime storyteller's soundscape gently *follow the words*: when a line
speaks of rain, waves, wind, a hearth, stars... the ambience bed crossfades to a
matching sound, holding it through the imagery and easing back to the story's base
ambience over abstract passages. All targets are always-registered procedural
GROUP_NATURE voices, so this works with no downloaded assets. Pure + testable.
"""
from __future__ import annotations

# (keywords, ambient voice). First match wins; ordered most- to least-specific.
# Keys are matched as substrings of the lowercased line, chosen to avoid common
# false hits (no bare "sea"/"room"/"season").
_CUES = [
    (("thunder", "storm", "lightning", "tempest"), "Distant Thunder"),
    (("purr", "purring", "a cat", "the cat", "kitten", "tabby", "whiskers"),
     "Purr"),
    (("wind chime", "wind chimes"), "Wind Chimes"),
    (("temple bell", "church bell", "the bells", "bell rang", "bell tolled",
      "singing bowl", "gong", "chimes", "a chime", "tolling"), "Singing Bowl"),
    (("cricket", "fireflies", "firefly", "summer night", "night insects",
      "chirp"), "Night Crickets"),
    (("campfire", "bonfire", "fireplace", "fireside", "hearth", "crackl",
      "the flames", "candlelight", "candle flame", "glowing coals"), "Campfire"),
    (("on the roof", "against the window", "against the pane", "under the eaves",
      "the eaves", "patter of rain", "rain on the"), "Rain on a Roof"),
    (("wave", "ocean", "tide", "surf", "seashore", "breaker", "the surf"),
     "Ocean Waves"),
    (("rain", "drizzle", "downpour", "rainfall"), "Soft Rainstorm"),
    (("river", "stream", "brook", "creek", "waterfall", "current of water",
      "meltwater", "rapids", "babbling"), "Mountain Stream"),
    (("birdsong", "dawn chorus", "the birds", "sparrow", "a robin", "a wren",
      "nightingale", "wind", "breeze", "forest", "meadow", "rustle", "leaves",
      "branches", "in the grass", "pine"), "Forest Wind"),
    (("cafe", "coffee house", "teahouse", "kettle", "the cup", "a cup",
      "murmur of voices", "lamplit"), "Cafe Murmur"),
    (("star", "galaxy", "cosmos", "the cosmos", "outer space", "the void",
      "abyss", "deep ocean", "the deep sea", "night sky", "the heavens",
      "interstellar"), "Brown Noise"),
    (("snow", "glacier", "the ice", "icy", "frozen", "hush", "stillness",
      "silence"), "Pink Noise"),
]


def cue_for_text(text):
    """Return an ambient voice name matching the imagery in *text*, or None."""
    if not text:
        return None
    t = str(text).lower()
    for keys, voice in _CUES:
        for k in keys:
            if k in t:
                return voice
    return None
