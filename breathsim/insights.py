"""Gentle, honest practice insights, computed from the existing logs.

All functions are pure and unit-testable: pass a ``history`` dict (the shape
:func:`breathsim.store.history` returns) and, where relevant, ``today``. Nothing
is read from globals. Phrasing is kind and never clinical, and every helper has a
graceful empty state (returns ``None`` when there isn't enough data to say
anything honest), so a brand-new user simply sees fewer lines.

Note: time-of-day relies on an hour histogram added to ``store.log_session``
later in the project's life, so older histories without it just skip that line.
"""
from __future__ import annotations

import datetime as _dt

from . import store

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]
_TOD = [("morning", range(5, 12)), ("afternoon", range(12, 17)),
        ("evening", range(17, 22))]      # everything else is "night"


def average_minutes(hist):
    """Average length of a logged sit, or None if none yet."""
    sits = int(hist.get("sits", 0))
    if sits <= 0:
        return None
    return round(float(hist.get("minutes", 0.0)) / sits, 1)


def busiest_weekday(hist):
    """The weekday you have practised most (by minutes), or None."""
    totals = {}
    for iso, v in hist.get("days", {}).items():
        try:
            wd = _dt.date.fromisoformat(iso).weekday()
        except ValueError:
            continue
        totals[wd] = totals.get(wd, 0.0) + float(v.get("min", 0.0))
    totals = {k: m for k, m in totals.items() if m > 0}
    if len(totals) < 2:                  # need a little spread to be meaningful
        return None
    return _WEEKDAYS[max(totals, key=totals.get)]


def time_of_day(hist):
    """The part of the day you most often practise, or None if unrecorded."""
    hours = hist.get("hours", {})
    counts = {}
    total = 0
    for hr, n in hours.items():
        try:
            h = int(hr)
            n = int(n)
        except (TypeError, ValueError):
            continue
        total += n
        label = "night"
        for name, rng in _TOD:
            if h in rng:
                label = name
                break
        counts[label] = counts.get(label, 0) + n
    if total < 3:                        # too little to claim a pattern
        return None
    return max(counts, key=counts.get)


def week_over_week(hist, today=None):
    """(this_week, last_week) minutes, or None if there's no prior week."""
    dm = store.daily_minutes(hist)
    if not dm:
        return None
    today = today or _dt.date.today()
    this0 = today - _dt.timedelta(days=6)
    last0 = today - _dt.timedelta(days=13)
    last1 = today - _dt.timedelta(days=7)

    def total(a, b):
        return round(sum(m for d, m in dm.items()
                         if a <= _dt.date.fromisoformat(d) <= b), 1)
    return (total(this0, today), total(last0, last1))


def avg_bpm(hist):
    """Average logged breaths-per-minute, or None if none recorded."""
    bs = [float(x) for x in hist.get("bpm", []) if isinstance(x, (int, float))]
    if not bs:
        return None
    return round(sum(bs) / len(bs), 1)


def pace_line(hist):
    """A kind one-liner on the usual breathing pace, or None without data."""
    a = avg_bpm(hist)
    if a is None:
        return None
    txt = f"You tend to breathe around {a:g} a minute"
    if 4.0 <= a <= 7.0:                  # the resonance / coherence sweet spot
        txt += " - a calm, resonant pace."
    else:
        txt += "."
    return txt


def lines(hist=None, today=None):
    """A short list of friendly insight strings (possibly empty for a new user)."""
    hist = hist if hist is not None else store.history()
    today = today or _dt.date.today()
    out = []
    sits = int(hist.get("sits", 0))
    if sits <= 0:
        return out                       # nothing honest to say yet
    mins = float(hist.get("minutes", 0.0))
    s = "session" if sits == 1 else "sessions"
    out.append(f"{sits} {s}, {mins:.0f} min in all.")
    avg = average_minutes(hist)
    if avg is not None:
        out.append(f"Your sits average about {avg:.0f} min.")
    from . import besttime               # a precise am/pm window when there's a clear mode
    bt = besttime.best_time_phrase(hist.get("hours", {}))
    if bt:
        out.append(bt)
    else:
        tod = time_of_day(hist)
        if tod:
            out.append(f"You tend to practise in the {tod}.")
    wd = busiest_weekday(hist)
    if wd:
        out.append(f"{wd} is your most regular day.")
    wow = week_over_week(hist, today)
    if wow is not None:
        this_w, last_w = wow
        if last_w > 0 and this_w >= last_w * 1.1:
            out.append(f"This week ({this_w:.0f} min) is up on last "
                       f"week ({last_w:.0f} min) - nicely done.")
        elif last_w > 0 and this_w <= last_w * 0.6:
            out.append(f"A quieter week ({this_w:.0f} min) than last "
                       f"({last_w:.0f} min) - that is perfectly fine.")
    pace = pace_line(hist)
    if pace:
        out.append(pace)
    return out
