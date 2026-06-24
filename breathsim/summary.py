"""A small, friendly practice summary you can keep or share.

Pure and unit-testable: build a few honest lines from an optional last-session
dict (``{"minutes": float, "mode": str}``) plus the practice ``history``. Nothing
is read from globals; pass ``today`` to test. It only summarises logged data --
no claims -- and has a graceful empty state for a new user.
"""
from __future__ import annotations

import datetime as _dt

from . import store


def last_session_line(last):
    """A line for the just-finished sit, or None if there isn't a real one."""
    if not last:
        return None
    mins = float(last.get("minutes", 0.0))
    if mins < 0.5:
        return None
    mm = max(1, int(round(mins)))
    mode = last.get("mode")
    line = f"This sit: {mm} min"
    if mode:
        line += f" of {mode}"
    return line + "."


def summary_lines(last=None, hist=None, today=None):
    """A short list of friendly summary lines (first line is the title)."""
    hist = hist if hist is not None else store.history()
    today = today or _dt.date.today()
    out = ["Vesper - practice summary", today.strftime("%A %d %B %Y")]
    ls = last_session_line(last)
    if ls:
        out.append(ls)
    sits = int(hist.get("sits", 0))
    if sits > 0:
        mins = float(hist.get("minutes", 0.0))
        s = "session" if sits == 1 else "sessions"
        out.append(f"All time: {sits} {s}, {mins:.0f} min.")
        cur, best = store.streak(hist, today)
        if cur > 0:
            d = "day" if cur == 1 else "days"
            out.append(f"Current streak: {cur} {d} (best {best}).")
    elif not ls:
        out.append("No sessions logged yet - your summary fills in as you practise.")
    out.append("")
    out.append("Be well, and rest easy.")
    return out


def summary_text(last=None, hist=None, today=None):
    return "\n".join(summary_lines(last, hist, today))
