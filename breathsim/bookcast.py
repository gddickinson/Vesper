"""Turn a :class:`breathsim.books.Book` into a **cast Script** -- a heuristic,
PURE, offline (no LLM, no network) guess at *who speaks each line*, so a book can
be read by a little cast of characters instead of one flat voice.

For every sentence it decides a **speaker** (the Narrator, or a named character),
detecting quoted dialogue and "..., said Alice" / "Alice asked," attribution
(including the common case where the sentence splitter cut the tag onto the next
fragment after a ``?``/``!``). Recurring speakers are mapped **deterministically**
to distinct 2D characters + voice archetypes (same book -> same cast), and a light
ambience cue is read from :mod:`breathsim.sound_cues`. The output is consumed by
the dramatized player (a later round); this module stays pure + unit-tested.

It does NOT import the GUI -- the casting pool is a plain list of character names
(matching ``vesper/characters``) and can be overridden by the caller.
"""
from __future__ import annotations

import re

# Default casting pool (names match vesper/characters); the caller may pass its
# own. First-appearing speaker takes the first slot, etc. -> stable per book.
POOL = ["Owl", "Fox", "Bear", "Bunny", "Cat", "Mouse", "Penguin", "Dog",
        "Sheep", "Panda", "Frog", "Hedgehog", "Duckling", "Chicken", "Woman",
        "Man", "Robot"]
ARCH = ["wise_m", "clever_f", "deep_m", "soft_f", "warm_f", "tiny_f",
        "bright_f", "warm_m", "gentle_f", "mellow_m"]

_VERB = (r"said|says|asked|asks|replied|replies|whispered|murmured|cried|"
         r"shouted|called|answered|muttered|exclaimed|added|continued|began|"
         r"sighed|laughed|wondered|roared|gasped|declared|insisted|moaned")
_NAME = (r"(?:(?:Mr|Mrs|Ms|Dr|Mister|Miss|Aunt|Uncle|Captain|King|Queen|Lord|"
         r"Lady)\.? )?[A-Z][a-z]+")
# Capitalised words that are not speaker names (sentence-initial words, pronouns).
_STOP = {"The", "A", "An", "And", "But", "He", "She", "It", "They", "We", "You",
         "His", "Her", "Their", "Then", "There", "Here", "That", "This", "When",
         "If", "As", "So", "Now", "Why", "How", "What", "Who", "Yes", "No", "Oh",
         "Well", "For", "With", "At", "On", "In", "To", "Of", "All", "One"}

_RE_NAME_VERB = re.compile(r"\b(" + _NAME + r")\s+(?:" + _VERB + r")\b")
_RE_VERB_NAME = re.compile(r"\b(?:" + _VERB + r")\s+(?:the\s+)?(" + _NAME + r")\b")
_HUSH = ("whisper", "murmur", "hush", "quietly", "softly", "sleep", "drows")


def _name_of(s):
    """A speaker name attributed in sentence *s*, or None (pronouns/junk -> None)."""
    for rx in (_RE_NAME_VERB, _RE_VERB_NAME):
        m = rx.search(s)
        if m:
            name = m.group(1).strip()
            if name.split()[-1] not in _STOP:
                return name
    return None


def _emotion(text, is_dialogue):
    t = text.lower()
    if any(w in t for w in _HUSH):
        return "hush"
    if "!" in text:
        return "bright"
    if "?" in text:
        return "soft"
    return "neutral"


def _sound(text):
    try:
        from . import sound_cues
        return sound_cues.cue_for_text(text) or None
    except Exception:
        return None


def _short_tag(text):
    """True when *text* looks like a short attribution fragment ('Alice asked.')."""
    return ('"' not in text and len(text.split()) <= 8
            and _name_of(text) is not None)


def script(book, pool=None):
    """Build the cast Script for *book*. Returns a dict with ``segments`` (one per
    sentence), ``cast`` (speaker -> {character, voice}) and ``speakers`` (in cast
    order). Deterministic: the same book always casts the same way."""
    pool = list(pool) if pool else POOL
    sents = book.sentences() if hasattr(book, "sentences") else list(book)
    n = len(sents)

    # --- pass 1: speaker per sentence (with a one-sentence look-ahead) ---
    raw = []
    last = None
    for i, text in enumerate(sents):
        dialogue = '"' in text
        if dialogue:
            name = _name_of(text)
            if not name and i + 1 < n and _short_tag(sents[i + 1]):
                name = _name_of(sents[i + 1])       # tag split onto next fragment
            if name:
                speaker, last = name, name
            elif last:
                speaker = last
            else:
                speaker = "Speaker"
        else:
            speaker = "Narrator"
        raw.append((i, text, speaker, dialogue))

    # --- casting: first-appearing dialogue speaker -> first pool slot ---
    order, seen = [], set()
    for _i, _t, sp, dl in raw:
        if dl and sp != "Narrator" and sp not in seen:
            seen.add(sp)
            order.append(sp)
    cast = {sp: {"character": pool[k % len(pool)], "voice": ARCH[k % len(ARCH)]}
            for k, sp in enumerate(order)}

    segments = []
    for i, text, sp, dl in raw:
        c = cast.get(sp, {})
        segments.append({"sentence": i, "text": text, "speaker": sp,
                         "is_dialogue": dl, "character": c.get("character", ""),
                         "voice": c.get("voice", "narrator"),
                         "emotion": _emotion(text, dl), "sound": _sound(text)})
    return {"segments": segments, "cast": cast, "speakers": order,
            "dialogue_lines": sum(1 for s in segments if s["is_dialogue"]),
            "narrator_lines": sum(1 for s in segments if s["speaker"] == "Narrator")}
