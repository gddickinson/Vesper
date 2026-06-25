"""Narration captions -- wrap a spoken line into a few centred display lines.

Pure, Qt-free text helper for the accessibility "Narration captions" toggle: the
storyteller / guided-session / lecture narration speaks one line at a time, and
when captions are on the GUI shows that *full* line as on-screen text (the small
scene subtitle is otherwise truncated). This module just turns one sentence into
a short list of word-wrapped lines, eliding gracefully if a line is unusually
long so the caption never grows past a few rows. Offline + unit-testable.
"""
from __future__ import annotations


def wrap(text, width=42, max_lines=3):
    """Word-wrap ``text`` into at most ``max_lines`` lines of about ``width``
    characters each. Returns a list of stripped lines (possibly empty). If the
    text does not fit, the last kept line is elided with a trailing ellipsis so
    the caption stays a fixed, calm size on screen."""
    if not text:
        return []
    width = max(8, int(width))
    max_lines = max(1, int(max_lines))
    words = str(text).split()
    lines = []
    cur = ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
        if len(lines) == max_lines:            # no more room -- elide and stop
            break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    # A single over-long word (or a truncated overflow) gets a soft ellipsis.
    leftover = len(words) > sum(len(ln.split()) for ln in lines)
    if lines and (leftover or len(lines[-1]) > width):
        last = lines[-1]
        if len(last) > width - 1:
            last = last[:width - 1].rstrip()
        lines[-1] = last + "..."
    return lines
