"""Pure text processing for the audiobook feature -- no I/O, no network.

Turns a raw book file (Project Gutenberg plain text, a Standard Ebooks chapter,
or a user's own .txt) into clean, ASCII, narratable units:

  * :func:`strip_boilerplate` removes the Project Gutenberg header/footer (the
    ``*** START/END OF THE PROJECT GUTENBERG EBOOK ***`` band and the legal
    front-matter) and trims obvious Standard-Ebooks/transcriber cruft;
  * :func:`to_ascii` folds smart quotes, dashes, ellipses and accents to plain
    ASCII so the procedural synthesiser can voice every character;
  * :func:`split_paragraphs` rejoins hard-wrapped lines into paragraphs;
  * :func:`split_sentences` is a small, abbreviation-aware sentence splitter;
  * :func:`segment` returns ``[[sentence, ...], ...]`` (paragraphs of sentences),
    the shape the narrator consumes;
  * :func:`chapter_marks` flags heading-like paragraphs for navigation.

Everything here is deterministic and unit-tested offline.
"""
from __future__ import annotations

import re
import unicodedata

# --- ASCII folding ---------------------------------------------------------

_PUNCT = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "–": "-", "—": " -- ", "―": " -- ", "−": "-",
    "…": "...", " ": " ", " ": " ", " ": " ", " ": " ",
    "•": "-", "·": "-", "﻿": "",
}


def to_ascii(text):
    """Fold common Unicode punctuation + accents down to plain ASCII."""
    if not text:
        return ""
    for a, b in _PUNCT.items():
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text)
    return text.encode("ascii", "ignore").decode("ascii")


# --- Project Gutenberg / transcriber boilerplate ---------------------------

_PG_START = re.compile(
    r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)
_PG_END = re.compile(
    r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)
# Older PG markers without the triple asterisks.
_PG_START2 = re.compile(r"^\s*START OF (?:THE|THIS) PROJECT GUTENBERG.*$", re.I | re.M)
_PG_END2 = re.compile(r"^\s*END OF (?:THE|THIS) PROJECT GUTENBERG.*$", re.I | re.M)
_PRODUCED = re.compile(r"^\s*Produced by .*$", re.I | re.M)


def pg_markers(text):
    """Return ``(has_start, has_end)`` for the Project Gutenberg header/footer
    bands. A Gutenberg download with a START band but no END band was almost
    certainly **truncated** mid-book -- the downloader uses this to refuse a
    half-book rather than save a silently-shortened one."""
    t = text or ""
    has_start = bool(_PG_START.search(t) or _PG_START2.search(t))
    has_end = bool(_PG_END.search(t) or _PG_END2.search(t))
    return has_start, has_end


def strip_boilerplate(text):
    """Return just the book body: drop the PG header (everything up to the START
    band) and footer (everything from the END band), plus a stray 'Produced by'
    line. Safe on text that has no markers (returns it unchanged)."""
    if not text:
        return ""
    m = _PG_START.search(text) or _PG_START2.search(text)
    if m:
        text = text[m.end():]
    m = _PG_END.search(text) or _PG_END2.search(text)
    if m:
        text = text[:m.start()]
    text = _PRODUCED.sub("", text)
    return text.strip()


# --- paragraphs + sentences ------------------------------------------------

def split_paragraphs(text):
    """Split into paragraphs on blank lines, rejoining hard-wrapped lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out = []
    for part in re.split(r"\n[ \t]*\n", text):
        p = re.sub(r"\s+", " ", part).strip()
        if p:
            out.append(p)
    return out


# Abbreviations whose trailing period does NOT end a sentence.
_ABBREV = {"mr", "mrs", "ms", "dr", "st", "prof", "sr", "jr", "vs", "etc", "no",
           "vol", "ch", "mt", "rev", "gen", "col", "capt", "sgt", "lt", "hon",
           "esq", "ave", "inc", "ltd", "co", "fig", "pp", "al", "ed"}
_END = re.compile(r"[.!?][\"')\]]*(?:\s+|$)")


def split_sentences(text):
    """A small, abbreviation-aware sentence splitter. Collapses whitespace and
    keeps terminal punctuation with each sentence."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    out, start = [], 0
    for m in _END.finditer(text):
        chunk = text[start:m.end()]
        word = re.search(r"([A-Za-z]+)[.!?][\"')\]]*\s*$", chunk)
        w = word.group(1).lower() if word else ""
        if w in _ABBREV or (len(w) == 1 and w.isalpha()):    # "Mr." / initials "H."
            continue
        s = chunk.strip()
        if s:
            out.append(s)
        start = m.end()
    tail = text[start:].strip()
    if tail:
        out.append(tail)
    return out


