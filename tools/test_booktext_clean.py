"""Offline test for non-story front-matter removal in breathsim.booktext.segment.

A downloaded Gutenberg book keeps a title page, edition note, a table of contents
and inline [Illustration] markers between the legal band and the story; none of it
should be narrated. `segment` now strips that, while keeping the actual chapters
(and any genuine preface). Pure, no Qt, no network.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import booktext  # noqa: E402

GUTENBERG = """The Project Gutenberg eBook of Wondertale

*** START OF THE PROJECT GUTENBERG EBOOK WONDERTALE ***

[Illustration]

Wondertale

by A. Writer

THE MILLENNIUM FULCRUM EDITION 3.0

Contents

CHAPTER I. The Beginning CHAPTER II. The Middle CHAPTER III. The End

CHAPTER I. The Beginning

Alice was beginning to get very tired of sitting by her sister on the bank, and \
of having nothing to do: once or twice she had peeped into the book, but it had \
no pictures in it, and what is the use of a book without pictures or conversations?

So she was considering in her own mind whether the pleasure of making a \
daisy-chain would be worth the trouble of getting up, when suddenly a White \
Rabbit with pink eyes ran close by her, and this is _quite_ a long line indeed.

[Illustration: the white rabbit]

CHAPTER II. The Middle

There was nothing so very remarkable in that, nor did Alice think it so very much \
out of the way to hear the Rabbit say to itself "Oh dear! I shall be late!" and on \
she went, and the tale went on for a good while after that, calm and unhurried.

*** END OF THE PROJECT GUTENBERG EBOOK WONDERTALE ***
"""


def _flat(paras):
    return " ".join(s for para in paras for s in para)


def main():
    paras = booktext.segment(GUTENBERG)
    flat = _flat(paras)
    first = paras[0][0]

    # narration starts at the story (the first chapter), not the title page
    assert first.startswith("CHAPTER I."), first
    # the book's own front-matter + editorial markers are gone
    assert "[Illustration" not in flat
    assert "by A. Writer" not in flat
    assert "MILLENNIUM" not in flat
    assert "The Beginning CHAPTER II" not in flat, "table-of-contents blob narrated"
    assert "_quite_" not in flat, "Gutenberg italics underscores left in"
    # but the real story (and both chapter headings) is fully preserved
    assert "Alice was beginning to get very tired" in flat
    assert "tale went on for a good while" in flat
    assert sum(1 for p in paras if p and p[0].startswith("CHAPTER ")) == 2
    print("ok: front-matter/TOC/illustrations stripped; both chapters + prose kept")

    # chapters still detected for jump-to-chapter, chapter I at the very start
    from breathsim import books
    chs = booktext.chapter_marks(paras)
    assert chs and chs[0][1].startswith("CHAPTER I"), chs
    bk = books.from_text(GUTENBERG, "Wondertale", "A. Writer")
    assert bk.sentences()[0].startswith("CHAPTER I."), bk.sentences()[0]
    print("ok: chapters detected; book starts at chapter I")

    # a genuine preface (long prose before chapter 1) is NOT dropped
    with_preface = GUTENBERG.replace(
        "CHAPTER I. The Beginning\n\nAlice was beginning",
        "A note before we begin: this small tale was written on a quiet evening \
for no reason but the pleasure of it, and it asks nothing of you but that you \
rest and let the words drift by as you grow sleepy and calm.\n\n"
        "CHAPTER I. The Beginning\n\nAlice was beginning", 1)
    pf = _flat(booktext.segment(with_preface))
    assert "A note before we begin" in pf, "a real preface should be preserved"
    assert "by A. Writer" not in pf, "title page should still be dropped"
    print("ok: a genuine preface is preserved; the title page still dropped")

    # a book with no chapter headings: drop the leading title run, keep all prose
    flat2 = _flat(booktext.segment(
        "*** START OF THE PROJECT GUTENBERG EBOOK X ***\n\n"
        "A Quiet Book\n\nby Someone\n\n"
        "The river moved slowly past the old town, and the evening came down soft \
and grey over the water, and nothing at all was in a hurry there.\n\n"
        "*** END OF THE PROJECT GUTENBERG EBOOK X ***\n"))
    assert flat2.startswith("The river moved slowly"), flat2[:40]
    assert "A Quiet Book" not in flat2 and "by Someone" not in flat2
    print("ok: heading-less book drops the title run, keeps the prose")

    # headings are KEPT in the book (display + jump-to-chapter) but never NARRATED;
    # footnote refs, scene dividers and a trailing transcriber note are removed
    from breathsim import bookreader
    HARD = ("*** START OF THE PROJECT GUTENBERG EBOOK Y ***\n\n"
            "CHAPTER I\n\nTHE BEGINNING\n\n"
            "It was a calm night by the river.[1] The water moved slowly past the reeds, \
and nothing at all was in a hurry there as the evening came softly down.\n\n"
            "* * *\n\n"
            "The moon rose over the hill, and all the little creatures settled down, warm \
and safe, to sleep the quiet night away until the morning.\n\n"
            "CHAPTER II\n\n"
            "They woke at dawn and went down to the water once more, glad and unhurried, \
to begin another slow and gentle day beside the river they loved.\n\n"
            "TRANSCRIBER'S NOTE\n\n"
            "Minor spelling errors have been corrected silently. This e-text was prepared \
from a scanned copy and may contain small inconsistencies in the original.\n\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK Y ***\n")
    bk2 = books.from_text(HARD, "Y", "Z")
    inbook = " ".join(bk2.sentences())
    spoken = " ".join(u["text"] for u in bookreader.units(bk2))
    assert "CHAPTER I" in inbook and "CHAPTER II" in inbook, "headings kept for nav/display"
    assert "CHAPTER" not in spoken and "THE BEGINNING" not in spoken, "headings narrated!"
    assert "It was a calm night by the river." in spoken, "story prose must be narrated"
    assert "[1]" not in inbook and "[1]" not in spoken, "footnote ref not stripped"
    assert "*" not in inbook, "scene divider not dropped"
    assert "TRANSCRIBER" not in inbook and "scanned copy" not in inbook, "tail not cut"
    assert booktext.is_narratable("It was a calm night.")
    assert not booktext.is_narratable("CHAPTER I")
    assert not booktext.is_narratable("THE RIVER BANK") and not booktext.is_narratable("* * *")
    print("ok: headings shown-not-narrated; footnotes/dividers/transcriber-tail removed")

    print("PASS: booktext front-matter removal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
