"""Offline tests for the audiobook core (booktext + books + store) -- no network.

Uses a small Project-Gutenberg-shaped fixture in a temp library dir. Asserts:
boilerplate is stripped; smart quotes / dashes / accents fold to ASCII;
abbreviations (Mr./Dr.) do NOT split a sentence; segmentation yields paragraphs
of sentences; a Book saves + loads + indexes; resume position round-trips; and
delete removes content, index and position.
"""
import os
import sys
import tempfile

# Isolate ALL storage in a temp dir BEFORE importing breathsim.
_TMP = tempfile.mkdtemp()
os.environ["BREATHSIM_HOME"] = _TMP
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import booktext, books, store  # noqa: E402

books.LIB_DIR = os.path.join(store.DIR, "books")    # follow the temp home

RAW = (
    "The Project Gutenberg eBook of A Test Book\n\n"
    "This eBook is for the use of anyone anywhere... lots of legal text.\n\n"
    "*** START OF THE PROJECT GUTENBERG EBOOK A TEST BOOK ***\n\n"
    "Produced by A Volunteer and the Online Distributed Proofreading Team.\n\n"
    "CHAPTER I\n\n"
    "It was a bright cold day in a small café. Mr. Smith said “hello” "
    "to Dr. Jones. They walked on together.\n\n"
    "The wind blew softly — gently — through the pines… She paused, "
    "then smiled.\n\n"
    "*** END OF THE PROJECT GUTENBERG EBOOK A TEST BOOK ***\n\n"
    "This eBook is distributed under more legal text nobody reads.\n")


def main():
    # boilerplate strip
    body = booktext.strip_boilerplate(RAW)
    assert "bright cold day" in body
    for gone in ("START OF", "END OF", "Produced by", "use of anyone", "distributed under"):
        assert gone not in body, gone
    print("ok: PG header/footer + 'Produced by' stripped")

    # ascii folding
    a = booktext.to_ascii("a café — “hi”…")
    assert "cafe" in a and "--" in a and '"hi"' in a and "..." in a
    assert a.isascii()
    print("ok: smart quotes / dashes / accents folded to ASCII")

    # segmentation + abbreviation-aware splitting
    paras = booktext.segment(RAW)
    assert all(isinstance(p, list) for p in paras)
    flat = [s for p in paras for s in p]
    # Mr./Dr. stay in one sentence; total sentence count is exact.
    assert any(s.startswith("Mr. Smith") and s.endswith("Jones.") for s in flat), flat
    assert "CHAPTER I" in flat[0] or any("CHAPTER I" in s for s in flat[:2])
    body_sents = [s for s in flat if "CHAPTER" not in s]
    assert len(body_sents) == 5, (len(body_sents), body_sents)
    assert all(s.isascii() for s in flat)
    print(f"ok: segmented into {len(paras)} paragraphs, {len(flat)} sentences")

    # chapter detection
    marks = booktext.chapter_marks(paras)
    assert any("CHAPTER" in t.upper() for _i, t in marks), marks
    print("ok: chapter heading detected")

    # Book model + library round-trip
    book = books.from_text(RAW, "A Test Book", "Anon", source="gutenberg")
    assert book.sentence_count() == len(flat)
    bid = books.save(book)
    assert bid and books.exists(bid)
    loaded = books.load(bid)
    assert loaded and loaded.paragraphs == book.paragraphs
    idx = {b["id"]: b for b in books.list_books()}
    assert bid in idx and idx[bid]["sentences"] == book.sentence_count()
    assert idx[bid]["source"] == "gutenberg"
    print(f"ok: book saved + loaded + indexed ({bid})")

    # resume position
    assert books.position(bid) == 0
    books.set_position(bid, 7)
    assert books.position(bid) == 7
    books.clear_position(bid)
    assert books.position(bid) == 0
    print("ok: resume position round-trips")

    # empty book refused; delete cleans up
    assert books.save(books.from_text("", "Empty")) is None
    books.set_position(bid, 3)
    books.delete(bid)
    assert not books.exists(bid)
    assert bid not in {b["id"] for b in books.list_books()}
    assert books.position(bid) == 0
    print("ok: empty refused; delete removes content + index + position")

    print("PASS: audiobook core -- segmentation, ASCII, library, resume (offline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
