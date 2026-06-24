"""Decide where to resume a long bedtime lecture, gently and honestly.

Pure + testable. Given a stored progress entry (`{"section": int, "t": iso}`)
and the lecture's total section count, `start_section(...)` returns the section
to begin at: it only resumes when the user got a fair way in (past the early
sections) and not basically to the end, and not too long ago -- otherwise it
returns 0 to start fresh. It just remembers a rough spot.
"""
from __future__ import annotations

import datetime as _dt


def start_section(entry, total, today=None, max_age_days=14, min_section=2):
    """Section to resume at (0 = start fresh) for a stored *entry* and *total*."""
    if not entry or total <= 0:
        return 0
    s = int(entry.get("section", 0))
    if s < min_section or s >= total - 1:        # too early, or basically finished
        return 0
    t = entry.get("t")
    if t and today is not None:
        try:
            d = _dt.date.fromisoformat(str(t)[:10])
            if (today - d).days > max_age_days:  # stale -> start fresh
                return 0
        except ValueError:
            pass
    return min(s, total - 1)
