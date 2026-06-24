"""Map a bedtime-story scene / lecture to a fitting cartoon character, so the
talking-head storyteller can *look* the part (a cosy bear for a hibernation tale,
a wise owl for the night sky, a penguin for the sea...). Opt-in and gentle: only
used when the cartoon face is shown and the "Character follows the story" toggle is
on, and the user's own chosen character is restored afterwards. Pure + testable.
"""
from __future__ import annotations

# (character, trigger words). First match wins; more specific themes lead.
_THEMES = [
    ("Penguin", ("sea", "ocean", "tide", "wave", "coast", "seaside", "coral",
                 "whale", "iceberg", "antarctic", "harbour", "harbor")),
    ("Duckling", ("river", "pond", "lake", "stream", "rain", "duck", "marsh")),
    ("Owl", ("night", "star", "sky", "moon", "cosmos", "galaxy", "planet",
             "constellation", "comet", "nebula", "owl", "midnight", "library")),
    ("Bear", ("forest", "wood", "mountain", "cave", "winter", "hibernat",
              "honey", "pine", "snow", "taiga")),
    ("Fox", ("meadow", "garden", "hill", "field", "autumn", "harvest", "vine",
             "orchard", "spice", "tea", "coffee")),
    ("Bunny", ("flower", "spring", "blossom", "petal", "clover", "dew", "seed")),
    ("Cat", ("cottage", "home", "hearth", "fire", "cafe", "café", "candle",
             "blanket", "quilt", "lamp", "kitchen")),
    ("Frog", ("swamp", "jungle", "rainforest", "lily", "bog")),
]
DEFAULT = "Owl"                                   # a calm, wise night-time narrator


def char_for_scene(scene) -> str:
    """The cartoon character that best fits *scene* (a story scene or lecture name)."""
    if not scene:
        return DEFAULT
    low = str(scene).lower()
    for name, words in _THEMES:
        for wd in words:
            if wd in low:
                return name
    return DEFAULT
