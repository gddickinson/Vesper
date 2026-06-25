"""Offline test for breathsim.bookmeta -- the pure book *description* helpers.

Checks popularity banding (+ stars), language spelling, the narration-length
estimate from chars / sentences, duration + size formatting, the compact
search-row and library-row descriptions, and the library report (counts + disk),
all deterministic and socket-free.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import bookmeta, books, booksource  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")


def main():
    # popularity banding + stars
    assert bookmeta.popularity(70000) == ("very popular", 3)
    assert bookmeta.popularity(2000)[0] == "popular"
    assert bookmeta.popularity(300)[0] == "known"
    assert bookmeta.popularity(5)[0] == "rarely read"
    assert bookmeta.popularity(None) == ("popularity unknown", 0)
    assert bookmeta.popularity_label(70000).startswith("★★★")
    assert "★" not in bookmeta.popularity_label(5)
    print("ok: popularity banding + stars")

    # language spelling
    assert bookmeta.language_label(["en"]) == "English"
    assert bookmeta.language_label(["fr"]) == "French"
    assert bookmeta.language_label("de") == "German"
    assert bookmeta.language_label(["xx"]) == "XX"        # unknown -> upper
    assert bookmeta.language_label([]) == ""
    print("ok: language labels")

    # length estimate: a real book's char count -> a sane number of hours
    mins = bookmeta.estimate_minutes(chars=743000)        # ~Pride and Prejudice
    assert 700 < mins < 1100, mins                        # ~12-15 h is reasonable
    assert bookmeta.estimate_minutes(sentences=6598) > 600
    assert bookmeta.estimate_minutes() == 0               # nothing known
    assert "h" in bookmeta.length_from_bytes(743000)
    assert bookmeta.length_from_bytes(0) == ""
    print("ok: narration-length estimate")

    # duration + size formatting
    assert bookmeta.format_duration(12) == "~12 min"
    assert bookmeta.format_duration(180) == "~3 h"
    assert bookmeta.format_duration(0) == ""
    assert bookmeta.format_size(0) == ""
    assert bookmeta.format_size(800) == "800 B"
    assert bookmeta.format_size(900_000).endswith("KB")
    assert bookmeta.format_size(1_500_000).endswith("MB")
    # length bands are ordered
    bands = [bookmeta.length_label(bookmeta.estimate_minutes(chars=c))
             for c in (20_000, 300_000, 1_500_000, 4_000_000)]
    assert "very short" in bands[0] and "epic" in bands[-1], bands
    print("ok: duration/size/length formatting")

    # compact descriptions
    cap = bookmeta.describe_result({"download_count": 70000, "languages": ["fr"],
                                    "byte_size": 743000})
    assert "very popular" in cap and "French" in cap and "h)" in cap, cap
    # English + unknown popularity -> uncluttered
    assert bookmeta.describe_result({"languages": ["en"]}) == ""
    assert "sentences" in bookmeta.describe_book({"sentences": 6598})
    assert bookmeta.describe_book({"sentences": 0}) == "empty"
    print("ok: compact result + book descriptions")

    # library report over a couple of saved books
    for t, txt in [("One", "A first sentence. A second one here."),
                   ("Two", "Another book entirely. With two sentences.")]:
        books.save(booksource.text_to_book(txt, t, "Anon"))
    rep = bookmeta.library_report()
    assert rep["count"] == 2 and rep["sentences"] >= 4 and rep["bytes"] > 0, rep
    line = bookmeta.report_line(rep)
    assert "2 books" in line, line
    assert bookmeta.report_line({"count": 0}) == "Your library is empty."
    print("ok: library report + line")

    print("PASS: bookmeta -- pure book descriptions + library report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
