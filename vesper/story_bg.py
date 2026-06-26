"""Map a narrated line to a fitting animated backdrop, so the picture quietly
follows the tale (a hearth glows on a fire line, stars on a night-sky line, rain
on a storm line...). Mirrors :mod:`breathsim.sound_cues` so the picture and the
soundscape move together. Pure + testable; returns a `face_bg` name or ``None``.

Kept deliberately gentle: only clear imagery switches the scene, and the caller
crossfades slowly and eases home over abstract passages, so it never startles.
"""
from __future__ import annotations

from breathsim import sound_cues

# (face_bg name, trigger words/phrases). Order matters -- first match wins, so the
# more specific / evocative families come first. Single-word triggers match WHOLE
# words (plus a simple +s/+es plural), so e.g. "star" never fires on "start" or
# "stared" and "tree" never fires on "street"; triggers with a space match as a
# phrase (substring). Inflections we care about are listed explicitly.
_THEMES = [
    ("Embers", ("fire", "fires", "flame", "hearth", "ember", "candle", "lantern",
                "fireplace", "coal", "forge", "furnace", "campfire", "glow of the",
                "warm light", "firelight", "firelit")),
    ("Aurora", ("aurora", "northern light", "southern light")),
    ("Nebula", ("nebula", "stardust", "deep space", "the void", "cosmos", "cosmic",
                "galaxy", "galaxies", "interstellar")),
    ("Stars", ("star", "starry", "starlight", "starlit", "night sky", "moon",
               "moonlight", "moonlit", "constellation", "comet", "planet",
               "the heavens", "midnight sky", "milky way")),
    ("Rain", ("rain", "rainfall", "raindrop", "drizzle", "downpour", "shower",
              "storm", "thunder", "puddle", "snow", "snowfall", "sleet", "frost",
              "blizzard", "the rain")),
    ("Underwater", ("sea", "ocean", "wave", "tide", "shore", "river", "stream",
                    "lake", "water", "waterfall", "harbour", "harbor", "coral",
                    "current", "the deep", "ripple", "lagoon", "brook")),
    ("Forest", ("forest", "tree", "wood", "woods", "leaf", "leaves",
                "meadow", "grass", "garden", "moss", "fern", "glade", "pine",
                "oak", "branch", "blossom", "petal", "hedgerow", "orchard")),
    ("City", ("city", "street", "town", "market", "cafe", "window",
              "rooftop", "lane", "square", "alley", "lamplit", "tavern", "shop",
              "cottage", "village", "courtyard")),
]

# (triggers, label) view for the shared matcher (which takes triggers-first, the
# way `sound_cues._CUES` is ordered); `_THEMES` stays label-first for readability.
_MATCH = [(triggers, name) for name, triggers in _THEMES]

# Story scenes -> a calm base backdrop to ease home toward between cues.
_SCENE_BASE = {
    "Rainy Cottage": "Rain",
    "Seaside": "Underwater",
    "Riverside": "Underwater",
    "Quiet Cafe": "City",
    "Quiet Café": "City",
    "Night Meadow": "Forest",
}
DEFAULT_BASE = "Stars"


def bg_for_text(text: str):
    """The backdrop best matching the imagery in *text*, or ``None`` if the line is
    abstract (no clear scene). Uses the shared ``sound_cues.match_themes`` whole-word
    matcher (so a single-word trigger never fires on a longer unrelated word -- "star"
    not "start", "tree" not "street"; space-containing triggers match as a phrase)."""
    return sound_cues.match_themes(text, _MATCH)


def base_for_scene(scene) -> str:
    """A calm base backdrop for a story scene/lecture (the home to ease back to)."""
    if not scene:
        return DEFAULT_BASE
    return _SCENE_BASE.get(scene, DEFAULT_BASE)
