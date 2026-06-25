"""Offline test for the R6 progress polish -- books.percent_read / in_progress +
resumehint.book_continue_hint. No Qt, no network.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import books  # noqa: E402
from vesper import resumehint  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")

TEXT = " ".join(f"Sentence {i}." for i in range(20))    # 20 sentences


def main():
    assert books.in_progress() == [] and resumehint.book_continue_hint([]) is None
    print("ok: empty library -> no in-progress, no hint")

    bid = books.save(books.from_text(TEXT, "Long Book", source="upload"))
    assert books.percent_read(bid) == 0                 # not started
    # partway
    books.set_position(bid, 5)
    assert books.percent_read(bid) == 25, books.percent_read(bid)
    ip = books.in_progress()
    assert len(ip) == 1 and ip[0]["id"] == bid and ip[0]["percent"] == 25
    hint = resumehint.book_continue_hint(ip)
    assert hint == 'Continue your book: "Long Book" (25% read).', hint
    print(f"ok: 25% read; hint = {hint!r}")

    # finished -> not 'in progress', percent clamps at 100 path (pos==total)
    books.set_position(bid, 20)
    assert books.in_progress() == []                    # 0 < pos < total only
    print("ok: a finished book is not 'in progress'")

    # at the very start -> not in progress
    books.set_position(bid, 0)
    assert books.in_progress() == [] and books.percent_read(bid) == 0
    print("ok: a book at the start is not 'in progress'")

    print("PASS: book progress -- percent_read + in_progress + continue hint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
