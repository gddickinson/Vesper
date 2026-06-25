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
    out = []
    for para in paras:
        sents = split_sentences(para)
        if sents:
            out.append(sents)
    return out


# --- chapter detection (for navigation) ------------------------------------

_HEADING = re.compile(
    r"^(chapter|book|part|canto|act|scene|volume|letter)\b.{0,40}$"
    r"|^[IVXLCDM]{1,7}\.?$|^\d{1,3}\.?$", re.I)


def chapter_marks(paragraphs):
    """Return ``[(paragraph_index, title), ...]`` for heading-like paragraphs (a
    short line such as 'CHAPTER IV' or a lone roman numeral). Best-effort."""
    marks = []
    for i, para in enumerate(paragraphs):
        text = " ".join(para) if isinstance(para, list) else str(para)
        if len(text) <= 50 and _HEADING.match(text.strip()):
            marks.append((i, text.strip()))
    return marks


# --- non-story material removal (so it isn't narrated) ---------------------

# Editorial markers Project Gutenberg leaves inline; never spoken aloud.
_ILLUS = re.compile(
    r"\[\s*(?:illustration|sidenote|image|picture|figure|plate|music)\b[^\]]*\]",
    re.I)
# Gutenberg marks italics with underscores (``_very_``); fold to the bare word.
_ITALIC = re.compile(
    r"(?<![A-Za-z0-9])_([A-Za-z0-9][^_\n]*?[A-Za-z0-9]|[A-Za-z0-9])_(?![A-Za-z0-9])")
_TOC_HEAD = re.compile(
    r"^\s*(contents|table of contents|index|list of (?:illustrations|plates))\s*$",
    re.I)
# A run of 'CHAPTER <numeral>' references packed together == a table-of-contents
# blob (real prose almost never lists three numbered chapters in one paragraph).
_TOC_BLOB = re.compile(r"(?:chapter|book|part|canto|letter)\s+[ivxlcdm\d]+\b", re.I)


def _strip_markup(body):
    """Drop inline [Illustration]/[Sidenote] markers and unwrap ``_italics_``."""
    return _ITALIC.sub(r"\1", _ILLUS.sub(" ", body or ""))


def _is_heading(p):
    return len(p) <= 60 and bool(_HEADING.match(p.strip()))


def _is_titlepage_line(p):
    """A short line with no sentence punctuation -- a title / author / edition line.
    NOT a chapter heading (those mark the start of the story and must be kept)."""
    s = p.strip()
    return 0 < len(s) <= 70 and s[-1] not in ".?!" and not _HEADING.match(s)


def _is_toc_blob(p):
    return len(_TOC_BLOB.findall(p)) >= 3


def _drop_frontmatter(paras):
    """Drop a leading title page / table of contents / list of illustrations -- the
    non-story matter Project Gutenberg keeps before the text -- **stopping at the
    first chapter heading or the first real paragraph**, so the story (and any
    genuine preface) is preserved. Conservative: it only removes positively
    identified front-matter lines and never looks past the start of the story."""
    i = 0
    while i < len(paras) and i < 40:
        p = paras[i]
        if _is_heading(p):                      # a chapter heading: the story starts
            break
        if _TOC_HEAD.match(p.strip()) or _is_toc_blob(p) or _is_titlepage_line(p):
            i += 1                              # title / author / edition / contents
            continue
        break                                   # first real prose paragraph
    return paras[i:]