def segment(text):
    """Clean + segment raw body text into ``[[sentence, ...], ...]`` (paragraphs
    of sentences), ready to narrate. Along the way it ASCII-folds, strips the
    Project Gutenberg legal band, removes non-story markup ([Illustration]/
    [Sidenote], ``_italic_`` underscores) and drops the leading title page / table
    of contents / list of illustrations, so the narration starts at the story (and
    a genuine preface/prologue is preserved)."""
    body = _strip_markup(to_ascii(strip_boilerplate(text)))
    paras = _drop_frontmatter(split_paragraphs(body))
    paras = _drop_tail(paras)                      # trailing transcriber notes / appendix
    out = []
    for para in paras:
        if _is_dropped_para(para):                # divider / footnote block / stray TOC
            continue
        sents = split_sentences(para)
        if sents:
            out.append(sents)
    return out


# --- chapter detection (for navigation) ------------------------------------

_HEADING = re.compile(
    r"^(chapter|book|part|canto|act|scene|volume|letter|stave|prologue|epilogue)\b.{0,40}$"
    r"|^[IVXLCDM]{1,8}\.?$|^\d{1,3}\.?$"
    # "I. THE RIVER BANK" / "1. The Old Sea-dog" -- a numeral + a comma/digit-free
    # title (so a name-initial dateline like 'L. Frank Baum, Chicago, 1900' is NOT
    # mistaken for a roman-numeral chapter heading).
    r"|^(?:[IVXLCDM]{1,8}|\d{1,3})\.\s+[A-Za-z\"'(][^,\d\n]{0,45}$", re.I)
# An all-caps title / running-head line ("THE RIVER BANK", "MR. BADGER").
_HEADING_CAPS = re.compile(r"^[A-Z][A-Z0-9 ,.'\"&:;()/-]{1,46}$")


def is_heading(s):
    """A heading-like line -- a chapter / book / part marker, a lone roman numeral
    or number, a 'I. THE RIVER BANK', or an all-caps title with no terminal
    sentence punctuation. Kept in the book for navigation + the read-along view,
    but skipped by the narrator (see :func:`is_narratable`)."""
    s = (s or "").strip()
    if not (0 < len(s) <= 60):
        return False
    if _HEADING.match(s):
        return True
    # an all-caps line that does NOT end like a sentence is a title, not prose.
    # Require it to be digit-free so a version / edition line ("MILLENNIUM EDITION
    # 3.0") is treated as front-matter, not kept as a chapter heading. (Numbered
    # headings -- 'CHAPTER 1', a lone roman / number -- are caught by _HEADING.)
    if (s[-1] not in ".?!" and _HEADING_CAPS.match(s)
            and not any(c.islower() or c.isdigit() for c in s)):
        return True
    return False


def chapter_marks(paragraphs):
    """Return ``[(paragraph_index, title), ...]`` for heading-like paragraphs (a
    short line such as 'CHAPTER IV', 'I. THE RIVER BANK' or a lone roman numeral)."""
    marks = []
    for i, para in enumerate(paragraphs):
        text = " ".join(para) if isinstance(para, list) else str(para)
        if is_heading(text):
            marks.append((i, text.strip()))
    return marks


# --- non-story material removal (so it isn't narrated) ---------------------

# Editorial markers Project Gutenberg leaves inline; never spoken aloud.
_ILLUS = re.compile(
    r"\[\s*(?:illustration|sidenote|image|picture|figure|plate|music)\b[^\]]*\]",
    re.I)
_FOOTREF = re.compile(r"\[\d{1,3}\]")          # inline footnote reference markers
# Gutenberg marks italics with underscores (``_very_``); fold to the bare word.
_ITALIC = re.compile(
    r"(?<![A-Za-z0-9])_([A-Za-z0-9][^_\n]*?[A-Za-z0-9]|[A-Za-z0-9])_(?![A-Za-z0-9])")
_TOC_HEAD = re.compile(
    r"^\s*(contents|table of contents|index|list of (?:illustrations|plates))\s*$",
    re.I)
