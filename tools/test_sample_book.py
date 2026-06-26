"""The bundled sample book is seeded once on a fresh install + narrates cleanly.

A brand-new library is empty, so Read mode would have nothing to read. `books.
seed_sample_if_fresh()` adds the bundled public-domain Wind in the Willows once;
it must narrate the *story* (not the title page / contents / Gutenberg boilerplate),
expose chapters for jump-to navigation, and never re-add itself (so deleting it
sticks). Pure books layer -- no Qt, no network, isolated BREATHSIM_HOME.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import books, bookreader, sample_book  # noqa: E402


def main():
    assert sample_book.text().strip(), "the bundled sample asset is missing"
    assert sample_book.text().isascii(), "sample asset should be plain ASCII"

    assert books.list_books() == [], "a fresh library should start empty"
    bid = books.seed_sample_if_fresh()
    assert bid, "seed should add the sample on a fresh install"
    lib = books.list_books()
    assert len(lib) == 1 and lib[0]["title"] == "The Wind in the Willows", lib
    print("ok: a fresh install seeds the sample book")

    book = books.load(bid)
    spoken = [u["text"] for u in bookreader.units(book)]
    assert len(spoken) > 2000, ("the whole book should narrate", len(spoken))
    head = " ".join(spoken[:6]).lower()
    for junk in ("gutenberg", "illustration", "contents", "kenneth grahame",
                 "chapter i"):
        assert junk not in head, ("narration opens with non-story text: " + junk)
    assert "mole had been working very hard" in spoken[0].lower(), spoken[0]
    assert len(bookreader.chapters(book)) >= 10, "chapters for jump-to navigation"
    print("ok: it narrates the story (not the front-matter); chapters detected")

    # idempotent: seeding again does nothing, so deleting the sample makes it stay gone
    assert books.seed_sample_if_fresh() is None
    assert len(books.list_books()) == 1, "must not duplicate on a second launch"
    books.delete(bid)
    assert books.seed_sample_if_fresh() is None and books.list_books() == [], \
        "a deleted sample must not come back"
    print("ok: seeded once only; a deleted sample is not re-added")

    print("PASS: bundled sample book")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
