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

    # a preface / introduction before chapter 1 is SKIPPED -- a chaptered book's
    # narration starts at chapter 1, not an editor's foreword (e.g. Saintsbury's
    # before Pride & Prejudice). The story, not the front matter, is read.
    with_preface = GUTENBERG.replace(
        "CHAPTER I. The Beginning\n\nAlice was beginning",
        "A note before we begin: this small tale was written on a quiet evening \
for no reason but the pleasure of it, and it asks nothing of you but that you \
rest and let the words drift by as you grow sleepy and calm.\n\n"
        "CHAPTER I. The Beginning\n\nAlice was beginning", 1)
    pf = _flat(booktext.segment(with_preface))
    assert pf.startswith("CHAPTER I."), pf[:50]
    assert "A note before we begin" not in pf, "a preface before chapter 1 is skipped"
    assert "Alice was beginning to get very tired" in pf, "the story itself is kept"
    print("ok: a preface before chapter 1 is skipped; narration starts at chapter 1")

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

    # the real-Gutenberg shapes that used to leak (Tom Sawyer / Peter Pan):
    #  - an all-caps TITLE at the very top (must not be read as a chapter heading)
    #  - a long Contents list, incl. a SHORT entry that also looks structural
    #    ('CHAPTER XIX. Tom Tells the Truth') -- must not halt the scrub mid-list
    #  - a LIST OF ILLUSTRATIONS of short captions, some ending in '?'/'.'
    #  - an edition / digitiser note, and a PREFACE before chapter 1
    # ...all dropped; narration begins at chapter 1's first prose.
    REAL = ("*** START OF THE PROJECT GUTENBERG EBOOK TOMLIKE ***\n\n"
            "THE ADVENTURES OF A QUIET BOY\n\nBy A. N. Author\n\n"
            "A Riverside Edition produced from a scanned copy in the public domain.\n\n"
            "CONTENTS\n\n"
            "CHAPTER I. The Long Summary That Runs On -- And On Across The Page\n\n"
            "CHAPTER XVIII. Another Very Long One -- With A Dash And More Words After\n\n"
            "CHAPTER XIX. The Short One\n\n"
            "CHAPTER XX. Becky in a Dilemma -- And A Trailing Page Summary Besides\n\n"
            "ILLUSTRATIONS\n\n"
            "The Quiet Boy\n\nAin't that Work?\n\nCat and Toys\n\nAmusement\n\n"
            "PREFACE\n\n"
            "Most of the adventures recorded in this book really occurred, and one or two \
were experiences of my own, while the rest belonged to boys who were my schoolmates.\n\n"
            "CHAPTER I\n\nTHE LONG SUMMARY\n\n"
            "Tom did not answer at first, for he was busy by the river where the water moved \
slowly past the reeds and nothing at all was in a hurry there that warm afternoon.\n\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK TOMLIKE ***\n")
    bk3 = books.from_text(REAL, "Tomlike", "A. N. Author")
    spoken3 = " ".join(u["text"] for u in bookreader.units(bk3))
    first3 = spoken3[:60]
    assert first3.startswith("Tom did not answer"), first3
    assert "ADVENTURES OF A QUIET BOY" not in spoken3, "all-caps title narrated!"
    assert "The Short One" not in spoken3, "structural-looking TOC entry leaked"
    assert "Becky in a Dilemma" not in spoken3, "TOC entry leaked"
    assert "Ain't that Work" not in spoken3 and "Cat and Toys" not in spoken3, "caption leaked"
    assert "Riverside Edition" not in spoken3, "edition note leaked"
    assert "Most of the adventures" not in spoken3, "a preface before chapter 1 is skipped"
    assert "Tom did not answer at first" in spoken3, "chapter-1 prose must be narrated"
    assert sum(1 for u in bookreader.units(bk3)) >= 1
    print("ok: all-caps title / TOC / captions / edition note / preface dropped -> chapter 1")

    # a book whose CHAPTER 1 carries no heading (its first heading is 'CHAPTER II')
    # -- like Pride & Prejudice, which opens straight into 'It is a truth...'. The
    # front matter (a critic's preface + a page-numbered plate list) is dropped and
    # narration starts at the headingless chapter 1, NOT chapter 2.
    NOHEAD = ("*** START OF THE PROJECT GUTENBERG EBOOK NOHEAD ***\n\n"
              "A QUIET NOVEL\n\nby A. Writer\n\n"
              "PREFACE\n\n"
              "This long editorial preface considers the book at leisure and at some "
              "length, as such prefaces always do, and is not part of the story at all.\n\n"
              "ILLUSTRATIONS\n\n"
              "The Garden Gate 12\n\nThe Old House 48\n\nThe End 211\n\n"
              "It is a truth universally felt, that a quiet evening in a quiet house is "
              "a fine and welcome thing to all who have known a long and tiring day.\n\n"
              "She closed the book softly and listened to the rain against the glass.\n\n"
              "CHAPTER II\n\n"
              "The next morning came grey and still, and the house was slow to wake.\n\n"
              "*** END OF THE PROJECT GUTENBERG EBOOK NOHEAD ***\n")
    bk4 = books.from_text(NOHEAD, "Nohead", "A. Writer")
    spoken4 = " ".join(u["text"] for u in bookreader.units(bk4))
    assert spoken4.startswith("It is a truth universally felt"), spoken4[:60]
    assert "editorial preface" not in spoken4, "preface leaked into a headingless ch.1"
    assert "The Garden Gate" not in spoken4, "plate list leaked"
    assert "The next morning came grey" in spoken4, "the rest of the story is kept"
    print("ok: a headingless chapter 1 (first heading is CHAPTER II) starts at the story")

    # a trailing printer's colophon (an all-caps imprint AFTER the story, as in some
    # Pride & Prejudice editions) is cut -- the story's real last line is kept.
    COLO = ("*** START OF THE PROJECT GUTENBERG EBOOK COLO ***\n\n"
            "CHAPTER I\n\n"
            "It was a calm and quiet night, and the river moved softly past the reeds "
            "as the moon rose slowly over the hill and all the world lay still.\n\n"
            "And so they were happy, and content, to the very end of their days.\n\n"
            "CHISWICK PRESS:--CHARLES WHITTINGHAM AND CO. TOOKS COURT, CHANCERY LANE, LONDON.\n\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK COLO ***\n")
    bk5 = books.from_text(COLO, "Colo", "X")
    spoken5 = " ".join(u["text"] for u in bookreader.units(bk5))
    assert spoken5.endswith("to the very end of their days."), spoken5[-60:]
    assert "CHISWICK PRESS" not in spoken5, "a trailing printer's colophon leaked"
    # the colophon guard is near-all-caps only: a normal closing sentence that just
    # mentions 'the press.' must NOT be cut.
    OKPRESS = COLO.replace(
        "CHISWICK PRESS:--CHARLES WHITTINGHAM AND CO. TOOKS COURT, CHANCERY LANE, LONDON.",
        "He had always valued, above most things, the freedom of the press.")
    spoken6 = " ".join(u["text"] for u in bookreader.units(books.from_text(OKPRESS, "Ok", "X")))
    assert spoken6.endswith("the freedom of the press."), spoken6[-50:]
    print("ok: a trailing printer's colophon is cut; normal prose with 'press' is kept")

    print("PASS: booktext front-matter removal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
