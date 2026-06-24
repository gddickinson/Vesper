"""Map a narrated line to a fitting animated backdrop, so the picture quietly
follows the tale (a hearth glows on a fire line, stars on a night-sky line, rain
on a storm line...). Mirrors :mod:`breathsim.sound_cues` so the picture and the
soundscape move together. Pure + testable; returns a `face_bg` name or ``None``.

Kept deliberately gentle: only clear imagery switches the scene, and the caller
crossfades slowly and eases home over abstract passages, so it never startles.
"""
from __future__ import annotations

# (face_bg name, trigger words). Order matters -- first match wins, so the more
# specific / evocative families come first.
_THEMES = [
    ("Embers", ("fire", "flame", "hearth", "ember", "candle", "lantern",
                "fireplace", "coal", "forge", "furnace", "campfire", "glow of the",
                "warm light", "firelight")),
    ("Aurora", ("aurora", "northern light", "southern light")),
    ("Nebula", ("nebula", "stardust", "deep space", "the void", "cosmos", "cosmic",
                "galaxy", "galaxies", "interstellar")),
    ("Stars", ("star", "stars", "starry", "night sky", "moon", "moonlight",
               "constellation", "comet", "planet", "the heavens", "midnight sky",
               "milky way")),
    ("Rain", ("rain", "drizzle", "downpour", "shower", "storm", "thunder",
              "raindrop", "puddle", "snow", "snowfall", "sleet", "frost",
              "blizzard", "the rain")),
    ("Underwater", ("sea", "ocean", "wave", "tide", "shore", "river", "stream",
                    "lake", "water", "harbour", "harbor", "coral", "current",
                    "the deep", "rippl", "lagoon", "brook")),
    ("Forest", ("forest", "tree", "trees", "wood", "woods", "leaf", "leaves",
                "meadow", "grass", "garden", "moss", "fern", "glade", "pine",
                "oak", "branch", "blossom", "petal", "hedgerow", "orchard")),
    ("City", ("city", "street", "town", "market", "cafe", "café", "window",
              "rooftop", "lane", "square", "alley", "lamplit", "tavern", "shop",
              "cottage", "village", "courtyard")),
]

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
    abstract (no clear scene)."""
    if not text:
        return None
    low = text.lower()
    for name, words in _THEMES:
        for wd in words:
            if wd in low:
                return name
    return None


def base_for_scene(scene) -> str:
    """A calm base backdrop for a story scene/lecture (the home to ease back to)."""
    if not scene:
        return DEFAULT_BASE
    return _SCENE_BASE.get(scene, DEFAULT_BASE)
