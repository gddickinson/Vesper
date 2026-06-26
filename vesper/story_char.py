"""Map a bedtime-story scene / lecture to a fitting cartoon character, so the
talking-head storyteller can *look* the part (a cosy bear for a hibernation tale,
a wise owl for the night sky, a penguin for the sea...). Opt-in and gentle: only
used when the cartoon face is shown and the "Character follows the story" toggle is
on, and the user's own chosen character is restored afterwards. Pure + testable.
"""
from __future__ import annotations

import re

_WORD = re.compile(r"[a-z]+")

# (character, trigger words). First match wins, so the more specific / leading
# themes come first. Covers most of the cast; Skull, Woman and Man are
# left out on purpose -- they stay deliberate manual picks (the Skull especially).
_THEMES = [
    # pastoral + sleep: the shepherd / lullaby tales -- lead so "night" can't grab them
    ("Sheep", ("sheep", "shepherd", "flock", "wool", "lamb", "fleece",
               "lullab", "pasture", "meadow", "dream")),
    # the sleepiest narrator of all -- the explicit sleep/slowness themes
    ("Sloth", ("sleep", "asleep", "slumber", "doze", "drowsy", "nap", "snooze",
               "siesta", "slow", "lazy", "yawn", "hammock", "rest", "sloth")),
    ("Penguin", ("sea", "ocean", "tide", "wave", "coast", "seaside", "surf",
                 "coral", "whale", "iceberg", "antarctic", "arctic", "polar",
                 "lighthouse", "harbour", "harbor")),
    # the wintry narrator: snow / frost / ice phenomena. Placed after Penguin (which
    # keeps the polar sea -- iceberg / arctic) and before Duckling (so "The Frozen
    # Lake" follows "frozen" here, not "lake" there); Bear below keeps the woodland.
    ("Snowman", ("snow", "winter", "wintr", "frost", "frozen", "freez", "freezing",
                 "icicle", "icy", "ice", "blizzard", "snowman", "snowflake",
                 "sleet", "flurr")),
    ("Duckling", ("river", "pond", "lake", "stream", "rain", "duck", "marsh",
                  "wetland", "canal")),
    ("Frog", ("swamp", "jungle", "rainforest", "lily", "bog", "mangrove")),
    ("Bunny", ("flower", "spring", "blossom", "petal", "clover", "dew", "seed",
               "bloom")),
    ("Hedgehog", ("hedge", "burrow", "bramble", "thicket", "autumn", "leaf",
                  "leaves", "acorn", "moss")),
    ("Fox", ("garden", "hill", "field", "vine", "orchard", "spice", "tea",
             "coffee", "grass", "savanna")),
    ("Bear", ("forest", "wood", "mountain", "cave", "hibernat",
              "honey", "pine", "taiga", "den")),       # snow/winter -> Snowman above
    ("Panda", ("bamboo", "panda", "jade")),
    ("Mouse", ("small", "tiny", "little", "micro", "miniature", "crumb",
               "grain", "pebble", "speck", "attic")),
    ("Chicken", ("dawn", "morning", "sunrise", "wake", "farm", "barn", "egg",
                 "rooster", "harvest")),
    ("Robot", ("machine", "clockwork", "engine", "factory", "metal", "circuit",
               "robot", "train", "railway", "loom", "forge", "blacksmith",
               "gear", "iron", "steel", "glass", "bridge")),
    ("Dog", ("journey", "voyage", "road", "trail", "path", "compass", "caravan",
             "travel", "wander", "walk", "watchman", "watch", "guard")),
    ("Cat", ("cottage", "home", "hearth", "fire", "cafe", "candle", "blanket",
             "quilt", "lamp", "lantern", "kitchen", "bread", "oven", "bake",
             "warm", "purr")),
    # the moon herself narrates the moon's own tales (before Owl, who keeps the
    # wider night sky -- stars, constellations, planets, the cosmos)
    ("Luna", ("moon", "lunar", "luna", "crescent", "eclipse")),
    ("Owl", ("night", "star", "sky", "cosmos", "galaxy", "planet",
             "constellation", "comet", "nebula", "owl", "midnight", "library",
             "philosoph", "wisdom")),
]
DEFAULT = "Owl"                                   # a calm, wise night-time narrator


def char_for_scene(scene) -> str:
    """The cartoon character that best fits *scene* (a story scene or lecture name).
    A trigger matches when it is the **start of a word** in the scene -- so stems
    work (``hibernat`` -> "hibernation") without false hits inside other words
    (``rain`` must not match "t-rain"). First theme with any match wins."""
    if not scene:
        return DEFAULT
    words = _WORD.findall(str(scene).lower())
    for name, triggers in _THEMES:
        if any(wd.startswith(t) for wd in words for t in triggers):
            return name
    return DEFAULT
