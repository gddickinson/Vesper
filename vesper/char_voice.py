"""Per-character voice + personality profiles. Each character gets a fitting
narrator voice (chosen from whatever the active TTS engine offers, by ordered
name/prefix hints that work for both Kokoro ids like ``af_heart`` and macOS
``say`` names like ``Samantha``), a speaking-rate multiplier, a signature greeting
and a signature eye/aura hue. Pure + testable; the window applies it when the
"Character voices" toggle is on.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CharVoice:
    hints: tuple             # ordered voice name/prefix hints (first match wins)
    rate: float = 1.0        # speaking-rate multiplier
    hue: str = "#86e6bf"     # signature eye + aura glow
    greeting: str = ""
    persona: str = ""
    xtts: str = ""           # preferred XTTS studio speaker (used when installed)


_F_SOFT = ("af_heart", "af_", "bf_", "samantha", "karen", "fiona", "moira")
_F_BRIGHT = ("bf_", "af_sky", "af_", "tessa", "kate", "karen")
_M_WARM = ("am_adam", "am_", "bm_", "daniel", "alex", "tom")
_M_DEEP = ("bm_george", "bm_", "am_michael", "am_", "lee", "daniel")

VOICES = {
    "Cat": CharVoice(_F_SOFT, 1.0, "#86e6bf",
                     "Mrrp. Let's find some calm together.", "soft and warm",
                     xtts="Daisy Studious"),
    "Penguin": CharVoice(_F_BRIGHT, 1.06, "#7fd0ff",
                         "Waddle in and settle down.", "chipper and tidy",
                         xtts="Sofia Hellen"),
    "Dog": CharVoice(_M_WARM, 1.0, "#ffd27a",
                     "Good to see you. Let's breathe.", "loyal and friendly",
                     xtts="Luis Moray"),
    "Owl": CharVoice(_M_DEEP, 0.9, "#b9a0ff",
                     "Whoo's ready to rest? Settle in.", "wise and unhurried",
                     xtts="Damien Black"),
    "Fox": CharVoice(("af_nicole", "af_", "bf_", "nicky", "samantha"), 1.05,
                     "#ffb04a", "Sly and serene -- let's begin.", "clever and calm",
                     xtts="Alison Dietlinde"),
    "Chicken": CharVoice(_F_BRIGHT, 1.12, "#ffd86b",
                         "Cluck. Time to unwind.", "busy but kind",
                         xtts="Henriette Usha"),
    "Bunny": CharVoice(("af_heart", "af_", "bf_", "samantha"), 1.05, "#f4a6cf",
                       "Hop in, soft and slow.", "gentle and shy",
                       xtts="Gracie Wise"),
    "Bear": CharVoice(("bm_", "am_michael", "am_", "daniel", "lee"), 0.88,
                      "#ffcf8a", "Mmm. Let's hibernate the stress away.",
                      "deep and cosy", xtts="Aaron Dreschner"),
    "Panda": CharVoice(("am_", "bm_", "daniel", "alex"), 0.95, "#9fe8ff",
                       "Easy does it. Breathe.", "mellow and content",
                       xtts="Kumar Dahl"),
    "Frog": CharVoice(("am_fenrir", "am_", "fred", "junior"), 1.05, "#9be86b",
                      "Ribbit. Breathe with me.", "playful and bouncy",
                      xtts="Marcos Rudaski"),
    "Duckling": CharVoice(("af_sky", "bf_", "af_", "junior", "tessa"), 1.13,
                          "#ffe27a", "Peep! Let's be calm together.",
                          "tiny and eager", xtts="Ana Florence"),
    "Hedgehog": CharVoice(("af_", "bf_", "tom", "daniel"), 1.0, "#d8b27a",
                          "Curl up cosy with me.", "small and snug",
                          xtts="Tammie Ema"),
    "Mouse": CharVoice(("af_sky", "af_", "bf_", "tessa", "samantha"), 1.12,
                       "#c8d2de", "Squeak. Let's be still and small together.",
                       "tiny and gentle", xtts="Ana Florence"),
    "Sheep": CharVoice(("af_heart", "af_", "bf_", "moira", "fiona"), 0.96,
                       "#eef0f2", "Soft as wool, let's drift off.",
                       "fluffy and calm", xtts="Gracie Wise"),
    "Sloth": CharVoice(("af_heart", "af_", "bf_", "fiona", "moira"), 0.80,
                       "#e8c98a", "Mmm... there's no hurry at all. Let's go slow.",
                       "slow, dreamy and content", xtts="Gracie Wise"),
    "Koala": CharVoice(("af_heart", "af_", "bf_", "moira", "fiona"), 0.82,
                       "#a9d6b0", "Mmm... let's find a quiet branch and rest.",
                       "dozy, soft and gentle", xtts="Gracie Wise"),
    "Red Panda": CharVoice(("af_sky", "af_", "bf_", "tessa", "samantha"), 1.0,
                           "#ff9a5a", "Let's curl up snug and breathe slow.",
                           "warm, cosy and bright", xtts="Tammie Ema"),
    "Snowman": CharVoice(("am_adam", "am_", "bm_", "daniel", "tom"), 0.92,
                         "#aee0ff", "Brr -- let's keep cosy and breathe slow.",
                         "cool, calm and kindly", xtts="Viktor Eka"),
    "Robot": CharVoice(("am_michael", "bm_lewis", "bm_", "am_", "fred", "ralph",
                        "daniel"), 0.97, "#4fd6ff",
                       "Beep. Systems calm. Let us begin.",
                       "level and synthetic", xtts="Royston Min"),
    "Woman": CharVoice(("af_bella", "af_", "bf_emma", "bf_", "samantha",
                        "victoria"), 1.0, "#86e6bf",
                       "Hello. Let's take a moment together.", "warm and human",
                       xtts="Claribel Dervla"),
    "Man": CharVoice(("am_michael", "am_", "bm_daniel", "bm_", "daniel", "alex"),
                     1.0, "#86e6bf", "Hey. Let's slow down together.",
                     "warm and human", xtts="Viktor Eka"),
    "Skull": CharVoice(("bm_george", "bm_", "am_michael", "am_", "lee", "daniel"),
                       0.84, "#9fe6dc",
                       "Gather close. I have a quiet old tale to tell.",
                       "deep, slow and hollow", xtts="Damien Black"),
}

DEFAULT = CharVoice(("af_", "bf_"), 1.0, "#86e6bf", "", "")


def get(name):
    """The CharVoice profile for *name* (a gentle default for unknowns)."""
    return VOICES.get(name, DEFAULT)


def pick_voice(hints, available):
    """The first voice in *available* matching a hint (case-insensitive, in hint
    order), or None to leave the current voice. Works for Kokoro ids + say names."""
    av = [v for v in (available or []) if v]
    low = [(v, v.lower()) for v in av]
    for h in hints:
        h = h.lower()
        for v, vl in low:
            if h in vl:
                return v
    return None
