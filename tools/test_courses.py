"""Offline test for the multi-night courses (courses.py).

A course is a short sequence of guided days; `apply_day` runs one day's program
or mode through the normal session machinery. The saved position can drift out of
range -- a finished course, or a corrupt/legacy `courses.json` with a negative or
oversized day -- so `apply_day` must clamp to a real day rather than IndexError
mid-sit. This checks the shipped courses are well formed, that day_label reads
right, that program- vs mode-days dispatch and announce their intention, and that
a bad index (negative / past the end / empty / None course) degrades safely.
Pure, no Qt.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import courses  # noqa: E402


class _Speech:
    def __init__(self):
        self.announced = []

    def announce(self, text):
        self.announced.append(text)


class _FakeApp:
    """Records what apply_day asks the app to do, without any Qt."""

    def __init__(self):
        self.speech = _Speech()
        self.programs = []
        self.modes = []
        self.ensured = 0

    def start_session_mode(self, name):
        self.programs.append(name)

    def apply_mode(self, name):
        self.modes.append(name)

    def _ensure_running(self):
        self.ensured += 1


def test_shipped_courses_well_formed():
    assert courses.names(), "no courses registered"
    for name in courses.names():
        c = courses.get(name)
        assert c is not None and c.total == len(c.days) >= 1, name
        assert isinstance(c.unit, str) and c.unit, name
        for d in c.days:
            assert isinstance(d.intention, str) and d.intention.strip(), name
            # a day points at a program OR a mode (or is intention-only, allowed)
            assert (d.program is None) or isinstance(d.program, str)
            assert (d.mode is None) or isinstance(d.mode, str)
    assert courses.get("no such course") is None
    print("ok: %d courses well formed" % len(courses.names()))


def test_day_label():
    c = courses.get(courses.names()[0])
    assert courses.day_label(c, 0) == "%s 1 of %d" % (c.unit, c.total)
    assert courses.day_label(c, c.total - 1).endswith("of %d" % c.total)
    print("ok: day_label reads '<unit> N of total'")


def test_apply_day_dispatch():
    c = courses.Course("T", "d", "Night", [
        courses.Day("rest now", program="Yoga Nidra (12 min)"),
        courses.Day("just sleep", mode="Sleep"),
    ])
    app = _FakeApp()
    courses.apply_day(app, c, 0)
    assert app.programs == ["Yoga Nidra (12 min)"], app.programs
    assert app.speech.announced == ["rest now"], app.speech.announced
    assert app.modes == [] and app.ensured == 0
    courses.apply_day(app, c, 1)
    assert app.modes == ["Sleep"] and app.ensured == 1, (app.modes, app.ensured)
    print("ok: program-days and mode-days dispatch + announce")


def test_apply_day_clamps_a_bad_index():
    c = courses.Course("T", "d", "Night", [
        courses.Day("first", mode="A"), courses.Day("last", mode="Z"),
    ])
    # a negative saved day -> first day, never an IndexError or wrap-around
    app = _FakeApp()
    courses.apply_day(app, c, -5)
    assert app.modes == ["A"], app.modes
    # past the end (a finished course) -> the last day
    app = _FakeApp()
    courses.apply_day(app, c, 99)
    assert app.modes == ["Z"], app.modes
    # an empty course, or no course at all, is a quiet no-op
    app = _FakeApp()
    courses.apply_day(app, courses.Course("E", "d", "Night", []), 0)
    courses.apply_day(app, None, 0)
    assert app.modes == [] and app.programs == []
    print("ok: a negative / past-end / empty index degrades safely")


def test_every_shipped_day_applies():
    """Smoke: every real day of every course applies without raising, for any
    index including out-of-range ones."""
    for name in courses.names():
        c = courses.get(name)
        for idx in (-3, 0, c.total // 2, c.total - 1, c.total, c.total + 50):
            app = _FakeApp()
            courses.apply_day(app, c, idx)        # must not raise
            assert (app.programs or app.modes), (name, idx)
    print("ok: every shipped day applies at any index without crashing")


def main():
    test_shipped_courses_well_formed()
    test_day_label()
    test_apply_day_dispatch()
    test_apply_day_clamps_a_bad_index()
    test_every_shipped_day_applies()
    print("PASS: multi-night courses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