# A run of 'CHAPTER <numeral>' references packed together == a table-of-contents
# blob (real prose almost never lists three numbered chapters in one paragraph).
_TOC_BLOB = re.compile(r"(?:chapter|book|part|canto|letter|stave)\s+[ivxlcdm\d]+\b", re.I)
# A line of only punctuation / asterisks / dashes == a scene divider, not prose.
_DIVIDER = re.compile(r"^[\s*._\-=~+#<>]+$")
# A paragraph that begins a footnote block, e.g. '[1] ...' or '[12] ...'.
_FOOTBLOCK = re.compile(r"^\[\d{1,3}\]")
# Trailing non-story matter (only cut in the LATTER part of the book).
_TAIL = re.compile(
    r"^(transcriber'?s?\s+note|footnotes?\b|appendi(x|ces)\b|glossary\b)", re.I)
# Title-page byline / edition lines that DO end in punctuation (so they slip past
# the bare-title test) -- still front-matter, only stripped before the story starts.
_BYLINE = re.compile(
    r"^(by\s|author\s+of\b|translated\b|illustrated\b|edited\b|adapted\b"
    r"|a\s+(?:story|tale|novel|romance|comedy|fairy)\b|copyright\b|published\b"
    r"|printed\b|new\s+(?:and\s+revised|edition)|\w+\s+edition\b)", re.I)
# A single table-of-contents *entry* -- a line that BEGINS with 'CHAPTER <numeral>'
# (often with a long page-summary trailing). The body's real chapter heading is the
# short structural form, caught by `_is_structural_heading` first, so this only
# strips the contents list, never the chapter that starts the story.
_TOC_ENTRY = re.compile(r"^(chapter|book|part|canto|letter|volume|stave)\s+[ivxlcdm\d]+\b", re.I)
# A table-of-contents / list-of-illustrations *line*: dot-leaders ('. . . .') or a
# trailing page number ('The End 476', 'I. The Old Sea-dog ... 11'). Real prose
# paragraphs don't end in a bare number or carry spaced-dot leaders.
_TOC_LINE = re.compile(r"\.\s+\.\s+\.|\s\d{1,4}\s*$")
# A digitiser / edition / transcriber note that some texts keep at the very front
# (e.g. 'A Millennium Fulcrum Edition produced ... in the public domain ...').
_EDITION_NOTE = re.compile(
    r"(millennium fulcrum|fulcrum edition|duncan research|\betexts?\b|\bebooks?\b"
    r"|\be-texts?\b|\be-books?\b|digiti[sz]|transcrib|proofread|this electronic"
    r"|electronic (?:version|edition)|in the public domain)", re.I)


_STRAY_US = re.compile(r"_(?=[A-Za-z])|(?<=[A-Za-z])_")   # a lone, unpaired italic _


def _strip_markup(body):
    """Drop inline [Illustration]/[Sidenote] markers + footnote refs, and unwrap
    ``_italics_`` -- none of which should be spoken aloud."""
    body = _FOOTREF.sub("", _ILLUS.sub(" ", body or ""))
    body = _ITALIC.sub(r"\1", body)
    return _STRAY_US.sub("", body)      # drop any leftover lone italic underscores


def _is_structural_heading(s):
    """A *structural* chapter heading -- 'CHAPTER IV', a lone roman/number, or
    'I. THE RIVER BANK' -- i.e. the heading regex, NOT the bare all-caps fallback.
    This is what marks the start of the story (a bare all-caps line at the very top
    is more likely the book's TITLE, so it must not halt the front-matter scrub)."""
    s = (s or "").strip()
    return 0 < len(s) <= 60 and bool(_HEADING.match(s))


def _is_titlepage_line(p):
    """A title / author / edition line of the front matter: a bare short line with no
    sentence punctuation (incl. an all-caps book title), OR an explicit byline/edition
    line even when it ends in a period ('Author of "The Golden Age," Etc.'). NOT a
    *structural* chapter heading (those mark the start of the story and are kept)."""
    s = p.strip()
    if not (0 < len(s) <= 70) or _is_structural_heading(s):
        return False
    return (s[-1] not in ".?!") or bool(_BYLINE.match(s))


def _is_toc_blob(p):
    return len(_TOC_BLOB.findall(p)) >= 3


def _is_dropped_para(p):
    """A paragraph to drop from the book entirely (not just from narration): a
    scene divider, a footnote block, or a stray table-of-contents line that wasn't
    caught up front. Positively-identified non-prose only -- never plain story."""
    s = (p or "").strip()
    return (not s or bool(_DIVIDER.match(s)) or bool(_FOOTBLOCK.match(s))
            or bool(_TOC_HEAD.match(s)) or _is_toc_blob(s))


def is_narratable(sentence):
    """False for a line the narrator should NOT read aloud -- a chapter heading or a
    divider. It stays in the book (so the read-along view shows it and jump-to-chapter
    can land on it), but the narrator skips it, so it never announces 'Chapter Two'."""
    s = (sentence or "").strip()
    return bool(s) and not is_heading(s) and not _DIVIDER.match(s)


