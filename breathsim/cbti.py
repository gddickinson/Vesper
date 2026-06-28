"""CBT-I sleep diary + sleep-window engine -- the desktop mirror of the iOS
``SleepDiary`` + ``CBTI`` modules.

From the last ~7 logged nights it computes Time-In-Bed (TIB), Total Sleep Time
(TST) and Sleep Efficiency (SE = TST/TIB), then prescribes a **sleep-restriction
window** anchored to a fixed wake time, with the standard titration rule
(SE >= 90% -> extend 15 min; <= 85% -> tighten 15 min; else hold). CBT-I is the
first-line treatment for chronic insomnia (NICE 2025, AASM); the sleep diary +
efficiency-driven window are its core. Pure + deterministic; diary persistence
lives in :mod:`breathsim.store` (``log_sleep`` / ``sleep_entries``). Times are
stored as minutes-from-midnight. See the agent memory ``vesper-sleep-science-upgrades``.
"""
from __future__ import annotations

import math

# Stimulus-control + circadian rules -- the behavioural core of CBT-I.
RULES = [
    "Keep the same wake time every day, even after a poor night -- it anchors your body clock.",
    "Use the bed only for sleep. Do your winding-down somewhere else.",
    "Only go to bed when you feel sleepy, not just tired.",
    "If you're awake longer than about 20 minutes, get up, keep the lights low, and return when sleepy.",
    "Don't watch the clock -- turn it away from view.",
    "Get bright light soon after waking; keep the evening dim and warm.",
]

_TIPS = [
    "Caffeine has a ~5-6 hour half-life -- try to finish coffee by early afternoon.",
    "A warm bath or shower 1-2 hours before bed helps your core temperature fall, cueing sleep.",
    "Keep the bedroom cool (around 18C / 65F) -- a falling body temperature deepens sleep.",
    "Alcohol fragments the second half of the night and suppresses REM, even if it helps you doze off.",
    "Morning daylight is the strongest signal that sets tonight's sleep timing.",
    "A consistent wake time matters more for health than the exact hours you sleep.",
    "If you can't sleep, getting up beats lying there frustrated -- it keeps bed a cue for sleep.",
    "Exercise helps you sleep deeper -- but finish vigorous workouts a few hours before bed.",
    "A short to-do list before bed offloads tomorrow's worries and speeds sleep onset.",
]


def tip(day_of_year: int) -> str:
    return _TIPS[(int(day_of_year) - 1) % len(_TIPS)]


# --- per-entry maths (entry = dict of minutes-from-midnight + counts) -------

def _span(a: int, b: int) -> float:
    """Minutes from time-of-day ``a`` to ``b``, wrapping past midnight."""
    iv = (b - a)
    if iv < 0:
        iv += 24 * 60
    return max(0.0, float(iv))


def time_in_bed(e) -> float:
    return _span(int(e.get("in_bed", 0)), int(e.get("out_of_bed", 0)))


def total_sleep(e) -> float:
    return max(0.0, time_in_bed(e) - float(e.get("sol", 0)) - float(e.get("waso", 0)))


def efficiency(e) -> float:
    tib = time_in_bed(e)
    return min(1.0, total_sleep(e) / tib) if tib > 0 else 0.0


def _recent(entries, nights):
    return list(entries or [])[-nights:]


def avg_efficiency(entries, nights=7) -> float:
    r = _recent(entries, nights)
    return sum(efficiency(e) for e in r) / len(r) if r else 0.0


def avg_total_sleep(entries, nights=7) -> float:
    r = _recent(entries, nights)
    return sum(total_sleep(e) for e in r) / len(r) if r else 0.0


# --- the plan --------------------------------------------------------------

def plan(wake_minutes: int, entries=None, nights: int = 7) -> dict:
    """Build the CBT-I sleep-window plan from the diary + the fixed wake time.

    ``entries`` defaults to the persisted diary (``store.sleep_entries()``)."""
    if entries is None:
        from . import store
        entries = store.sleep_entries()
    r = _recent(entries, nights)
    n = len(r)
    eff = avg_efficiency(entries, nights)
    tst = avg_total_sleep(entries, nights)
    eff_pct = int(round(eff * 100))

    window = max(300, min(540, int(round(tst))))           # sleep restriction, 5-9 h
    bed = ((wake_minutes - window) % 1440 + 1440) % 1440

    if n < 3:
        titration = "Log a few nights and your personalised window will appear here."
    elif eff_pct >= 90:
        titration = "Your sleep is efficient -- you can move your earliest bedtime 15 minutes earlier."
    elif eff_pct <= 85:
        titration = "Tighten the window: move your earliest bedtime 15 minutes later to build sleep pressure."
    else:
        titration = "Hold this window for now -- you're on track."

    return {
        "ready": n >= 3, "nights": n, "eff_pct": eff_pct,
        "sleep_mins": int(round(tst)), "window_mins": window,
        "bedtime_minutes": bed, "wake_minutes": wake_minutes,
        "titration": titration,
        "window_str": "%s - %s" % (clock(bed), clock(wake_minutes)),
        "regularity": regularity(entries, nights),
    }


def regularity(entries, nights: int = 7):
    """A 0-100 sleep-regularity score from the consistency of bed + wake times of
    day over recent nights (circular mean-abs-deviation, mapped to 0-100). Sleep
    regularity predicts mortality better than duration (UK Biobank, 2024). ``None``
    if fewer than 3 nights are logged."""
    r = _recent(entries, nights)
    if len(r) < 3:
        return None

    def circ_mad(mins):
        ang = [m / 1440 * 2 * math.pi for m in mins]
        mean = math.atan2(sum(math.sin(a) for a in ang), sum(math.cos(a) for a in ang))
        dev = []
        for a in ang:
            d = a - mean
            while d > math.pi:
                d -= 2 * math.pi
            while d < -math.pi:
                d += 2 * math.pi
            dev.append(abs(d))
        return sum(dev) / len(dev) / (2 * math.pi) * 1440

    mad = (circ_mad([int(e.get("final_wake", 0)) for e in r])
           + circ_mad([int(e.get("in_bed", 0)) for e in r])) / 2
    return int(round(max(0.0, min(100.0, 100 - mad * 1.4))))


def clock(m: int) -> str:
    """minutes-from-midnight -> '11:25 PM'."""
    mm = (int(m) % 1440 + 1440) % 1440
    h24, mn = mm // 60, mm % 60
    ampm = "AM" if h24 < 12 else "PM"
    h12 = h24 % 12 or 12
    return "%d:%02d %s" % (h12, mn, ampm)
