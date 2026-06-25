"""Find + fetch **public-domain** books on demand -- the only networked part of
the audiobook feature, and deliberately the most cautious *and* the most
talkative about failure.

SAFETY: nothing here touches the network at import or by itself. A fetch happens
ONLY when a caller (a user pressing Search / Download in the GUI) invokes
:func:`search` / :func:`search_ex` / :func:`download` / :func:`download_ex`. It is
**public-domain only** (Project Gutenberg via the open **Gutendex** JSON API -- no
API key, ever), **rate-limited** (a minimum interval), **size-capped**, given a
sane **timeout** and a descriptive **User-Agent**. Downloaded bytes are treated
as **untrusted**: only ever decoded as text and parsed into a
:class:`breathsim.books.Book` -- never executed, never written outside the local
library.

RELIABILITY (why this module is bigger than a one-liner ``urlopen``):
  * **integrity** -- a Gutenberg body with a START band but no END band is a
    truncated download; we *refuse* it rather than save a silently-shortened
    book (the "my book is cut short" bug);
  * **completeness** -- ``Content-Length`` is verified; a short / interrupted
    read raises rather than returning half a book;
  * **diagnosis** -- every failure is mapped to a typed :class:`DownloadError`
    with a *reason* and a friendly *detail*, so the GUI can say WHY (no internet,
    HTTP 404 / 403 / 429 / 5xx, timeout, too large, no usable text), instead of a
    blank "could not download";
  * **retry** -- transient failures (timeout, 429, 5xx, incomplete) are retried
    with backoff; permanent ones (404 / 403) are not.

The pure parts (:func:`parse_gutendex`, :func:`text_to_book`) take bytes/str and
are unit-tested offline with fixtures; the networked functions accept an
injectable *fetch* so tests exercise the whole path with zero sockets.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

from . import books, bookmeta, booktext

GUTENDEX = "https://gutendex.com/books?search="
USER_AGENT = ("Vesper/1.0 (calm meditation + public-domain book reader; "
              "+https://github.com/gddickinson/Vesper)")
MAX_BYTES = 25_000_000         # hard cap on a downloaded book (~25 MB of text)
_MIN_INTERVAL = 1.0            # politeness: >= 1 s between real network calls
_last_call = [0.0]


# --- typed failures --------------------------------------------------------

class DownloadError(Exception):
    """A fetch failure with a machine *reason*, a friendly *detail* sentence, and
    whether it is worth a *retryable* second try."""

    def __init__(self, reason, detail, retryable=False):
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.retryable = retryable


def _classify(exc):
    """Map a raw exception (or a DownloadError) to a typed DownloadError with a
    plain, reassuring message. Never raises."""
    import http.client
    import socket
    import ssl
    import urllib.error
    if isinstance(exc, DownloadError):
        return exc
    if isinstance(exc, urllib.error.HTTPError):
        code = exc.code
        msgs = {
            404: ("http_404", "The book file was not found on the server "
                  "(this edition may have moved).", False),
            403: ("http_403", "The server declined the request (it may be "
                  "rate-limiting downloads -- try again in a minute).", True),
            429: ("http_429", "Too many requests just now -- please wait a "
                  "moment and try again.", True),
        }
        if code in msgs:
            r, d, retry = msgs[code]
            return DownloadError(r, d, retry)
        if 500 <= code < 600:
            return DownloadError(f"http_{code}",
                                 "The book server had a temporary problem -- "
                                 "try again shortly.", True)
        return DownloadError(f"http_{code}", f"The server returned HTTP {code}.",
                             False)
    if isinstance(exc, http.client.IncompleteRead):
        return DownloadError("incomplete", "The download was cut short before the "
                             "whole book arrived -- trying again may fix it.", True)
    if isinstance(exc, (ssl.SSLError,)):
        return DownloadError("tls", "The secure connection timed out before the "
                             "book finished -- please try again.", True)
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return DownloadError("timeout", "The connection timed out -- the network "
                             "may be slow; please try again.", True)
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return DownloadError("timeout", "The connection timed out -- please "
                                 "try again.", True)
        if isinstance(reason, ssl.SSLError):
            return DownloadError("tls", "The secure connection failed -- please "
                                 "try again.", True)
        return DownloadError("no_network", "No internet connection just now. Your "
                             "library still works offline.", False)
    if isinstance(exc, OSError):
        # socket / connection / DNS errors (gaierror, ConnectionError, ...) all
        # land here once URLError/timeout/SSL above are excluded.
        return DownloadError("no_network", "No internet connection just now. Your "
                             "library still works offline.", False)
    return DownloadError("error", "Something went wrong fetching the book -- "
                         "please try again.", False)


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
    """Parse a Gutendex JSON response (bytes or str) into result dicts ``{id,
    title, author, source, text_url, download_count, languages}``. Never raises;
    returns [] on junk."""
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
                    "author": author, "source": "gutenberg", "text_url": url,
                    "download_count": r.get("download_count"),
                    "languages": r.get("languages") or []})
    return out


def text_to_book(text, title, author="", source="gutenberg"):
    """Boilerplate-strip + segment downloaded *text* into a saved-ready Book."""
    return books.from_text(text, title, author, source=source)


# --- networked (only on an explicit user action) ---------------------------

def _politeness():
    wait = _MIN_INTERVAL - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(min(wait, _MIN_INTERVAL))
    _last_call[0] = time.monotonic()


def _http_get(url, timeout=20, max_bytes=MAX_BYTES):
    """Fetch *url* fully with a descriptive UA + timeout + size cap, following
    redirects. Reads to EOF in chunks (robust on chunked streams), verifies it
    did not exceed the cap, and lets ``Content-Length`` mismatches surface as an
    IncompleteRead. Raises a typed :class:`DownloadError` on any failure."""
    import urllib.request
    _politeness()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            chunks, got = [], 0
            while got <= max_bytes:
                block = r.read(65536)
                if not block:
                    break
                chunks.append(block)
                got += len(block)
            if got > max_bytes:
                raise DownloadError("too_large",
                                    "This book is unusually large (over "
                                    f"{max_bytes // 1_000_000} MB) and was not "
                                    "saved. Try a single volume instead.", False)
            return b"".join(chunks)
    except DownloadError:
        raise
    except Exception as e:
        raise _classify(e)


def _fetch_retry(fetch, url, tries=3):
    """Call ``fetch(url)`` (real or injected), retrying *retryable* DownloadErrors
    with a short backoff. Raises the final typed error; non-network exceptions
    from an injected fetch are classified too."""
    last = None
    for attempt in range(max(1, tries)):
        try:
            return fetch(url)
        except Exception as e:
            last = _classify(e)
            if not last.retryable or attempt == tries - 1:
                raise last
            time.sleep(0.6 * (attempt + 1))
    raise last


def search_ex(query, limit=24, fetch=None):
    """Search public-domain books. Returns ``(results, reason)`` where *reason* is
    '' on success, 'empty_query', 'no_matches', or a DownloadError reason. Network
    only when CALLED; never raises."""
    query = (query or "").strip()
    if not query:
        return [], "empty_query"
    fetch = fetch or _http_get
    try:
        import urllib.parse
        data = _fetch_retry(fetch, GUTENDEX + urllib.parse.quote(query))
    except DownloadError as e:
        return [], e.reason
    except Exception:
        return [], "error"
    rows = parse_gutendex(data)[:max(1, int(limit))]
    return rows, ("" if rows else "no_matches")


def search(query, limit=24, fetch=None):
    """Back-compatible search: returns just the result list ([] on any error)."""
    return search_ex(query, limit=limit, fetch=fetch)[0]


@dataclass
class Outcome:
    """The result of a download attempt, for the GUI to show plainly."""
    ok: bool
    book_id: str = None
    reason: str = ""            # saved | no_network | timeout | http_404 | empty ...
    detail: str = ""            # a friendly, ready-to-show sentence
    title: str = ""
    sentences: int = 0
    byte_size: int = 0


def download_ex(result, fetch=None):
    """Fetch a chosen result's plain text, verify it is whole, segment + save it.
    Returns an :class:`Outcome`. Network only when CALLED; never raises."""
    title = (result or {}).get("title", "Untitled")
    url = (result or {}).get("text_url")
    if not url:
        return Outcome(False, reason="not_text", title=title,
                       detail="This edition has no plain-text version to read.")
    fetch = fetch or _http_get
    try:
        raw = _fetch_retry(fetch, url)
    except DownloadError as e:
        return Outcome(False, reason=e.reason, title=title, detail=e.detail)
    except Exception:
        return Outcome(False, reason="error", title=title,
                       detail="Something went wrong fetching the book.")

    byte_size = len(raw) if isinstance(raw, (bytes, bytearray)) else len(str(raw))
    text = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else str(raw)

    # integrity: a Gutenberg START band with no END band == truncated mid-book.
    if (result or {}).get("source", "gutenberg") == "gutenberg":
        has_start, has_end = booktext.pg_markers(text)
        if has_start and not has_end:
            return Outcome(False, reason="incomplete", title=title, byte_size=byte_size,
                           detail="The download arrived incomplete (the book's end "
                           "marker is missing). Please try downloading it again.")

    if not booktext.to_ascii(booktext.strip_boilerplate(text)).strip():
        return Outcome(False, reason="empty", title=title, byte_size=byte_size,
                       detail="No readable text was found in that file. Try a "
                       "different edition.")
    book = text_to_book(text, title, (result or {}).get("author", ""),
                        source=(result or {}).get("source", "gutenberg"))
    bid = books.save(book)
    if not bid:
        return Outcome(False, reason="empty", title=title, byte_size=byte_size,
                       detail="That book had no usable sentences after cleaning.")
    return Outcome(True, book_id=bid, reason="saved", title=book.title,
                   sentences=book.sentence_count(), byte_size=byte_size,
                   detail="Saved to your library.")


def download(result, fetch=None):
    """Back-compatible download: returns the saved book id, or None on any error."""
    out = download_ex(result, fetch=fetch)
    return out.book_id if out.ok else None


def probe_size(result, fetch=None):
    """Best-effort PRE-download size (bytes) of a result's text file, for showing
    an estimated length before committing. Tries a ranged GET (cheap); returns an
    int, or None when the server won't say. Network only when CALLED; never
    raises. The result dict is annotated in place with ``byte_size`` on success."""
    url = (result or {}).get("text_url")
    if not url:
        return None
    try:
        size = _content_length(url) if fetch is None else None
    except Exception:
        size = None
    if size and isinstance(result, dict):
        result["byte_size"] = size
    return size


def _content_length(url, timeout=12):
    """Read just the Content-Length via a HEAD request (no body). None if absent
    (Gutenberg's cache often omits it). Never raises out -- classified instead."""
    import urllib.request
    _politeness()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT},
                                 method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            cl = r.headers.get("Content-Length")
            return int(cl) if cl and cl.isdigit() else None
    except Exception:
        return None


# --- friendly summaries for the GUI ----------------------------------------

def result_caption(result):
    """A compact, pre-download description of a search result (popularity /
    language / estimated length when a size has been probed)."""
    return bookmeta.describe_result(result)
