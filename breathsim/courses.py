"""Multi-night guided courses: an optional, gentle sequence of sessions over days.

A :class:`Course` is an ordered list of :class:`Day`s. Each Day reuses an
*existing* building block -- a guided :mod:`~breathsim.programs` program or a
mode -- plus a one-line intention, so no new audio is invented here. Progress is
remembered per course in :mod:`~breathsim.store`: the day you are on advances
only when a session actually completes, so you can return night after night and
pick up where you left off.

This is gentle structured practice, not a medical or clinical programme.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Day:
    intention: str
    program: str | None = None     # a programs.Program name (preferred)
    mode: str | None = None        # or a mode name (Meditate/Sleep/...)


@dataclass
class Course:
    name: str
    description: str
    unit: str                      # "Night" / "Day" / "Morning" (how a day reads)
    days: list = field(default_factory=list)

    @property
    def total(self):
        return len(self.days)


COURSES: list[Course] = []
_BY_NAME: dict[str, Course] = {}


def _add(name, description, unit, days):
    c = Course(name, description, unit, days)
    COURSES.append(c)
    _BY_NAME[name] = c


def names():
    return [c.name for c in COURSES]


def get(name):
    return _BY_NAME.get(name)


def day_label(course, idx):
    """e.g. 'Night 3 of 7' (idx is 0-based)."""
    return f"{course.unit} {idx + 1} of {course.total}"


def apply_day(app, course, idx):
    """Apply one course day to the app, reusing the normal session machinery.

    *idx* is clamped to a real day, so a corrupt/legacy saved position (negative,
    or past the end) can never IndexError -- it just falls back to the nearest
    valid day rather than crashing the night's sit."""
    if not course or not course.days:
        return
    idx = max(0, min(int(idx), course.total - 1))
    day = course.days[idx]
    if day.program:
        app.start_session_mode(day.program)
    elif day.mode:
        app.apply_mode(day.mode)
        app._ensure_running()
    if day.intention:
        try:
            app.speech.announce(day.intention)        # spoken, if cues are on
        except Exception:
            pass


# --- courses ---------------------------------------------------------------
# Each day points at an existing program (see programs.names()) or a mode.

_add("7 Nights to Sleep",
     "A week of gentler nights, easing gradually into sleep.", "Night",
     [Day("Arrive in bed, and let the breath begin to slow.",
          program="Sleep Wind-Down (18 min)"),
      Day("Tonight, simply rest deeply, without trying to sleep.",
          program="NSDR / Yoga Nidra (12 min)"),
      Day("Soften the whole body, from the feet to the head.",
          program="Body & Breath (10 min)"),
      Day("Let a quiet bedtime story carry you off.", mode="Sleep"),
      Day("Unwind the day, and lengthen each out-breath.",
          program="Calm & Unwind (12 min)"),
      Day("Return to deep rest, and notice it comes a little easier.",
          program="NSDR / Yoga Nidra (12 min)"),
      Day("Trust the slow wind-down now, and sleep well.", mode="Sleep")])

_add("Ten Days of Calm",
     "Ten days of steady, simple practice to settle the mind.", "Day",
     [Day("Begin gently; there is nothing to achieve.",
          program="Calm & Unwind (12 min)"),
      Day("Sit, and simply follow the natural breath.", mode="Meditate"),
      Day("A slow, breath-paced scan through the body.",
          program="Body & Breath (10 min)"),
      Day("Try a slower, longer out-breath today.", mode="Breathwork"),
      Day("A fuller pranayama practice, energising then calming.",
          program="Pranayama (15 min)"),
      Day("Rest the attention on the breath, and let it stay.",
          mode="Meditate"),
      Day("Non-sleep deep rest: still, and at ease.",
          program="NSDR / Yoga Nidra (12 min)"),
      Day("Let a layered soundscape simply hold you.", mode="Relax"),
      Day("Unwind once more, with a little more ease.",
          program="Calm & Unwind (12 min)"),
      Day("Sit, and gently notice what has changed.", mode="Meditate")])

_add("Five Mornings to Energize",
     "Five brighter mornings of breathwork to wake the body.", "Morning",
     [Day("Wake the body with a few easy breaths.", mode="Breathwork"),
      Day("A short, brightening set of breathwork.",
          program="Energize (8 min)"),
      Day("Power breaths, gentle holds, and recovery.",
          program="Wim Hof (3 rounds)"),
      Day("A fuller pranayama practice to clear the mind.",
          program="Pranayama (15 min)"),
      Day("Energize once more, and carry it into your day.",
          program="Energize (8 min)")])
