"""Turn a :class:`breathsim.books.Book` into a stream of narrator **units**.

Pure + testable: :func:`units` yields one unit dict per sentence (the same shape
the storyteller produces -- ``{"text", "pause", "kind", "sentence"}``), with a
longer pause at the end of each paragraph so the narration breathes naturally.
The ``sentence`` index lets the reader persist a **resume** position as each
sentence is spoken, so a book picks up where you fell asleep. No I/O here; the
GUI feeds these straight to ``narration.Narrator.start`` and persists the index
via :func:`breathsim.books.set_position`.
"""
from __future__ import annotations

DEFAULT_LINE_PAUSE = 700        # ms between sentences within a paragraph
DEFAULT_PARA_PAUSE = 1600       # ms at a paragraph break (a gentle settle)


def units(book, start=0, line_pause=DEFAULT_LINE_PAUSE,
          para_pause=DEFAULT_PARA_PAUSE):
    """Yield narrator units for *book*, starting at sentence index *start*.

    Each unit is ``{"text": sentence, "pause": ms, "kind": "book",
    "sentence": i}``. The last sentence of a paragraph (and the final sentence)
    gets *para_pause*; the rest get *line_pause*. Chapter headings / dividers stay
    in the book (for the read-along view + jump-to-chapter) but are **not narrated**
    -- the reader skips them so it never reads 'Chapter Two' or a row of asterisks."""
    from . import booktext
    sents = book.sentences()
    n = len(sents)
    starts = set(book.paragraph_starts())
    start = max(0, min(int(start), n))
    for i in range(start, n):
        if not booktext.is_narratable(sents[i]):     # heading / divider: show, don't read
            continue
        para_end = (i + 1 in starts) or (i == n - 1)
        yield {"text": sents[i], "pause": para_pause if para_end else line_pause,
               "kind": "book", "sentence": i}


def resume_units(book, **kw):
    """Like :func:`units` but starting from the book's saved resume position."""
    from . import books
    pos = books.position(book.id)
    if pos >= book.sentence_count():        # finished last time -> start over
        pos = 0
    return units(book, start=pos, **kw)


def chapters(book):
    """Return ``[(sentence_index, title), ...]`` -- the flat sentence index at
    which each detected chapter/heading begins, for **jump-to** navigation.

    Built from :func:`breathsim.booktext.chapter_marks` (heading-like paragraphs:
    'CHAPTER IV', 'BOOK II', a lone roman numeral...) mapped through the book's
    paragraph starts. Best-effort and may be empty (e.g. a heading-less text);
    duplicate start positions are collapsed and titles trimmed for display."""
    from . import booktext
    if book is None:
        return []
    starts = book.paragraph_starts()
    out, seen = [], set()
    for pidx, title in booktext.chapter_marks(book.paragraphs):
        if 0 <= pidx < len(starts):
            si = starts[pidx]
            if si in seen:
                continue
            seen.add(si)
            out.append((si, (title or "").strip()[:60]))
    return out[:1000]
