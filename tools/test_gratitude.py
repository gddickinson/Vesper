"""Offline test for the bedtime gratitude / "one good thing" feature.

Covers the pure store helpers (log_gratitude / gratitude_entries /
gratitude_count / gratitude_last_date) and the pure gating predicate
gratitude.should_offer. No Qt window is constructed, so this stays headless and
socket-free; ask_gratitude/maybe_offer_bedtime (which build a QDialog) are
exercised by the offscreen GUI smoke, not here.
"""
import datetime as _dt
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import store  # noqa: E402


def _check_should_offer():
    # should_offer is pure: a plain predicate, no Qt, importable without a display.
    from vesper.gratitude import should_offer
    today = "2026-06-25"
    assert should_offer(True, "", today) is True            # on + never noted
    assert should_offer(True, "2026-06-24", today) is True  # on + last was yesterday
    assert should_offer(True, today, today) is False        # already noted today
    assert should_offer(False, "", today) is False          # off -> never offered
    print("ok: should_offer gates on enabled AND not-yet-today")


def main():
    # empty to start
    assert store.gratitude_entries() == []
    assert store.gratitude_count() == 0
    assert store.gratitude_last_date() == ""
    print("ok: empty history -> no entries, count 0, no last date")

    # blank / whitespace notes are ignored (kindly silent)
    store.log_gratitude("")
    store.log_gratitude("   ")
    assert store.gratitude_count() == 0
    print("ok: blank notes are ignored")

    # a real note lands
    store.log_gratitude("A quiet cup of tea.")
    es = store.gratitude_entries()
    assert len(es) == 1 and es[0]["text"] == "A quiet cup of tea."
    assert store.gratitude_count() == 1
    today = _dt.date.today().isoformat()
    assert store.gratitude_last_date() == today, store.gratitude_last_date()
    assert "t" in es[0] and es[0]["t"][:10] == today      # timestamped
    print(f"ok: one note stored; last date = {store.gratitude_last_date()}")

    # over-long notes are clamped to 280 chars; entries cap at 200
    store.log_gratitude("x" * 500)
    assert len(store.gratitude_entries()[-1]["text"]) == 280
    for i in range(210):
        store.log_gratitude(f"note {i}")
    assert store.gratitude_count() == 200, store.gratitude_count()
    print("ok: notes clamp to 280 chars and history caps at 200 entries")

    # passing an explicit history dict works (used by the Stats dialog)
    h = store.history()
    assert store.gratitude_count(h) == 200
    assert store.gratitude_entries(h) == store.gratitude_entries()
    print("ok: helpers accept an explicit history dict")

    # corrupt 'gratitude' value degrades gracefully (never crashes Stats)
    assert store.gratitude_entries({"gratitude": "oops"}) == []
    assert store.gratitude_count({"gratitude": 7}) == 0
    print("ok: a malformed gratitude value degrades to empty")

    _check_should_offer()

    print("PASS: bedtime gratitude -- store helpers + should_offer gating")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