def _first_chapter_index(paras):
    """Index of the first *isolated* structural chapter heading -- the start of the
    story in a **chaptered** book -- or ``None`` if the text has no chapter
    structure. A heading inside a contents *run* (each one followed by another
    heading / TOC entry / page-numbered contents line) is skipped, so a table of
    contents never counts; the real chapter heading is the first one followed by
    something that is NOT itself a heading / contents line (the story prose)."""
    n = len(paras)
    for i in range(min(n, 400)):
        if not _is_structural_heading(paras[i].strip()):
            continue
        nxt = paras[i + 1].strip() if i + 1 < n else ""
        if (_is_structural_heading(nxt) or _TOC_ENTRY.match(nxt)
                or _TOC_LINE.search(nxt)):
            continue                            # part of a contents run -> not the start
        return i
    return None


def _heading_is_first(s):
    """True if a structural heading is the FIRST chapter -- 'CHAPTER I', 'I. ...',
    '1. ...', 'PART ONE'. Used to tell a book whose chapter 1 carries a heading from
    one whose chapter 1 has none (its first heading is 'CHAPTER II')."""
    s = (s or "").strip().lower()
    s = re.sub(r"^(chapter|book|part|canto|act|scene|volume|letter|stave)\s+", "", s)
    m = re.match(r"([ivxlcdm]+|\d+|one|first)\b", s)
    return (not m) or m.group(1) in ("i", "1", "one", "first")


def _is_frontmatter_line(p):
    """A positively-identified front-matter *boundary* line -- byline / edition / TOC
    head / contents entry / a dot-leader or page-number plate line. Used to find
    where the front matter ends when chapter 1 itself carries no heading. Kept strict
    (no bare short-line / titlepage guess) so a stray bracket left by an illustration
    inside the story doesn't look like a boundary and truncate chapter 1."""
    s = (p or "").strip()
    return bool(_TOC_HEAD.match(s) or _is_toc_blob(s) or _TOC_ENTRY.match(s)
                or _EDITION_NOTE.search(s) or _BYLINE.match(s)
                or (len(s) <= 70 and _TOC_LINE.search(s)))


def _drop_frontmatter(paras):
    """Drop the non-story matter Project Gutenberg keeps before the text -- title
    page, edition note, table of contents, list of illustrations, dedication,
    **editor's preface / introduction**. For a *chaptered* book the story begins at
    chapter 1, so everything before it is dropped (this is what skips a long critic's
    introduction -- e.g. Saintsbury's before *Pride and Prejudice* -- a dedication or
    a 'by the same author' list). A text with **no chapter structure** keeps its
    first real prose, removing only positively identified leading front-matter."""
    h = _first_chapter_index(paras)
    if h is not None:
        if _heading_is_first(paras[h]):
            return paras[h:]                    # chapter 1 has a heading: start there
        # The first heading is 'CHAPTER II' etc -- chapter 1 carries NO heading (e.g.
        # Pride & Prejudice opens straight into 'It is a truth...'). Back up over the
        # contiguous story prose to the end of the front matter, and start there.
        i = h
        while i > 0 and not _is_frontmatter_line(paras[i - 1]):
            i -= 1
        return paras[i:]
    # heading-less text: keep the first real prose paragraph.
    i = 0
    dropped = 0
    while i < len(paras) and i < 300:
        p, s = paras[i], paras[i].strip()
        if (_TOC_HEAD.match(s) or _is_toc_blob(s) or _TOC_ENTRY.match(s)
                or _EDITION_NOTE.search(s) or _is_titlepage_line(p)
                or (len(s) <= 70 and _TOC_LINE.search(s))):
            i += 1               # title / byline / edition / contents / toc entry / plate
            dropped += 1
            continue
        # once front matter has been seen, a remaining *short* line is almost always
        # a stray illustration caption ('Cat and Toys'), not the story's first prose.
        if dropped and len(s) < 120:
            i += 1
            continue
        break                                   # first real prose paragraph
    return paras[i:]


def _drop_tail(paras):
    """Cut trailing non-story matter -- a transcriber's note, footnotes section,
    appendix or glossary that sits after the story but before the PG END band. Only
    acts on an explicit marker in the LATTER part of the book, so it never truncates
    the story itself."""
    n = len(paras)
    for i in range(n):
        s = paras[i].strip()
        if i >= n * 0.55 and len(s) <= 60 and _TAIL.match(s):
            return paras[:i]
    return paras
