"""Offline test for the bedtime 'park your worries' / tomorrow's-list offload.

Covers the pure store helpers (log_worry / worry_entries / worry_count /
worry_last_date) and the pure gate worries.should_offer. Headless: ask_worries /
maybe_offer_bedtime (which build a QDialog) are exercised by the offscreen GUI
smoke, not here.
"""
import datetime as _dt
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import store  # noqa: E402


def _check_should_offer():
    from vesper.worries import should_offer
    today = "2026-06-25"
    assert should_offer(True, "", today) is True
    assert should_offer(True, "2026-06-24", today) is True
    assert should_offer(True, today, today) is False
    assert should_offer(False, "", today) is False
    print("ok: should_offer gates on enabled AND not-yet-today")


def main():
    assert store.worry_entries() == [] and store.worry_count() == 0
    assert store.worry_last_date() == ""
    print("ok: empty history -> no entries, count 0, no last date")

    store.log_worry("")
    store.log_worry("   ")
    assert store.worry_count() == 0
    print("ok: blank notes are ignored")

    store.log_worry("Call the dentist.\nFinish the report.")
    es = store.worry_entries()
    assert len(es) == 1 and "dentist" in es[0]["text"]
    today = _dt.date.today().isoformat()
    assert store.worry_last_date() == today, store.worry_last_date()
    assert es[0]["t"][:10] == today
    print(f"ok: a multi-line worry note stored; last date = {store.worry_last_date()}")

    # over-long notes clamp to 1000 chars; history caps at 200
    store.log_worry("x" * 2000)
    assert len(store.worry_entries()[-1]["text"]) == 1000
    for i in range(210):
        store.log_worry(f"note {i}")
    assert store.worry_count() == 200, store.worry_count()
    print("ok: notes clamp to 1000 chars and history caps at 200 entries")

    # explicit history dict + malformed value degrade gracefully
    h = store.history()
    assert store.worry_count(h) == 200
    assert store.worry_entries({"worries": "oops"}) == []
    assert store.worry_count({"worries": 7}) == 0
    print("ok: helpers accept a history dict; malformed value -> empty")

    # gratitude and worries are independent keys
    store.log_gratitude("a good thing")
    assert store.gratitude_count() == 1 and store.worry_count() == 200
    print("ok: gratitude and worries are stored independently")

    _check_should_offer()
    print("PASS: bedtime worry-parking -- store helpers + should_offer gating")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
