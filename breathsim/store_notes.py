"""Bedtime self-reflection notes -- gratitude ("one good thing") and worry-parking
(tomorrow's list). Split out of ``store.py`` to keep it under the file-size limit;
both persist into ``history.json`` via store. Re-exported from ``store`` so callers
keep using ``store.log_gratitude`` / ``store.log_worry`` etc.
"""
from __future__ import annotations

import datetime as _dt

from . import store as _store


def _log(key, text, clamp):
    text = (text or "").strip()
    if not text:
        return
    h = _store.history()
    e = {"t": _dt.datetime.now().isoformat(timespec="seconds"), "text": text[:clamp]}
    h[key] = (h.get(key, []) + [e])[-200:]
    _store._write("history.json", h)


def _entries(key, hist):
    h = hist if hist is not None else _store.history()
    es = h.get(key, [])
    return list(es) if isinstance(es, list) else []


def _last_date(key, hist):
    es = _entries(key, hist)
    return es[-1].get("t", "")[:10] if es else ""


# --- gratitude ("one good thing") -----------------------------------------
def log_gratitude(text):
    """Record a short 'one good thing' note (most recent 200 kept). Empty = no-op."""
    _log("gratitude", text, 280)


def gratitude_entries(hist=None):
    return _entries("gratitude", hist)


def gratitude_count(hist=None):
    return len(gratitude_entries(hist))


def gratitude_last_date(hist=None):
    """The date (YYYY-MM-DD) of the most recent note, or '' if none."""
    return _last_date("gratitude", hist)


# --- bedtime worry-parking (tomorrow's list) ------------------------------
def log_worry(text):
    """Record a bedtime 'park your worries' / tomorrow's-list note (most recent
    200 kept). Writing one before bed shortens sleep onset; kept on-device only."""
    _log("worries", text, 1000)


def worry_entries(hist=None):
    return _entries("worries", hist)


def worry_count(hist=None):
    return len(worry_entries(hist))


def worry_last_date(hist=None):
    """The date (YYYY-MM-DD) of the most recent worry note, or '' if none."""
    return _last_date("worries", hist)
