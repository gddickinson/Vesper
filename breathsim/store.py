"""User persistence: custom patterns, voices, presets and settings (JSON).

Files live in ``~/.breathsim`` (override with ``$BREATHSIM_HOME``). Custom
patterns and voices are merged into the live registries by :func:`register_all`
at startup, so they appear in every menu and dropdown.
"""
from __future__ import annotations

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

_HIST_DEFAULT = {"sits": 0, "minutes": 0.0, "holds": []}


def history():
    h = _read("history.json", {})
    return {**_HIST_DEFAULT, **h}


def log_session(minutes: float):
    h = history()
    h["sits"] += 1
    h["minutes"] = round(h["minutes"] + max(0.0, float(minutes)), 1)
    _write("history.json", h)


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
