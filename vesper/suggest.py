"""A gentle launch suggestion: what might suit you right now.

Pure and unit-testable -- everything is derived from injected inputs (the hour,
the practice history dict, and the per-course progress dict), with no globals and
no clock reads of its own (pass ``today`` to test). The window shows the result
as a one-line, non-modal hint in the status bar while idle, and never nags.

Priority: an in-progress multi-night course (the kindest "pick up where you left
off") wins; otherwise a friendly, time-of-day mode hint, lightly coloured by any
practice streak. It is a gentle hint, not advice. Lives in the GUI layer because
the time-of-day mode mapping comes from :mod:`clocktheme`.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from breathsim import courses, store

from . import clocktheme


@dataclass
class Suggestion:
    text: str
    action: str        # a mode name or a course name
    kind: str          # "mode" | "course"


def _greeting(h: int) -> str:
    h = h % 24
    if h >= 22 or h < 6:
        return "Winding down for the night?"
    if 6 <= h < 9:
        return "Good morning."
    if 9 <= h < 12:
        return "Taking a moment this morning?"
    if 12 <= h < 17:
        return "A pause in the afternoon?"
    return "Time to unwind?"


def _in_progress_course(courses_state):
    """The most recently touched course that is started but not finished."""
    best = None
    for name, e in (courses_state or {}).items():
        c = courses.get(name)
        if not c:
            continue
        day = int(e.get("day", 0))
        if 0 < day < c.total and not e.get("completed"):
            done = e.get("done", [])
            last = done[-1] if done else ""
            if best is None or last > best[2]:
                best = (name, day, last, c)
    return best


def suggest(hour, history=None, courses_state=None, today=None) -> Suggestion:
    history = history if history is not None else store.history()
    courses_state = courses_state if courses_state is not None else store.course_state()
    today = today or _dt.date.today()

    ip = _in_progress_course(courses_state)
    if ip:
        name, day, _last, c = ip
        return Suggestion(
            f"Pick up \"{name}\" - {c.unit} {day + 1} of {c.total}.",
            name, "course")

    mode = clocktheme.suggested_mode_for_hour(hour)
    greet = _greeting(hour)
    cur, _best = store.streak(history, today)
    dm = store.daily_minutes(history)
    practised_today = dm.get(today.isoformat(), 0.0) > 0
    fresh = int(history.get("sits", 0)) == 0 and not dm

    if fresh:
        text = f"{greet} New here? {mode} is a gentle place to start."
    elif practised_today:
        text = f"You have practised today - lovely. If you like, a little {mode}."
    elif cur >= 2:
        text = f"{greet} You are on a {cur}-day streak - keep it easy with {mode}."
    else:
        text = f"{greet} {mode} suits this hour."
    return Suggestion(text, mode, "mode")
