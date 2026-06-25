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


# --- AI-generated stories (saved to the library) ---------------------------

def ai_stories_list():
    return _read("ai_stories.json", [])


def save_ai_story(d):
    data = [s for s in ai_stories_list() if s.get("name") != d.get("name")]
    data.append(d)
    _write("ai_stories.json", data)


def delete_ai_story(name):
    _write("ai_stories.json",
           [s for s in ai_stories_list() if s.get("name") != name])


def ai_mantras_list():
    return _read("ai_mantras.json", [])


def save_ai_mantra(d):
    data = [m for m in ai_mantras_list() if m.get("name") != d.get("name")]
    data.append(d)
    _write("ai_mantras.json", data)


def delete_ai_mantra(name):
    _write("ai_mantras.json",
           [m for m in ai_mantras_list() if m.get("name") != name])


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
    """Merge *d* into the saved settings (read-modify-write), so a partial patch
    (e.g. just ``{"last_scene": ...}``) never clobbers the other keys."""
    cur = load_settings()
    cur.update(d or {})
    _write("settings.json", cur)


# --- practice history (gentle progress + breath-hold log) ------------------

_HIST_DEFAULT = {"sits": 0, "minutes": 0.0, "holds": [], "days": {}, "moods": [],
                 "hours": {}, "bpm": []}


def history():
    h = _read("history.json", {})
    if not isinstance(h, dict):                     # a corrupted file -> safe default
        h = {}
    return {**_HIST_DEFAULT, **h}


def log_session(minutes: float, bpm=None):
    h = history()
    mins = max(0.0, float(minutes))
    h["sits"] += 1
    h["minutes"] = round(h["minutes"] + mins, 1)
    now = _dt.datetime.now()
    day = now.date().isoformat()                    # per-day log for streaks/heatmap
    d = dict(h.get("days", {}))
    cur = d.get(day, {"min": 0.0, "sits": 0})
    d[day] = {"min": round(cur["min"] + mins, 1), "sits": cur["sits"] + 1}
    h["days"] = d
    hours = dict(h.get("hours", {}))               # hour-of-day histogram (added later)
    hr = str(now.hour)
    hours[hr] = int(hours.get(hr, 0)) + 1
    h["hours"] = hours
    if bpm and float(bpm) > 0:                      # breaths/min (added later; optional)
        h["bpm"] = (list(h.get("bpm", [])) + [round(float(bpm), 2)])[-200:]
    _write("history.json", h)


# --- streaks / heatmap (gentle, computed from the per-day log) --------------

def _valid_day(key):
    """True if *key* is a parseable ISO date. Guards against corrupted/legacy
    history files whose ``days`` map holds a junk key (which would otherwise
    crash streak / week computations downstream)."""
    try:
        _dt.date.fromisoformat(str(key))
        return True
    except (ValueError, TypeError):
        return False


def daily_minutes(hist=None):
    """{ 'YYYY-MM-DD': minutes } from the per-day practice log (pure / testable).

    Only well-formed ISO date keys mapping to a dict-like value are included, so
    a damaged history file degrades gracefully instead of crashing the Stats
    view, streaks, or the insight lines built on top of this."""
    h = hist if hist is not None else history()
    days = h.get("days", {})
    if not isinstance(days, dict):
        return {}
    out = {}
    for d, v in days.items():
        if not _valid_day(d) or not isinstance(v, dict):
            continue
        try:
            out[d] = float(v.get("min", 0.0))
        except (TypeError, ValueError):
            continue
    return out


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


# --- mood check-ins (optional, gentle) -------------------------------------

def log_mood(value, when="after"):
    """Record a 1..5 mood, ``when`` = 'before' | 'after'. Keeps the most recent 200."""
    h = history()
    e = {"t": _dt.datetime.now().isoformat(timespec="seconds"),
         "v": max(1, min(5, int(value))), "when": when}
    h["moods"] = (h.get("moods", []) + [e])[-200:]
    _write("history.json", h)


def mood_entries(hist=None):
    h = hist if hist is not None else history()
    return list(h.get("moods", []))


def mood_summary(hist=None):
    """(count, avg_before, avg_after, avg_shift) over logged moods (pure)."""
    es = mood_entries(hist)
    bef = [e["v"] for e in es if e.get("when") == "before"]
    aft = [e["v"] for e in es if e.get("when") == "after"]
    avg = lambda xs: round(sum(xs) / len(xs), 2) if xs else None
    ab, aa = avg(bef), avg(aft)
    shift = round(aa - ab, 2) if (ab is not None and aa is not None) else None
    return (len(es), ab, aa, shift)


# --- bedtime self-reflection notes (gratitude + worry-parking) -------------
# Split into store_notes.py to stay under the file-size limit; re-exported here
# so callers keep using store.log_gratitude / store.log_worry etc.
from .store_notes import (gratitude_count, gratitude_entries,  # noqa: E402,F401
                          gratitude_last_date, log_gratitude, log_worry,
                          worry_count, worry_entries, worry_last_date)


