"""The phase of the Moon for a given date -- pure, dependency-free and testable.

A small synodic-month model: the Moon cycles new -> full -> new every ~29.53 days
from a known new-moon reference. Accurate to about a day, which is plenty to draw
tonight's moon and name its phase. No I/O, no globals; pass a ``datetime.date``
(or let it default to today).

  phase_fraction(d) -> 0..1 through the cycle (0 = new, 0.5 = full)
  illumination(d)   -> lit fraction of the disc, 0 (new) .. 1 (full)
  waxing(d)         -> True while growing (new->full), False while waning
  phase_name(d)     -> "New Moon" / "Waxing Crescent" / "First Quarter" / ...
"""
from __future__ import annotations

import datetime as _dt
import math

SYNODIC = 29.530588853                  # mean length of a lunar month, in days
# A known new moon: 2000-01-06 at 18:14 UTC, as a fractional day number.
_EPOCH = _dt.date(2000, 1, 6).toordinal() + (18.0 + 14.0 / 60.0) / 24.0

_NAMES = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
          "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]


def _age_days(d=None) -> float:
    """Days since the reference new moon (the date taken at local noon)."""
    d = d or _dt.date.today()
    return (d.toordinal() + 0.5) - _EPOCH


def phase_fraction(d=None) -> float:
    """Position in the cycle: 0 = new, 0.25 first quarter, 0.5 full, 0.75 last."""
    return (_age_days(d) % SYNODIC) / SYNODIC


def illumination(d=None) -> float:
    """The lit fraction of the disc, 0.0 at new moon up to 1.0 at full moon."""
    return (1.0 - math.cos(2.0 * math.pi * phase_fraction(d))) / 2.0


def waxing(d=None) -> bool:
    """True while the Moon is growing (new -> full), False while it wanes."""
    return phase_fraction(d) < 0.5


def phase_name(d=None) -> str:
    """The familiar name of tonight's phase (eighth-of-cycle bins, with the four
    principal phases -- new / first quarter / full / last quarter -- centred)."""
    idx = int(((phase_fraction(d) + 0.0625) % 1.0) * 8) % 8
    return _NAMES[idx]
