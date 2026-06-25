"""Pure, human-friendly **descriptions** of a book -- so a reader can judge one
*before* downloading and see at a glance how long it is *after*.

No network, no Qt, no disk writes (``library_report`` only *reads* the index via
:mod:`books`). The networked search/download live in :mod:`booksource`; storage
in :mod:`books`. Everything here is deterministic and unit-tested offline.

Three signals, from three sources:
  * **popularity** -- Project Gutenberg's ``download_count`` (a good proxy for
    "is this a well-known, well-transcribed edition"); free, comes with search;
  * **language** -- the ISO code(s) Gutendex returns, spelled out;
  * **length** -- estimated narration time, from a byte *size* (a pre-download
    probe) or, once saved, the exact sentence/character count.
"""
from __future__ import annotations

# Calm narration runs slower than silent reading. ~140 spoken words/minute, and
# (for English prose) roughly one word per 5.9 characters including spaces.
_WORDS_PER_MIN = 140.0
_CHARS_PER_WORD = 5.9
_WORDS_PER_SENTENCE = 18.0          # literary average, when only a count is known

_LANGUAGES = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "la": "Latin",
    "el": "Greek", "ru": "Russian", "fi": "Finnish", "sv": "Swedish",
    "da": "Danish", "no": "Norwegian", "hu": "Hungarian", "pl": "Polish",
    "cs": "Czech", "ja": "Japanese", "zh": "Chinese", "ar": "Arabic",
    "he": "Hebrew", "tl": "Tagalog", "eo": "Esperanto", "cy": "Welsh",
    "ga": "Irish", "is": "Icelandic", "ca": "Catalan", "ro": "Romanian",
}


# --- popularity ------------------------------------------------------------

def popularity(download_count):
    """Map a Gutenberg ``download_count`` to ``(label, stars)`` (stars 0..3).
    None/unknown -> a neutral, star-free label."""
    try:
        n = int(download_count)
    except (TypeError, ValueError):
        return ("popularity unknown", 0)
    if n >= 5000:
        return ("very popular", 3)
    if n >= 1000:
        return ("popular", 2)
    if n >= 100:
        return ("known", 1)
    return ("rarely read", 0)


def popularity_label(download_count):
    """Just the words (e.g. 'very popular'), with a star prefix for the top tiers.
    Stars are a GUI-only glyph (never narrated)."""
    label, stars = popularity(download_count)
    return (("★" * stars + " ") if stars else "") + label


# --- language --------------------------------------------------------------

def language_label(languages):
    """Spell out an ISO language list (``['en']`` -> 'English'). Accepts a list,
    a single code or None; unknown codes pass through upper-cased."""
    if isinstance(languages, str):
        languages = [languages]
    if not languages:
        return ""
    names = [_LANGUAGES.get((c or "").lower(), (c or "").upper())
             for c in languages if c]
    return ", ".join(n for n in names if n)


# --- length / narration time ----------------------------------------------

def estimate_minutes(chars=None, sentences=None, words=None):
    """Estimated calm-narration minutes from whatever is known (prefer chars >
    words > sentences). Returns 0 when nothing usable is given."""
    if words is None:
        if chars:
            words = float(chars) / _CHARS_PER_WORD
        elif sentences:
            words = float(sentences) * _WORDS_PER_SENTENCE
        else:
            return 0
    return max(0, int(round(float(words) / _WORDS_PER_MIN)))


def format_duration(minutes):
    """A short, friendly duration: '~12 min', '~3 h', '~12.5 h'."""
    m = int(round(minutes or 0))
    if m <= 0:
        return ""
    if m < 90:
        return f"~{m} min"
    hours = m / 60.0
    return f"~{hours:.0f} h" if abs(hours - round(hours)) < 0.1 else f"~{hours:.1f} h"


def length_label(minutes):
    """A qualitative size band + duration, e.g. 'medium (~6 h)'."""
    m = minutes or 0
    if m <= 0:
        return ""
    band = ("very short" if m < 60 else "short" if m < 240
            else "medium" if m < 600 else "long" if m < 1200 else "epic")
    return f"{band} ({format_duration(m)})"


def length_from_bytes(byte_size):
    """Pre-download estimate: a UTF-8 text byte size -> a length label (chars ~=
    bytes for mostly-ASCII books). Empty when size is unknown."""
    if not byte_size:
        return ""
    return length_label(estimate_minutes(chars=byte_size))


def format_size(byte_size):
    """Human bytes: '812 KB', '1.4 MB'. Empty for unknown/zero."""
    n = float(byte_size or 0)
    if n <= 0:
        return ""
    if n < 1024:
        return f"{int(n)} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


# --- compact descriptions for the GUI --------------------------------------

def describe_result(result):
    """One compact line for a *search result* row (pre-download): popularity and
    language, plus an estimated length if a probed ``byte_size`` is present."""
    bits = []
    pl = popularity_label((result or {}).get("download_count"))
    if pl and pl != "popularity unknown":
        bits.append(pl)
    lang = language_label((result or {}).get("languages"))
    if lang and lang != "English":          # English is the default; don't clutter
        bits.append(lang)
    length = length_from_bytes((result or {}).get("byte_size"))
    if length:
        bits.append(length)
    return "  -  ".join(bits)


def describe_book(meta):
    """One compact line for a *saved library* entry: exact sentence count + an
    estimated narration length, and a percent-read marker handled by the caller."""
    n = int((meta or {}).get("sentences", 0) or 0)
    if not n:
        return "empty"
    mins = estimate_minutes(sentences=n)
    dur = format_duration(mins)
    s = f"{n:,} sentences"
    return f"{s}  -  {dur}" if dur else s


# --- a small library report for the management UI --------------------------

def library_report(books_module=None):
    """A summary of the local library: ``{count, sentences, minutes, bytes}``.
    Reads the index + on-disk sizes via :mod:`books` (no writes)."""
    if books_module is None:
        from . import books as books_module
    idx = books_module.list_books()
    count = len(idx)
    sentences = sum(int(b.get("sentences", 0) or 0) for b in idx)
    byte_total = 0
    for b in idx:
        try:
            byte_total += books_module.disk_bytes(b.get("id"))
        except Exception:
            pass
    return {"count": count, "sentences": sentences,
            "minutes": estimate_minutes(sentences=sentences), "bytes": byte_total}


def report_line(report):
    """A one-line summary of :func:`library_report`, e.g.
    '3 books  -  ~28 h of reading  -  4.1 MB'."""
    n = report.get("count", 0)
    if not n:
        return "Your library is empty."
    parts = [f"{n} book" + ("" if n == 1 else "s")]
    dur = format_duration(report.get("minutes", 0))
    if dur:
        parts.append(f"{dur} of reading")
    size = format_size(report.get("bytes", 0))
    if size:
        parts.append(size)
    return "  -  ".join(parts)
