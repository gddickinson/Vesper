"""Face mouth/nostril motion from the breath — shape routing + per-breath variance.

Split from ``window.py`` to keep it lifecycle-focused. Pure functions; the window's
``_face_inputs`` composes these with the talking (narration) state so speech takes
precedence over breathing.
"""
from __future__ import annotations

import random

from breathsim import voices

# Mouth *shape* per breath type, as full-airflow AU targets (scaled by airflow).
SHAPE_AUS = {
    "pursed":    {"jaw": 0.05, "pucker": 0.85, "stretch": 0.0},   # pursed-lip out
    "round":     {"jaw": 0.30, "pucker": 0.55, "stretch": 0.0},   # OM / "ooh"
    "open":      {"jaw": 0.55, "pucker": 0.0,  "stretch": 0.25},  # haa / sigh
    "fricative": {"jaw": 0.10, "pucker": 0.0,  "stretch": 0.5},   # sss / shh / fff
    "nasal":     {"jaw": 0.02, "pucker": 0.0,  "stretch": 0.0},   # nose / ujjayi
    "default":   {"jaw": 0.42, "pucker": 0.0,  "stretch": 0.12},  # generic mouth out
}


def sample_inhale_open():
    """A per-breath 0..1 scale for how far the mouth parts on an in-breath.
    Squared so it's skewed low — most breaths barely part the lips, the odd one
    opens more — which reads far more naturally than a fixed opening."""
    return random.random() ** 2


# Gentle emotion read from the narrated line: (smile, brow_raise, eye_openness)
# deltas added to a serene baseline. All small — these are soothing lectures, so
# the face only ever *shades* toward wonder / awe / curiosity / deep calm.
_MOOD = [
    (("wonder", "beautiful", "lovely", "marvel", "wondrous", "magic", "gift",
      "delight", "tender", "sweet", "grace", "glow"), (0.16, 0.10, 0.0)),
    (("vast", "enormous", "immense", "giant", "endless", "infinite", "billion",
      "huge", "towering", "boundless", "great wheel", "unimaginab"),
     (0.04, 0.22, 0.05)),
    (("strange", "mystery", "mysterious", "curious", "puzzle", "unknown",
      "stranger", "secret", "riddle", "wonder why"), (0.0, 0.16, 0.04)),
    (("rest", "sleep", "calm", "peace", "gentle", "quiet", "soft", "drift",
      "heavy", "warm", "still", "soothe", "slow", "settle", "let go"),
     (0.08, 0.0, -0.07)),
    (("sorrow", "lonely", "grief", "mourn", "lost to", "fading", "vanished",
      "long gone", "forgotten"), (-0.07, 0.05, -0.02)),
]


def emotion_for_text(text):
    """(smile, brow_raise, eye_openness) deltas matching the line's mood."""
    if not text:
        return (0.0, 0.0, 0.0)
    t = str(text).lower()
    for keys, delta in _MOOD:
        for k in keys:
            if k in t:
                return delta
    return (0.0, 0.0, 0.0)


def mouth_shape(name):
    """Classify a voice's mouth shape from its name + formant shape."""
    cfg = voices.get_voice(name) if name else None
    text = ((name or "") + " " + (getattr(cfg, "vowel", "") or "")).lower()

    def has(*ks):
        return any(k in text for k in ks)
    if has("nose", "nasal", "ujjayi", "ocean", "hum", "bhram", "nadi", "mmm"):
        return "nasal"
    if has("purs", "straw", "whistle", "blow"):
        return "pursed"
    if has("om", "ooh", "round"):
        return "round"
    if has("sss", "shh", "fff", "hiss", "fric"):
        return "fricative"
    if has("haa", "sigh", "yawn", "gasp", "aah", "open"):
        return "open"
    return "default"


def breath_routing(phase, voice_a, voice_out):
    """(jaw, pucker, stretch, nose) full-flow targets for this breath phase.
    In-breath: mostly nose (mouth closed); out-breath: mostly mouth, shaped by
    the active exhale voice; nasal voices keep the mouth closed both ways."""
    # Nostril flare is kept tiny: the only nose AU (noseSneer) also lifts the
    # upper lip, so a big value would open the mouth — the closed mouth wins.
    if phase == "inhale":
        # The jaw value here is the *maximum* parting; _face_inputs scales it by a
        # per-breath random factor so the in-breath opening varies and is usually
        # small (mouth nearly closed on a nose breath, a little wider on a gasp).
        if mouth_shape(voice_a) == "open":               # oral inhale (gasp/yawn)
            return {"jaw": 0.40, "pucker": 0.0, "stretch": 0.2, "nose": 0.08}
        return {"jaw": 0.12, "pucker": 0.0, "stretch": 0.0, "nose": 0.12}  # nose
    if phase == "exhale":
        sh = mouth_shape(voice_out or voice_a)
        au = dict(SHAPE_AUS.get(sh, SHAPE_AUS["default"]))
        au["nose"] = 0.12 if sh == "nasal" else 0.05
        return au
    return {"jaw": 0.0, "pucker": 0.0, "stretch": 0.0, "nose": 0.03}   # holds