def log_hold(seconds: float, label: str = ""):
    """Record one breath-hold (retention) time; keeps the most recent 50."""
    h = history()
    h["holds"] = (h["holds"] + [{"s": round(float(seconds), 1), "label": label}])[-50:]
    _write("history.json", h)


def clear_history():
    _write("history.json", dict(_HIST_DEFAULT))


# --- multi-night courses (gentle per-course progress) ----------------------

def course_state():
    """{ course_name: {'day': next-0-based-index, 'done': [iso...], 'completed': bool} }."""
    d = _read("courses.json", {})
    return d if isinstance(d, dict) else {}


def course_day(name):
    """The 0-based index of the next day to do for *name* (0 if unstarted)."""
    return int(course_state().get(name, {}).get("day", 0))


def advance_course(name, total):
    """Mark today's day done and step to the next (capped at *total*). Called only
    when a session actually completes, so progress is honest. Returns the new day."""
    st = course_state()
    e = dict(st.get(name, {"day": 0, "done": []}))
    e["day"] = min(int(e.get("day", 0)) + 1, int(total))
    e["done"] = (list(e.get("done", [])) + [_dt.date.today().isoformat()])[-90:]
    e["completed"] = e["day"] >= int(total)
    st[name] = e
    _write("courses.json", st)
    return e["day"]


def reset_course(name):
    st = course_state()
    st.pop(name, None)
    _write("courses.json", st)


# --- favourite voices (quick-access stars) ----------------------------------

def favourites():
    """The starred voice names, de-duplicated, order preserved."""
    out = []
    for f in _read("favourites.json", []):
        if isinstance(f, str) and f not in out:
            out.append(f)
    return out


def is_favourite(name):
    return name in favourites()


def toggle_favourite(name):
    """Star/unstar a voice name; returns the new favourites list. No-op on empty."""
    if not name:
        return favourites()
    favs = favourites()
    favs = [f for f in favs if f != name] if name in favs else favs + [name]
    _write("favourites.json", favs)
    return favs


# --- recent "tonight's pick" lectures (avoid repeating two nights running) ---

def recent_picks():
    return [x for x in _read("recent_picks.json", []) if isinstance(x, str)]


def push_recent_pick(name, keep=5):
    """Record *name* as just-picked (most recent last); keeps the last *keep*."""
    if not name:
        return recent_picks()
    rp = [x for x in recent_picks() if x != name] + [name]
    rp = rp[-int(keep):]
    _write("recent_picks.json", rp)
    return rp


# --- saved soundscapes (a light sound-only mix: ambience/effect/levels/flags) -

def soundscapes():
    d = _read("soundscapes.json", {})
    return d if isinstance(d, dict) else {}


def soundscape_names():
    return list(soundscapes().keys())


def save_soundscape(name, mix):
    if not name:
        return soundscapes()
    d = soundscapes()
    d[name] = dict(mix)
    _write("soundscapes.json", d)
    return d


def get_soundscape(name):
    return soundscapes().get(name)


def delete_soundscape(name):
    d = soundscapes()
    d.pop(name, None)
    _write("soundscapes.json", d)
    return d


# --- per-lecture resume (roughly where a long lecture left off) -------------

def lecture_progress():
    d = _read("lecture_progress.json", {})
    return d if isinstance(d, dict) else {}


def get_lecture_progress(name):
    e = lecture_progress().get(name, {})
    return e if isinstance(e, dict) else {}


def set_lecture_progress(name, section):
    if not name:
        return lecture_progress()
    d = lecture_progress()
    d[name] = {"section": int(section),
               "t": _dt.date.today().isoformat()}
    _write("lecture_progress.json", d)
    return d


def clear_lecture_progress(name):
    d = lecture_progress()
    d.pop(name, None)
    _write("lecture_progress.json", d)


# --- per-mode remembered voice / ambience ----------------------------------

def mode_prefs():
    d = _read("mode_prefs.json", {})
    return d if isinstance(d, dict) else {}


def get_mode_pref(mode):
    p = mode_prefs().get(mode, {})
    return p if isinstance(p, dict) else {}


def set_mode_pref(mode, key, value):
    """Remember *key* (e.g. 'voice'/'ambience') for *mode*; returns all prefs."""
    if not mode:
        return mode_prefs()
    d = mode_prefs()
    e = dict(d.get(mode, {}) if isinstance(d.get(mode), dict) else {})
    e[key] = value
    d[mode] = e
    _write("mode_prefs.json", d)
    return d


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
    try:                                      # saved AI-generated stories (opt-in)
        from . import llm_story
        llm_story.register_saved()
    except Exception as exc:
        print(f"[breathsim] could not load saved AI stories: {exc}")
