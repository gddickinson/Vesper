"""The audiobook **library**: a Book model + local storage, built on the pure
:mod:`breathsim.booktext` tokenizer. No network here -- books arrive as raw text
(a downloader or a user upload, in later rounds) and are segmented, saved locally
and indexed so they can be narrated like any other story.

Storage (all under the user data dir, never the repo):
  * full book content -> ``~/.breathsim/books/<id>.json``;
  * a lightweight **index** ("books table") -> ``store.books_list`` so the
    Library can list titles without loading every book;
  * a **resume position** (a sentence index) -> ``store.book_position``.

A :class:`Book` holds ``paragraphs`` (a list of paragraphs, each a list of
sentences). :meth:`Book.sentences` flattens them for narration / resume; the
paragraph boundaries are kept so the narrator can breathe between paragraphs.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from . import booktext, store

# Local library dir (under the user data dir; honours $BREATHSIM_HOME via store).
# Tests repoint this for isolation. Content lives as <id>.json files here; a small
# ``_index.json`` ("books table") + ``_progress.json`` (resume) sit alongside.
LIB_DIR = os.path.join(store.DIR, "books")


def _meta_read(name, default):
    try:
        with open(os.path.join(LIB_DIR, name)) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _meta_write(name, data):
    try:
        os.makedirs(LIB_DIR, exist_ok=True)
        with open(os.path.join(LIB_DIR, name), "w") as fh:
            json.dump(data, fh)
    except OSError:
        pass


@dataclass
class Book:
    id: str
    title: str
    author: str = ""
    source: str = "upload"                 # gutenberg | standard | upload
    paragraphs: list = field(default_factory=list)   # [[sentence, ...], ...]

    # --- narratable shape ---
    def sentences(self):
        """A flat, ordered list of every sentence (the resume/narration unit)."""
        return [s for para in self.paragraphs for s in para]

    def sentence_count(self):
        return sum(len(p) for p in self.paragraphs)

    def paragraph_starts(self):
        """Flat sentence index at which each paragraph begins (for pausing)."""
        starts, n = [], 0
        for para in self.paragraphs:
            starts.append(n)
            n += len(para)
        return starts

    def to_dict(self):
        return {"id": self.id, "title": self.title, "author": self.author,
                "source": self.source, "paragraphs": self.paragraphs}

    def meta(self):
        return {"id": self.id, "title": self.title, "author": self.author,
                "source": self.source, "sentences": self.sentence_count()}


def from_dict(d):
    return Book(id=d.get("id") or make_id(d.get("title", "")),
               title=d.get("title", "Untitled"), author=d.get("author", ""),
               source=d.get("source", "upload"),
               paragraphs=d.get("paragraphs", []))


def make_id(title, author=""):
    """A filesystem-safe slug from title (+author), stable + collision-resistant."""
    base = re.sub(r"[^a-z0-9]+", "-", f"{title} {author}".lower()).strip("-")
    return (base or "book")[:60]


def from_text(text, title, author="", source="upload"):
    """Segment raw book *text* into a :class:`Book` (boilerplate-stripped, ASCII,
    paragraphs of sentences). Pure -- does not save."""
    paras = booktext.segment(text or "")
    return Book(id=make_id(title, author), title=(title or "Untitled").strip(),
                author=(author or "").strip(), source=source, paragraphs=paras)


# --- local storage ---------------------------------------------------------

def _content_path(book_id):
    return os.path.join(LIB_DIR, f"{book_id}.json")


def save(book):
    """Persist *book* content to the library dir + record it in the index. Returns
    the book id. Refuses to save an empty book (no sentences)."""
    if not isinstance(book, Book) or book.sentence_count() == 0:
        return None
    os.makedirs(LIB_DIR, exist_ok=True)
    with open(_content_path(book.id), "w") as fh:
        json.dump(book.to_dict(), fh)
    idx = [b for b in list_books() if b.get("id") != book.id]
    idx.append(book.meta())
    _meta_write("_index.json", idx)
    return book.id


def load(book_id):
    """Load a Book by id from the library, or None if missing/corrupt."""
    try:
        with open(_content_path(book_id)) as fh:
            return from_dict(json.load(fh))
    except (OSError, ValueError):
        return None


def list_books():
    """The library index (metadata only): id / title / author / source / sentences."""
    d = _meta_read("_index.json", [])
    return d if isinstance(d, list) else []


def exists(book_id):
    return os.path.exists(_content_path(book_id))


def delete(book_id):
    """Remove a book's content, index entry and saved resume position."""
    try:
        os.remove(_content_path(book_id))
    except OSError:
        pass
    _meta_write("_index.json", [b for b in list_books() if b.get("id") != book_id])
    clear_position(book_id)


# --- resume position (a flat sentence index) -------------------------------

def _progress():
    d = _meta_read("_progress.json", {})
    return d if isinstance(d, dict) else {}


def position(book_id):
    """The saved sentence index to resume from (0 if none/finished)."""
    e = _progress().get(book_id, {})
    return int(e.get("sentence", 0)) if isinstance(e, dict) else 0


def set_position(book_id, sentence_index):
    if not book_id:
        return
    import datetime as _dt
    d = _progress()
    d[book_id] = {"sentence": int(sentence_index), "t": _dt.date.today().isoformat()}
    _meta_write("_progress.json", d)


def clear_position(book_id):
    d = _progress()
    d.pop(book_id, None)
    _meta_write("_progress.json", d)
