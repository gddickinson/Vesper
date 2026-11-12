"""Keep the counts quoted in README.md and CLAUDE.md in step with the code.

The numbers (voices, lectures, branches, phrases, modes, patterns, programs, characters,
costumes) are computed from the real registries -- the same ``vesper.web.catalog.info()``
the web pages use, plus the cartoon-cast registry -- never typed by hand.

    python scripts/doc_counts.py          # rewrite the counts in README.md / CLAUDE.md
    python scripts/doc_counts.py --check  # exit 1 and list what is stale (used by the tests)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# (file, pattern, count key). Each pattern has exactly one group: the number to keep current.
# Whitespace in a phrase may be a line break, so phrases are written with \s+.
RULES = [
    ("README.md", r"<!-- counts: (\d+) lectures", "lectures"),
    ("README.md", r"<!-- counts: \d+ lectures / (\d+) branches", "branches"),
    ("README.md", r"<!-- counts: [^>]*?· (\d+) voices", "voices"),
    ("README.md", r"<!-- counts: [^>]*?· (\d+) phrases", "phrases"),
    ("README.md", r"<!-- counts: [^>]*?· (\d+) modes", "modes"),
    ("README.md", r"<!-- counts: [^>]*?· (\d+) characters", "characters"),
    ("README.md", r"<!-- counts: [^>]*?· (\d+) costumes", "costumes"),
    ("README.md", r"\*\*(\d+)\s+hand-drawn\s+cartoon\s+characters\*\*", "characters"),
    ("README.md", r"library of \*\*(\d+)\s+soothing\s+sleep-lectures\*\*", "lectures"),
    ("README.md", r"\*\*(\d+) voices\*\* synthesised", "voices"),
    ("README.md", r"\*\*(\d+)\s+authored\s+sleep-lectures", "lectures"),
    ("README.md", r"authored\s+sleep-lectures\s+across\s+(\d+)\s+branches", "branches"),
    ("README.md", r"\*\*(\d+)\s+mantras, chants", "phrases"),
    ("README.md", r"\(200\+ stories, (\d+) voices\)", "voices"),
    ("README.md", r"All (\d+) patterns or paced breathing", "patterns"),
    ("CLAUDE.md", r"(\d+) modes, \d+ voices", "modes"),
    ("CLAUDE.md", r"\d+ modes, (\d+) voices", "voices"),
    ("CLAUDE.md", r"(\d+)\s+breath\s+patterns", "patterns"),
    ("CLAUDE.md", r"(\d+) guided programs", "programs"),
    ("CLAUDE.md", r"(\d+) chants", "phrases"),
    ("CLAUDE.md", r"\*\*(\d+) sleep-lectures across \d+ branches\*\*", "lectures"),
    ("CLAUDE.md", r"\*\*\d+ sleep-lectures across (\d+) branches\*\*", "branches"),
    ("CLAUDE.md", r"(\d+)\s+cartoon characters", "characters"),
]


def counts() -> dict:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from vesper import characters
    from vesper.web import catalog
    c = catalog.info()
    out = {k: c[k] for k in ("lectures", "branches", "voices", "phrases", "modes",
                             "patterns", "programs")}
    out["characters"] = len(characters.names())
    out["costumes"] = len(characters.costume_names())
    return out


def apply(write: bool) -> list[str]:
    """Return a list of stale spots ('file: key was X, code says Y'); rewrite them if *write*."""
    want = counts()
    stale, texts = [], {}
    for fname, pat, key in RULES:
        text = texts.setdefault(fname, (ROOT / fname).read_text(encoding="utf-8"))
        m = re.search(pat, text)
        if not m:
            stale.append(f"{fname}: pattern for {key!r} not found ({pat})")
            continue
        if int(m.group(1)) != want[key]:
            stale.append(f"{fname}: {key} says {m.group(1)}, code has {want[key]}")
            texts[fname] = text[:m.start(1)] + str(want[key]) + text[m.end(1):]
    if write:
        for fname, text in texts.items():
            (ROOT / fname).write_text(text, encoding="utf-8")
    return stale


def main(argv=None) -> int:
    check = "--check" in (argv if argv is not None else sys.argv[1:])
    stale = apply(write=not check)
    for line in stale:
        print(("stale: " if check else "updated: ") + line)
    if check:
        return 1 if stale else 0
    missing = [s for s in stale if "not found" in s]
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
