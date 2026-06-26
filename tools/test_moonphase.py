"""Offline test for the lunar-phase model (breathsim/moonphase.py).

A pure synodic-month model: from a known new moon, the cycle runs new -> first
quarter -> full -> last quarter every ~29.53 days. This checks the principal
phases land on the right day offsets, illumination tracks the cycle (dark at new,
bright at full), the waxing flag flips at full, and today's phase is always a
valid, sane value. Pure, no Qt, no I/O.
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import moonphase  # noqa: E402

# the reference new moon the model is built on (2000-01-06)
NEW = dt.date(2000, 1, 6)


def _off(days):
    return NEW + dt.timedelta(days=days)


def test_principal_phases():
    # near the reference new moon, then a quarter / half / three-quarters on
    assert moonphase.phase_name(_off(0)) == "New Moon"
    assert moonphase.phase_name(_off(7)) == "First Quarter"
    assert moonphase.phase_name(_off(15)) == "Full Moon"
    assert moonphase.phase_name(_off(22)) == "Last Quarter"
    # the crescents / gibbous fill the gaps between
    assert moonphase.phase_name(_off(3)) == "Waxing Crescent"
    assert moonphase.phase_name(_off(11)) == "Waxing Gibbous"
    assert moonphase.phase_name(_off(19)) == "Waning Gibbous"
    assert moonphase.phase_name(_off(26)) == "Waning Crescent"
    # the cycle wraps back to new after a synodic month
    assert moonphase.phase_name(_off(30)) == "New Moon"
    print("ok: principal phases + crescents land on the right days")


def test_illumination_tracks_the_cycle():
    assert moonphase.illumination(_off(0)) < 0.05         # new: dark
    assert moonphase.illumination(_off(15)) > 0.95        # full: bright
    assert 0.4 < moonphase.illumination(_off(7)) < 0.6    # quarter: half lit
    for d in range(0, 30):
        i = moonphase.illumination(_off(d))
        assert 0.0 <= i <= 1.0
    print("ok: illumination is 0 at new, ~1 at full, always in [0,1]")


def test_waxing_flag():
    assert moonphase.waxing(_off(5)) is True              # growing toward full
    assert moonphase.waxing(_off(20)) is False            # waning toward new
    print("ok: waxing flips at full")


def test_today_is_sane():
    name = moonphase.phase_name()                          # defaults to today
    assert name in moonphase._NAMES, name
    assert 0.0 <= moonphase.phase_fraction() < 1.0
    assert 0.0 <= moonphase.illumination() <= 1.0
    print("ok: today's phase is a valid name (%s)" % name)


def main():
    test_principal_phases()
    test_illumination_tracks_the_cycle()
    test_waxing_flag()
    test_today_is_sane()
    print("PASS: lunar phase model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
