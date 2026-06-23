"""A SQLite record of every story — lectures + scenes — built from the source.

Lets the whole library be recorded, browsed and searched as data. ``build(path)``
(re)creates the DB from the live ``lectures`` + ``stories`` registries; the other
helpers are read-only queries. Pure stdlib (``sqlite3``, LIKE search — no FTS
needed), rebuilds in well under a second. Run ``python -m breathsim.story_db`` to
(re)build it and print the stats.
"""
from __future__ import annotations

import os
import time

try:
    import sqlite3
except Exception:                  # broken/missing _sqlite3 (e.g. some Anaconda builds)
    sqlite3 = None                 # the DB feature simply disables itself


def available() -> bool:
    """True if sqlite3 works in this Python; the DB is optional otherwise."""
    return sqlite3 is not None


def default_path():
    """`<project root>/data/stories.db` (the project root holds this package)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "stories.db")


_SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE lectures (name TEXT PRIMARY KEY, category TEXT, ambience TEXT,
                       n_sections INTEGER, n_lines INTEGER, n_words INTEGER);
CREATE TABLE lines (story TEXT, section INTEGER, line INTEGER, text TEXT);
CREATE TABLE scenes (name TEXT PRIMARY KEY, ambience TEXT);
CREATE INDEX idx_lines_story ON lines(story);
"""


def build(path=None):
    """(Re)build the stories DB from the source modules. Returns the path (or None
    if sqlite3 is unavailable)."""
    if sqlite3 is None:
        return None
    from . import lectures, stories
    path = path or default_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript(_SCHEMA)
    for name in lectures.names():
        lec = lectures.get(name)
        secs = lec.sections
        n_lines = sum(len(s) for s in secs)
        n_words = sum(len(ln.split()) for s in secs for ln in s)
        con.execute("INSERT INTO lectures VALUES (?,?,?,?,?,?)",
                    (name, lec.category, lec.ambience, len(secs), n_lines, n_words))
        for si, sec in enumerate(secs):
            for li, ln in enumerate(sec):
                con.execute("INSERT INTO lines VALUES (?,?,?,?)", (name, si, li, ln))
    for sname, scene in stories.SCENES.items():
        con.execute("INSERT INTO scenes VALUES (?,?)", (sname, scene.ambience))
    con.execute("INSERT INTO meta VALUES ('built_at', ?)",
                (time.strftime("%Y-%m-%d %H:%M:%S"),))
    con.execute("INSERT INTO meta VALUES ('n_lectures', ?)",
                (str(len(lectures.names())),))
    con.commit()
    con.close()
    return path


def ensure(path=None):
    """Build the DB if it's missing; return the path (or None if unavailable)."""
    if sqlite3 is None:
        return None
    path = path or default_path()
    if not os.path.exists(path):
        build(path)
    return path


def connect(path=None):
    if sqlite3 is None:
        raise RuntimeError("sqlite3 is unavailable in this Python environment")
    con = sqlite3.connect(path or default_path())
    con.row_factory = sqlite3.Row
    return con


# --- read helpers ----------------------------------------------------------
def categories(con):
    return [r[0] for r in con.execute(
        "SELECT DISTINCT category FROM lectures ORDER BY rowid")]


def lectures_in(con, category=None):
    if category:
        return list(con.execute(
            "SELECT * FROM lectures WHERE category=? ORDER BY rowid", (category,)))
    return list(con.execute("SELECT * FROM lectures ORDER BY rowid"))


def lines_of(con, story):
    return [r["text"] for r in con.execute(
        "SELECT text FROM lines WHERE story=? ORDER BY section, line", (story,))]


def search(con, term, limit=80):
    """Lines containing *term* (case-insensitive), as (story, text) rows."""
    return list(con.execute(
        "SELECT story, text FROM lines WHERE text LIKE ? "
        "ORDER BY story LIMIT ?", (f"%{term}%", limit)))


def stats(con):
    row = con.execute(
        "SELECT COUNT(*) lectures, SUM(n_lines) lines, SUM(n_words) words "
        "FROM lectures").fetchone()
    cats = len(categories(con))
    scenes = con.execute("SELECT COUNT(*) FROM scenes").fetchone()[0]
    return dict(lectures=row["lectures"] or 0, branches=cats,
                lines=row["lines"] or 0, words=row["words"] or 0, scenes=scenes)


if __name__ == "__main__":
    p = build()
    if p:
        print("built", p)
        print(stats(connect(p)))
    else:
        print("sqlite3 unavailable in this Python — stories DB not built "
              "(the stories themselves are unaffected).")
