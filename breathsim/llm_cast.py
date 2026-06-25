"""Optional LLM **cast director** -- it refines a book's cast when (and only when)
the user has configured a backend. Opt-in, validated, **fail-closed**.

It pre-reads a *sample* of the book (the opening + a couple of middle slices --
never the whole novel) and asks the model for a small JSON cast: for each speaking
character, a fitting 2D **character**, an optional **costume**, a short voice
description and an emotion. The reply is **untrusted**: it is parsed defensively
and every field is **validated + clamped against the allowed registries** (the
caller passes the legal character + costume name lists, so this module never
imports the GUI); anything unknown is dropped and filled from the heuristic
:func:`breathsim.bookcast.script` casting. On ANY error, malformed JSON, or no
backend it returns the pure heuristic cast -- it never raises and never blocks.

The result is cached **once per book** in ``~/.breathsim/casts.json`` so the
pre-read happens a single time. ``vesper/cast.build_cast`` prefers a saved cast.
"""
from __future__ import annotations

import json
import os
import re

from . import bookcast, llm, store

CASTS = os.path.join(store.DIR, "casts.json")   # {book_id: {"cast": {...}, "source": ...}}
_MAX_SAMPLE = 6000          # chars of book text sent to the model (a small sample)
_CHUNK = 2000


# --- per-book persistence (own file; keeps store.py untouched) --------------

def _read():
    try:
        with open(CASTS) as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(d):
    try:
        os.makedirs(store.DIR, exist_ok=True)
        with open(CASTS, "w") as fh:
            json.dump(d, fh)
    except OSError:
        pass


def load_cast(book_id):
    """The saved cast for a book (speaker -> {character, costume, voice, emotion})
    or None."""
    e = _read().get(book_id)
    return e.get("cast") if isinstance(e, dict) else None


def save_cast(book_id, cast, source="llm"):
    d = _read()
    d[book_id] = {"cast": cast, "source": source}
    _write(d)


def delete_cast(book_id):
    d = _read()
    d.pop(book_id, None)
    _write(d)


# --- sample + prompt + parse + validate -------------------------------------

def _sample(book):
    sents = book.sentences() if hasattr(book, "sentences") else list(book)
    text = " ".join(sents)
    if len(text) <= _MAX_SAMPLE:
        return text
    parts = [text[:_CHUNK]]
    for f in (0.4, 0.7):                          # a couple of middle slices
        i = int(len(text) * f)
        parts.append(text[i:i + _CHUNK])
    return "\n[...]\n".join(parts)


def _heuristic(book, characters):
    """The CAST-2 heuristic cast keyed speaker -> {character, voice, costume, emotion}."""
    sc = bookcast.script(book, pool=characters)
    base = {sp: {"character": info["character"], "voice": info.get("voice", ""),
                 "costume": "None", "emotion": "neutral"}
            for sp, info in sc["cast"].items()}
    return base, sc.get("speakers", [])


def _prompt(sample, speakers, characters, costumes):
    return (
        "You are gently casting a soothing bedtime audiobook. Here is a short "
        "sample of the book:\n\n" + sample[:_MAX_SAMPLE] + "\n\nThe speaking "
        "characters are: " + ", ".join(speakers) + ".\nReturn ONLY strict JSON, "
        "no prose, of exactly this shape:\n"
        '{"cast": {"<speaker name>": {"character": "<one of the allowed '
        'characters>", "costume": "<one of the allowed costumes>", "voice": "<a '
        'short calm voice description>", "emotion": "<one word>"}}}\n'
        "The character MUST be exactly one of: " + ", ".join(characters) + ".\n"
        "The costume MUST be exactly one of: " + ", ".join(costumes) + ".\n"
        "Choose a fitting, calm character (and optional costume) for each speaker; "
        "keep everything soothing and sleepy.")


def _parse(text):
    if not isinstance(text, str):
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def validate_cast(raw, speakers, characters, costumes, base):
    """Clamp the model's cast to the allowed registries, filling gaps from *base*
    (the heuristic). Unknown character/costume -> the heuristic / 'None'."""
    chars, costs = set(characters), set(costumes)
    rc = (raw or {}).get("cast") if isinstance(raw, dict) else None
    rc = rc if isinstance(rc, dict) else {}
    out = {}
    for sp in speakers:
        b = base.get(sp, {})
        m = rc.get(sp) if isinstance(rc.get(sp), dict) else {}
        ch = m.get("character")
        if ch not in chars:
            ch = b.get("character")
        co = m.get("costume")
        if co not in costs:
            co = b.get("costume", "None")
        voice = str(m.get("voice") or b.get("voice", ""))[:48]
        emo = (str(m.get("emotion") or b.get("emotion", "neutral"))
               .strip().lower()[:16] or "neutral")
        out[sp] = {"character": ch, "costume": co, "voice": voice, "emotion": emo}
    return out


def direct(book, characters, costumes, complete=None, save=True):
    """Refine *book*'s cast with the LLM (opt-in). Always returns a cast dict;
    **fails closed** to the pure heuristic on any error / no backend. Caches the
    result per book when *save*."""
    base, speakers = _heuristic(book, characters)
    if not speakers:
        return {}
    comp = complete or (llm.complete if llm.available() else None)
    if comp is None:                              # no backend -> heuristic
        return base
    try:
        raw = _parse(comp(_prompt(_sample(book), speakers, characters, costumes),
                          max_tokens=900))
        cast = validate_cast(raw, speakers, characters, costumes, base)
    except Exception:
        cast = base
    if save and getattr(book, "id", None):
        save_cast(book.id, cast, source=("llm" if cast != base else "heuristic"))
    return cast
