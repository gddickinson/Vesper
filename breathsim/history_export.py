"""Export the practice history as portable CSV / plain text.

Pure + testable: turn a `store.history()` dict into a tidy CSV (one row per day:
date, minutes, sits) with a short summary block, or a friendly text report. It
just writes the data you have logged -- no claims. Reuses the streak / insight
helpers so the figures match what the Stats dialog shows.
"""
from __future__ import annotations

from . import insights, store


def _summary_rows(hist):
    sits = int(hist.get("sits", 0))
    mins = float(hist.get("minutes", 0.0))
    cur, best = store.streak(hist)
    rows = [
        ("total_sessions", sits),
        ("total_minutes", round(mins, 1)),
        ("current_streak_days", cur),
        ("best_streak_days", best),
    ]
    avg = insights.avg_bpm(hist)
    if avg is not None:
        rows.append(("avg_breaths_per_min", avg))
    _n, _ab, _aa, shift = store.mood_summary(hist)
    if shift is not None:
        rows.append(("avg_mood_shift", shift))
    return rows


def history_csv(hist=None):
    """A CSV string: a daily table, then a blank line and a key,value summary."""
    hist = hist if hist is not None else store.history()
    lines = ["date,minutes,sits"]
    for day in sorted(hist.get("days", {})):
        v = hist["days"][day]
        lines.append(f"{day},{float(v.get('min', 0.0)):.1f},{int(v.get('sits', 0))}")
    lines.append("")
    lines.append("metric,value")
    for k, v in _summary_rows(hist):
        lines.append(f"{k},{v}")
    return "\n".join(lines) + "\n"


def history_text(hist=None):
    """A short, friendly plain-text report (title, summary, insight lines)."""
    hist = hist if hist is not None else store.history()
    out = ["Vesper - practice history", ""]
    if int(hist.get("sits", 0)) <= 0:
        out.append("No sessions logged yet - your history will fill in as you practise.")
        return "\n".join(out) + "\n"
    for k, v in _summary_rows(hist):
        out.append(f"{k.replace('_', ' ')}: {v}")
    extra = insights.lines(hist)
    if extra:
        out.append("")
        out.extend(extra)
    return "\n".join(out) + "\n"
