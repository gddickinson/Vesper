"""Map a bedtime-story scene / lecture to a fitting cartoon character *and* a
fitting costume, so the talking-head storyteller can *look* the part (a cosy bear
for a hibernation tale, a wise owl in a mortarboard for a library, a cat in a chef
hat for a baking tale, a space-helmeted face for a tale of orbit...). Opt-in and
gentle: only used when the cartoon face is shown and the "Character follows the
story" toggle is on, and the user's own character + costume are restored
afterwards. Pure + testable.
"""
from __future__ import annotations

import re

_WORD = re.compile(r"[a-z]+")


def _matches(words, triggers):
    """True if any *trigger* fits any word. A plain trigger matches as a word
    *prefix* (so ``hibernat`` -> "hibernation"); a trigger written ``=mars`` must
    match the *whole* word (so "mars" hits but "marsh" / "marsupial" do not)."""
    for t in triggers:
        if t.startswith("="):
            if any(wd == t[1:] for wd in words):
                return True
        elif any(wd.startswith(t) for wd in words):
            return True
    return False

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
    # a softer, rounder bot for the future / spacecraft / automaton tales (Robot
    # above keeps the industrial / machine / railway themes)
    ("Bot", ("android", "cyborg", "automaton", "satellite", "spacecraft",
             "probe", "rover")),
    ("Dog", ("journey", "voyage", "road", "trail", "path", "compass", "caravan",
             "travel", "wander", "walk", "watchman", "watch", "guard")),
    ("Cat", ("cottage", "home", "hearth", "fire", "cafe", "candle", "blanket",
             "quilt", "lamp", "lantern", "kitchen", "bread", "oven", "bake",
             "warm", "purr")),
    # the moon herself narrates the moon's own tales (before Owl, who keeps the
    # wider night sky -- stars, constellations, planets, the cosmos)
    ("Luna", ("moon", "lunar", "luna", "crescent", "eclipse")),
    # friendly visitors from elsewhere: the cyclops Martian takes the red planet
    # (=mars exact, so "marsh" stays a wetland), the green Alien takes alien tales
    ("Martian", ("martian", "=mars")),
    ("Alien", ("alien", "extraterrestrial", "ufo", "saucer", "spaceman")),
    ("Owl", ("night", "star", "sky", "cosmos", "galaxy", "planet",
             "constellation", "comet", "nebula", "owl", "midnight", "library",
             "philosoph", "wisdom")),
]
DEFAULT = "Owl"                                   # a calm, wise night-time narrator

# (costume, trigger words). Drawn ON TOP of whatever character fits, so a baking
# tale gives a cosy cat a chef hat, a library a mortarboard, a tale of orbit a
# space helmet. First match wins; "None" (no match) leaves the user's costume.
_COSTUME_THEMES = [
    ("Space Helmet", ("astronaut", "cosmonaut", "spacesuit", "spacewalk",
                      "spaceflight", "spaceship", "spacecraft", "apollo",
                      "rocket", "=orbit", "=space")),
    ("Chef Hat", ("bake", "baker", "bakery", "baking", "bread", "sourdough",
                  "pastry", "patisserie", "chef", "kitchen", "dough", "=oven",
                  "loaf", "crumb")),
    ("Crown", ("king", "queen", "royal", "throne", "palace", "emperor",
               "empress", "coronation", "monarch", "castle", "chateau",
               "fortress", "kingdom")),
    ("Pirate Hat", ("pirate", "buccaneer", "corsair", "galleon", "treasure")),
    ("Wizard Hat", ("wizard", "sorcer", "mage", "alchemy", "alchemist",
                    "enchant", "magician")),
    ("Graduation Cap", ("scholar", "university", "academy", "professor",
                        "graduat", "diploma", "librar", "scriptorium",
                        "manuscript", "scribe", "wisdom")),
    ("Police Cap", ("police", "constable", "watchman", "sentry", "patrol",
                    "gendarme")),
    ("Fire Helmet", ("firefighter", "fireman", "brigade")),
    ("Nurse Cap", ("nurse", "midwife", "infirmary")),
    ("Head Mirror", ("doctor", "physician", "surgeon", "hospital", "medicine",
                     "medical", "apothecary", "healer")),
    ("Hard Hat", ("builder", "construction", "mason", "bricklayer", "scaffold",
                  "quarry", "cement", "concrete")),
    ("Robot Aerial", ("satellite", "transmitter", "broadcast", "beacon")),
]


def char_for_scene(scene) -> str:
    """The cartoon character that best fits *scene* (a story scene or lecture name).
    Triggers match a **word prefix** (so ``hibernat`` -> "hibernation") -- or the
    whole word for ``=`` triggers. First theme with any match wins."""
    if not scene:
        return DEFAULT
    words = _WORD.findall(str(scene).lower())
    for name, triggers in _THEMES:
        if _matches(words, triggers):
            return name
    return DEFAULT


def costume_for_scene(scene) -> str:
    """A fitting costume for *scene* (drawn over the chosen character), or ``"None"``
    when nothing themed applies -- in which case the storyteller keeps the user's own
    costume. Same word-prefix / ``=`` exact matching as :func:`char_for_scene`."""
    if not scene:
        return "None"
    words = _WORD.findall(str(scene).lower())
    for costume, triggers in _COSTUME_THEMES:
        if _matches(words, triggers):
            return costume
    return "None"
