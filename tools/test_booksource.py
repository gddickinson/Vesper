"""Offline test for breathsim.booksource -- NO sockets, NO network.

Feeds canned Gutendex JSON + a canned Project-Gutenberg text blob through the
pure parsing + an INJECTED fetch, asserting: results parse (title/author/text
URL chosen), a Book is segmented (boilerplate stripped, ASCII) and saved into the
local library, an empty/garbage body is rejected, and every path degrades
gracefully (a failing fetch -> [] / None, never an exception).
"""
import json
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import books, booksource  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")

GUTENDEX_JSON = json.dumps({
    "count": 1,
    "results": [{
        "id": 1342,
        "title": "Pride and Prejudice",
        "authors": [{"name": "Austen, Jane"}],
        "formats": {
            "text/html": "https://example.org/1342.html",
            "application/epub+zip": "https://example.org/1342.epub",
            "text/plain; charset=us-ascii": "https://example.org/1342.txt",
            "text/plain; charset=utf-8": "https://example.org/1342-0.txt",
        },
    }, {
        "id": 99, "title": "No Text Here", "authors": [],
        "formats": {"text/html": "https://example.org/99.html"},
    }],
}).encode("utf-8")

PG_TEXT = (
    "The Project Gutenberg eBook of Pride and Prejudice\n\nlegal front matter...\n\n"
    "*** START OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***\n\n"
    "It is a truth universally acknowledged. A single man must want a wife.\n\n"
    "However little known the feelings of such a man may be.\n\n"
    "*** END OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***\n\nfooter...\n"
).encode("utf-8")


def main():
    # parse_gutendex: only books with a plain-text format survive; UTF-8 preferred
    rows = booksource.parse_gutendex(GUTENDEX_JSON)
    assert len(rows) == 1, rows
    r = rows[0]
    assert r["title"] == "Pride and Prejudice" and "Austen" in r["author"]
    assert r["text_url"].endswith("1342-0.txt"), r["text_url"]   # utf-8 preferred
    assert r["source"] == "gutenberg"
    print("ok: Gutendex parsed; UTF-8 plain-text URL chosen; no-text book dropped")

    # title tidy-up: MARC subfield codes ('$b') and orphaned ' : ' are removed
    assert booksource._clean_title("Peter Pan : $b [Peter and Wendy]") == \
        "Peter Pan [Peter and Wendy]"
    assert booksource._clean_title("Plain Title") == "Plain Title"
    assert booksource._clean_title("") == "Untitled"
    print("ok: catalogue titles tidied ($b subfield + orphan colon removed)")

    # junk in -> [] (never raises)
    assert booksource.parse_gutendex(b"not json") == []
    assert booksource.parse_gutendex("{}") == []
    print("ok: junk JSON -> empty, no crash")

    # search with an injected fetch (no socket)
    res = booksource.search("pride", fetch=lambda url: GUTENDEX_JSON)
    assert len(res) == 1 and res[0]["id"] == 1342
    assert booksource.search("", fetch=lambda url: GUTENDEX_JSON) == []   # empty query
    print("ok: search() via injected fetch (no network)")

    # download with an injected fetch -> Book saved + segmented + boilerplate gone
    bid = booksource.download(r, fetch=lambda url: PG_TEXT)
    assert bid, "download should save a book"
    book = books.load(bid)
    assert book and book.sentence_count() >= 3
    flat = " ".join(book.sentences())
    assert "truth universally acknowledged" in flat
    assert "Project Gutenberg" not in flat and "START OF" not in flat
    assert all(s.isascii() for s in book.sentences())
    assert bid in {b["id"] for b in books.list_books()}
    print(f"ok: download -> saved Book '{bid}' ({book.sentence_count()} sentences)")

    # empty body -> None, never saved
    assert booksource.download(r, fetch=lambda url: b"   \n\n  ") is None
    print("ok: empty body rejected")

    # a failing fetch -> graceful None / [] (no network, no raise)
    def boom(url):
        raise OSError("no network")
    assert booksource.search("x", fetch=boom) == []
    assert booksource.download(r, fetch=boom) is None
    print("ok: network failure degrades to []/None")

    # --- richer metadata in parsed results ---
    assert "download_count" in r and "languages" in r
    print("ok: parsed results carry download_count + languages")

    # --- typed download outcomes (the diagnostics) ---
    out = booksource.download_ex(r, fetch=lambda url: PG_TEXT)
    assert out.ok and out.reason == "saved" and out.sentences >= 3
    assert out.byte_size == len(PG_TEXT)
    print(f"ok: download_ex -> Outcome(saved, {out.sentences} sentences)")

    # integrity: a Gutenberg START band with no END band == a truncated download,
    # refused with reason 'incomplete' (the 'my book is shortened' fix)
    truncated = (b"*** START OF THE PROJECT GUTENBERG EBOOK FOO ***\n\n"
                 b"Half a chapter that the connection cut off mid-sen")
    o = booksource.download_ex({"title": "Foo", "text_url": "u",
                                "source": "gutenberg"}, fetch=lambda url: truncated)
    assert not o.ok and o.reason == "incomplete", o
    print("ok: truncated Gutenberg body refused (incomplete), not saved short")

    # empty / no-text-format outcomes
    assert booksource.download_ex(r, fetch=lambda url: b"  \n ").reason == "empty"
    assert booksource.download_ex({"title": "X"}).reason == "not_text"
    print("ok: empty body + no-text-format carry clear reasons")

    # typed network reasons surfaced (not just None)
    import urllib.error
    def http(code):
        def f(url):
            raise urllib.error.HTTPError("u", code, "x", {}, None)
        return f
    assert booksource.download_ex(r, fetch=http(404)).reason == "http_404"
    assert booksource.download_ex(r, fetch=http(403)).reason == "http_403"
    assert booksource.download_ex(r, fetch=boom).reason == "no_network"
    print("ok: HTTP 404/403 + no-network surfaced as typed reasons")

    # classification covers timeouts + incomplete reads
    import http.client
    import socket
    assert booksource._classify(socket.timeout()).reason == "timeout"
    assert booksource._classify(http.client.IncompleteRead(b"")).reason == "incomplete"
    assert booksource._classify(http.client.IncompleteRead(b"")).retryable
    print("ok: timeouts + incomplete reads classified (retryable)")

    # search_ex carries a reason; retryable failures are retried then reported
    rows, reason = booksource.search_ex("pride", fetch=lambda url: GUTENDEX_JSON)
    assert rows and reason == ""
    assert booksource.search_ex("")[1] == "empty_query"
    assert booksource.search_ex("x", fetch=boom)[1] == "no_network"
    calls = [0]
    def flaky(url):
        calls[0] += 1
        raise urllib.error.HTTPError("u", 429, "Too Many", {}, None)
    assert booksource.search_ex("x", fetch=flaky)[1] == "http_429"
    assert calls[0] >= 2, "a 429 (retryable) should be retried before giving up"
    print(f"ok: search_ex reasons + retry (429 tried {calls[0]}x)")

    print("PASS: booksource -- search/download, diagnostics, integrity, offline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
