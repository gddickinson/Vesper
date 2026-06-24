"""User persistence: custom patterns, voices, presets and settings (JSON).

Files live in ``~/.breathsim`` (override with ``$BREATHSIM_HOME``). Custom
patterns and voices are merged into the live registries by :func:`register_all`
at startup, so they appear in every menu and dropdown.
"""
from __future__ import annotations

import datetime as _dt
import json
import os

from . import patterns, voices
from .patterns import BreathPattern

DIR = os.environ.get("BREATHSIM_HOME") or os.path.expanduser("~/.breathsim")


def _path(name):
    return os.path.join(DIR, name)


def _read(name, default):
    try:
        with open(_path(name)) as fh:
            return json.load(fh)
    except Exception:
        return default


def _write(name, data) -> bool:
    try:
        os.makedirs(DIR, exist_ok=True)
        with open(_path(name), "w") as fh:
            json.dump(data, fh, indent=2)
        return True
    except Exception as exc:
        print(f"[breathsim] could not save {name}: {exc}")
        return False


def _pattern_from(d):
    return BreathPattern(d["name"], d["inhale"], d["hold_full"], d["exhale"],
                         d["hold_empty"], d.get("description", "Custom pattern."))


# --- patterns --------------------------------------------------------------

def patterns_list():
    return _read("patterns.json", [])


def save_pattern(d):
    data = [p for p in patterns_list() if p.get("name") != d["name"]]
    data.append(d)
    _write("patterns.json", data)
    patterns.add_pattern(_pattern_from(d))


def delete_pattern(name):
    _write("patterns.json",
           [p for p in patterns_list() if p.get("name") != name])


# --- voices ----------------------------------------------------------------

def voices_list():
    return _read("voices.json", [])


def save_voice(d):
    data = [v for v in voices_list() if v.get("name") != d["name"]]
    data.append(d)
    _write("voices.json", data)
    voices.register_from_dict(d)


def delete_voice(name):
    _write("voices.json", [v for v in voices_list() if v.get("name") != name])


# --- presets ---------------------------------------------------------------

def presets_list():
    return _read("presets.json", [])


def save_preset(d):
    data = [p for p in presets_list() if p.get("name") != d["name"]]
    data.append(d)
    _write("presets.json", data)


def delete_preset(name):
    _write("presets.json", [p for p in presets_list() if p.get("name") != name])


def preset_by_name(name):
    for p in presets_list():
        if p.get("name") == name:
            return p
    return None


# --- settings --------------------------------------------------------------

def load_settings():
    return _read("settings.json", {})


def save_settings(d):
    _write("settings.json", d)


# --- practice history (gentle progress + breath-hold log) ------------------

_HIST_DEFAULT = {"sits": 0, "minutes": 0.0, "holds": [], "days": {}}


def history():
    h = _read("history.json", {})
    return {**_HIST_DEFAULT, **h}


def log_session(minutes: float):
    h = history()
    mins = max(0.0, float(minutes))
    h["sits"] += 1
    h["minutes"] = round(h["minutes"] + mins, 1)
    day = _dt.date.today().isoformat()             # per-day log for streaks/heatmap
    d = dict(h.get("days", {}))
    cur = d.get(day, {"min": 0.0, "sits": 0})
    d[day] = {"min": round(cur["min"] + mins, 1), "sits": cur["sits"] + 1}
    h["days"] = d
    _write("history.json", h)


# --- streaks / heatmap (gentle, computed from the per-day log) --------------

def daily_minutes(hist=None):
    """{ 'YYYY-MM-DD': minutes } from the per-day practice log (pure / testable)."""
    h = hist if hist is not None else history()
    return {d: float(v.get("min", 0.0)) for d, v in h.get("days", {}).items()}


def streak(hist=None, today=None):
    """(current, best) run of consecutive days with any practice. Today not yet
    practised does not break the current streak. Pure; pass *today* to test."""
    practised = {d for d, m in daily_minutes(hist).items() if m > 0}
    if not practised:
        return (0, 0)
    today = today or _dt.date.today()
    d = today
    if d.isoformat() not in practised:             # today still open - look back
        d = d - _dt.timedelta(days=1)
    cur = 0
    while d.isoformat() in practised:
        cur += 1
        d -= _dt.timedelta(days=1)
    dates = sorted(_dt.date.fromisoformat(x) for x in practised)
    best = run = 1
    for i in range(1, len(dates)):
        run = run + 1 if (dates[i] - dates[i - 1]).days == 1 else 1
        best = max(best, run)
    return (cur, best)


def week_minutes(hist=None, today=None):
    """Minutes practised over the last 7 days (today included)."""
    dm = daily_minutes(hist)
    today = today or _dt.date.today()
    start = today - _dt.timedelta(days=6)
    return round(sum(m for d, m in dm.items()
                     if start <= _dt.date.fromisoformat(d) <= today), 1)


def log_hold(seconds: float, label: str = ""):
    """Record one breath-hold (retention) time; keeps the most recent 50."""
    h = history()
    h["holds"] = (h["holds"] + [{"s": round(float(seconds), 1), "label": label}])[-50:]
    _write("history.json", h)


def clear_history():
    _write("history.json", dict(_HIST_DEFAULT))


def register_all():
    """Merge saved custom patterns and voices into the live registries."""
    for d in patterns_list():
        try:
            patterns.add_pattern(_pattern_from(d))
        except Exception as exc:
            print(f"[breathsim] bad saved pattern: {exc}")
    for d in voices_list():
        try:
            voices.register_from_dict(d)
        except Exception as exc:
            print(f"[breathsim] bad saved voice: {exc}")
