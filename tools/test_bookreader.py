"""Offline test for breathsim.bookreader -- pure, no Qt, no network.

Builds a Book, runs the BookReader, and asserts: one unit per sentence with the
right keys; sentence indices are contiguous from the start; paragraph-final
sentences get the longer pause; and resume_units honours a saved position.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import bookreader, books  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")

TEXT = ("One. Two. Three.\n\n"          # paragraph 1: 3 sentences
        "Four. Five.\n\n"               # paragraph 2: 2 sentences
        "Six.")                         # paragraph 3: 1 sentence


def main():
    book = books.from_text(TEXT, "Counting", source="upload")
    n = book.sentence_count()
    assert n == 6, n
    starts = book.paragraph_starts()
    assert starts == [0, 3, 5], starts

    us = list(bookreader.units(book, start=0, line_pause=700, para_pause=1600))
    assert len(us) == 6
    assert [u["sentence"] for u in us] == list(range(6))
    assert all(u["kind"] == "book" and u["text"] for u in us)
    # paragraph-final sentences: indices 2, 4, 5 -> long pause; 0,1,3 -> short
    longs = {i for i, u in enumerate(us) if u["pause"] == 1600}
    assert longs == {2, 4, 5}, longs
    print("ok: one unit/sentence, contiguous, paragraph pauses correct")

    # start partway
    mid = list(bookreader.units(book, start=3))
    assert [u["sentence"] for u in mid] == [3, 4, 5]
    print("ok: start index respected")

    # resume from saved position
    books.save(book)
    books.set_position(book.id, 4)
    res = list(bookreader.resume_units(book))
    assert [u["sentence"] for u in res] == [4, 5], [u["sentence"] for u in res]
    # finished -> resume restarts at 0
    books.set_position(book.id, n)
    res2 = list(bookreader.resume_units(book))
    assert [u["sentence"] for u in res2] == list(range(6))
    print("ok: resume_units honours saved position (and restarts when finished)")

    print("PASS: bookreader -- units, pauses, start index, resume (offline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
