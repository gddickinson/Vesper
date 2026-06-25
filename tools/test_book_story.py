"""Offline test: a library book narrates as a Sleep storyteller option.

Asserts that a saved book surfaces via stories.book_names(), resolves a real
ambience and a book id, and that stories.story_units("Book: <title>") yields
book units that resume from the saved sentence position -- all pure, no Qt, no
network, no LLM.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import books, stories, voices  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")

TEXT = ("One. Two. Three.\n\nFour. Five.\n\nSix. Seven.")


def main():
    # empty library -> no book options, but the app is unaffected
    assert stories.book_names() == []
    print("ok: empty library -> no book options")

    book = books.from_text(TEXT, "My Novel", "Anon", source="upload")
    bid = books.save(book)
    name = stories.BOOK_PREFIX + "My Novel"

    assert name in stories.book_names()
    assert stories.book_id_for(name) == bid
    amb = stories.ambience_for(name)
    assert amb == stories.BOOK_AMBIENCE and amb in set(voices.names()), amb
    print(f"ok: book surfaces as '{name}', ambience '{amb}' resolves")

    us = list(stories.story_units(name))
    assert us and all(u.get("kind") == "book" for u in us)
    assert [u["sentence"] for u in us] == list(range(book.sentence_count()))
    assert all("phase" not in u or u["phase"] is None for u in us)  # no breath-gating
    print(f"ok: story_units yields {len(us)} book units from the start")

    # resume by sentence index
    books.set_position(bid, 4)
    res = list(stories.story_units(name))
    assert [u["sentence"] for u in res] == [4, 5, 6], [u["sentence"] for u in res]
    print("ok: story_units resumes from the saved sentence position")

    # unknown / missing book -> empty stream, never raises
    assert list(stories.story_units(stories.BOOK_PREFIX + "Nope")) == []
    print("ok: unknown book name -> empty stream, no crash")

    print("PASS: book narrates as a Sleep story (dispatch + ambience + resume)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
