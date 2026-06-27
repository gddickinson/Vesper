#!/usr/bin/env python3
"""Export the desktop content (lectures, patterns, breath ambiences) to JSON so
the native iOS app can bundle the full library. Run from the repo root:

    python ios/tools/export_content.py

Writes ios/Vesper/Vesper/Content/lectures.json (and prints a summary). The Swift
LectureStore reads this from the app bundle. Re-run whenever the Python content
changes.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from breathsim import lectures  # noqa: E402

OUT = os.path.join(ROOT, "ios", "Vesper", "Vesper", "Content", "lectures.json")


def export_lectures() -> list[dict]:
    out = []
    for name in lectures.names():
        lec = lectures.LECTURES[name]
        lines: list[str] = []
        for section in lec.sections:
            # sections are already lists of gentle, sentence-length strings
            for s in section:
                s = " ".join(str(s).split())
                if s:
                    lines.append(s)
        out.append({
            "title": lec.name,
            "branch": lec.category,
            "ambience": lec.ambience,
            "lines": lines,
        })
    return out


def main() -> None:
    data = {"lectures": export_lectures(),
            "branches": lectures.categories()}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    n = len(data["lectures"])
    words = sum(len(" ".join(l["lines"]).split()) for l in data["lectures"])
    size = os.path.getsize(OUT)
    print(f"wrote {n} lectures across {len(data['branches'])} branches "
          f"({words:,} words, {size/1024:.0f} KB) -> {OUT}")


if __name__ == "__main__":
    main()
