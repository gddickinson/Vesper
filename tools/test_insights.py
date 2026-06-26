"""Offline test for the gentle practice insights (breathsim/insights.py).

These pure helpers build the Stats dialog's kind summaries -- total time, average
sit, busiest weekday, time of day, week-over-week, this month, longest streak and
breathing pace -- each with a graceful empty state so a new user simply sees fewer
lines, and each tolerant of a corrupted / legacy history file (the #152 hardening).
This locks all of that: correct values on a realistic history with an injected
"today", the None empty-states, and -- most importantly -- that a deliberately
junk history never raises. Pure, no Qt, no store file touched.
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import insights  # noqa: E402

TODAY = dt.date(2024, 6, 15)            # a fixed Saturday, for determinism


def _iso(days_ago):
    return (TODAY - dt.timedelta(days=days_ago)).isoformat()


def _rich_history():
    """A plausible history: a week-long streak ending today, mostly evenings,
    with a couple of earlier sits, plus a resonant breathing pace."""
    days = {}
    for d in range(0, 7):               # today and the six days before -> a streak of 7
        days[_iso(d)] = {"sits": 1, "min": 10.0}
    days[_iso(8)] = {"sits": 1, "min": 6.0}     # earlier sits, in the "last week" window
    days[_iso(10)] = {"sits": 1, "min": 4.0}
    sits = sum(v["sits"] for v in days.values())
    mins = sum(v["min"] for v in days.values())
    return {
        "sits": sits, "minutes": mins, "days": days,
        "hours": {"20": 5, "21": 3, "8": 1},    # evenings dominate (total 9 >= 3)
        "bpm": [5.5, 6.0, 5.0],                  # the resonance sweet spot
    }


def test_empty_history_says_nothing():
    empty = {"sits": 0, "minutes": 0.0, "days": {}, "hours": {}, "bpm": []}
    assert insights.lines(empty, TODAY) == []
    assert insights.average_minutes(empty) is None
    assert insights.busiest_weekday(empty) is None
    assert insights.time_of_day(empty) is None
    assert insights.week_over_week(empty, TODAY) is None
    assert insights.avg_bpm(empty) is None
    assert insights.pace_line(empty) is None
    assert insights.this_month(empty, TODAY) is None
    assert insights.streak_line(empty, TODAY) is None
    print("ok: a brand-new history yields no lines and every helper -> None")


def test_values_on_a_real_history():
    h = _rich_history()
    assert insights.average_minutes(h) == 8.9           # 80 min over 9 sits
    # week-over-week split around the injected today
    this_w, last_w = insights.week_over_week(h, TODAY)
    assert this_w == 70.0, this_w                        # seven evenings of 10 min
    assert last_w == 10.0, last_w                        # the 6.0 + 4.0 earlier sits
    assert insights.time_of_day(h) == "evening"
    assert abs(insights.avg_bpm(h) - 5.5) < 1e-6
    pace = insights.pace_line(h)
    assert pace and "resonant" in pace                  # 5.5 bpm is in the sweet spot
    tm = insights.this_month(h, TODAY)
    assert tm and tm.startswith("This month:")
    sl = insights.streak_line(h, TODAY)
    assert sl and "longest streak" in sl and "on it now" in sl   # 7-day current streak
    lines = insights.lines(h, TODAY)
    assert lines and all(isinstance(s, str) and s for s in lines)
    print("ok: realistic history -> correct averages / week / pace / streak (%d lines)"
          % len(lines))


def test_thresholds():
    # a lone day is not a streak; one bpm reading still averages; <3 hours = no TOD
    h = {"sits": 1, "minutes": 8.0,
         "days": {_iso(0): {"sits": 1, "min": 8.0}},
         "hours": {"20": 1}, "bpm": [12.0]}
    assert insights.streak_line(h, TODAY) is None        # best < 2
    assert insights.time_of_day(h) is None               # total < 3
    assert insights.busiest_weekday(h) is None           # < 2 weekdays
    p = insights.pace_line(h)
    assert p and "resonant" not in p                     # 12 bpm is not the sweet spot
    print("ok: streak / time-of-day / weekday thresholds hold")


def test_corrupt_history_never_raises():
    """The #152 hardening: a damaged history must degrade, not crash."""
    junk = {
        "sits": 3, "minutes": 30.0,
        "days": {
            _iso(0): {"sits": 1, "min": 10.0},      # one good entry
            "not-a-date": {"sits": 1, "min": 5.0},  # junk key
            "2024-13-99": {"sits": 1, "min": 5.0},  # unparseable date
            _iso(2): ["not", "a", "dict"],          # non-dict value
            _iso(3): {"min": "lots"},               # non-numeric minutes
        },
        "hours": {"20": 2, "xx": 9, "25": "n"},     # junk hour keys / values
        "bpm": [4.0, "fast", None, 6.0],            # mixed bpm list (good mean = 5.0)
    }
    # none of these may raise
    for fn in (insights.average_minutes, insights.busiest_weekday,
               insights.time_of_day, insights.avg_bpm, insights.pace_line):
        fn(junk)
    insights.week_over_week(junk, TODAY)
    insights.this_month(junk, TODAY)
    insights.streak_line(junk, TODAY)
    out = insights.lines(junk, TODAY)
    assert isinstance(out, list)
    # the good bpm values still average despite the junk in the list
    assert abs(insights.avg_bpm(junk) - 5.0) < 1e-6
    print("ok: a corrupt history degrades gracefully, never raises (%d lines)" % len(out))


def main():
    test_empty_history_says_nothing()
    test_values_on_a_real_history()
    test_thresholds()
    test_corrupt_history_never_raises()
    print("PASS: practice insights")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
