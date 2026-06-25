"""Find + fetch **public-domain** books on demand -- the only networked part of
the audiobook feature, and deliberately the most cautious.

SAFETY: nothing here touches the network at import or by itself. A fetch happens
ONLY when a caller (a user pressing Search / Download in the GUI) invokes
:func:`search` or :func:`download`. It is **public-domain only** (Project
Gutenberg via the open **Gutendex** JSON API -- no API key, ever), **rate-limited**
(a small minimum interval), **size-capped**, given a sane **timeout** and a real
descriptive **User-Agent**, and every network path is wrapped so it **degrades to
empty / None** with no internet rather than raising. Downloaded bytes are treated
as **untrusted**: they are only ever decoded as text and parsed into a
:class:`breathsim.books.Book` -- never executed, never written outside the local
library.

The pure parts (:func:`parse_gutendex`, :func:`text_to_book`) take bytes/str and
are unit-tested offline with fixtures; :func:`search`/:func:`download` accept an
injectable *fetch* so tests exercise the whole path with zero sockets.

Standard Ebooks (EPUB-only) downloads arrive with the EPUB importer in the next
round; this round covers Gutenberg plain text.
"""
from __future__ import annotations

import json
import time

from . import books, booktext

GUTENDEX = "https://gutendex.com/books?search="
USER_AGENT = ("Vesper/1.0 (calm meditation + public-domain book reader; "
              "+https://github.com/gddickinson/Vesper)")
MAX_BYTES = 6_000_000          # hard cap on a downloaded book (~6 MB of text)
_MIN_INTERVAL = 1.0            # politeness: >= 1 s between real network calls
_last_call = [0.0]


# --- pure parsing (offline-testable) ---------------------------------------

def _plain_text_url(formats):
    """Pick a usable plain-text URL from a Gutendex 'formats' map, or None."""
    if not isinstance(formats, dict):
        return None
    cands = [(k, v) for k, v in formats.items()
             if isinstance(k, str) and k.startswith("text/plain")
             and isinstance(v, str) and not v.endswith(".zip")]
    if not cands:
        return None
    for k, v in cands:                               # prefer a UTF-8 transcript
        if "utf-8" in k.lower() or "utf8" in k.lower() or "utf-8" in v or "utf8" in v:
            return v
    return cands[0][1]


def parse_gutendex(data):
    """Parse a Gutendex JSON response (bytes or str) into a list of result dicts
    ``{id, title, author, source, text_url}``. Never raises; returns [] on junk."""
    try:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8", "replace")
        obj = json.loads(data) if isinstance(data, str) else data
        rows = obj.get("results", []) if isinstance(obj, dict) else []
    except Exception:
        return []
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        url = _plain_text_url(r.get("formats"))
        if not url:
            continue
        authors = r.get("authors") or []
        author = authors[0].get("name", "") if authors and isinstance(authors[0], dict) else ""
        out.append({"id": r.get("id"), "title": (r.get("title") or "Untitled").strip(),
                    "author": author, "source": "gutenberg", "text_url": url})
    return out


def text_to_book(text, title, author="", source="gutenberg"):
    """Boilerplate-strip + segment downloaded *text* into a saved-ready Book."""
    return books.from_text(text, title, author, source=source)


# --- networked (only on an explicit user action) ---------------------------

def _http_get(url, timeout=12, max_bytes=MAX_BYTES):
    """Fetch *url* with a descriptive UA + timeout + size cap. Rate-limited."""
    import urllib.request
    wait = _MIN_INTERVAL - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(min(wait, _MIN_INTERVAL))
    _last_call[0] = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(max_bytes + 1)[:max_bytes]


def search(query, limit=24, fetch=None):
    """Search public-domain books by title/author (Gutendex). Returns a list of
    result dicts, or [] on any error / no network. Network only when CALLED."""
    query = (query or "").strip()
    if not query:
        return []
    fetch = fetch or _http_get
    try:
        import urllib.parse
        data = fetch(GUTENDEX + urllib.parse.quote(query))
        return parse_gutendex(data)[:max(1, int(limit))]
    except Exception:
        return []


def download(result, fetch=None):
    """Fetch a chosen result's plain text, segment + save it to the local library.
    Returns the saved book id, or None on any error. Network only when CALLED."""
    url = (result or {}).get("text_url")
    if not url:
        return None
    fetch = fetch or _http_get
    try:
        raw = fetch(url)
    except Exception:
        return None
    text = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
    if not booktext.to_ascii(booktext.strip_boilerplate(text)).strip():
        return None                                  # nothing usable in the body
    book = text_to_book(text, (result or {}).get("title", "Untitled"),
                        (result or {}).get("author", ""),
                        source=(result or {}).get("source", "gutenberg"))
    return books.save(book)
