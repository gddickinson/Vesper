"""A gentle, optional **bedtime gratitude** note -- "one good thing about today".

A brief bedtime gratitude reflection is a gentle way to end the day. This is deliberately tiny and kind: a single soft line you
can type (or skip), kept only on this device, never scored. It is **off by
default**; when on, it is offered once at the start of a Sleep session (and any
time from the Sessions menu). Reuses the mood-check-in pattern; a kind count
appears in Practice Stats.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout)

from breathsim import store

from .widgets import muted


def should_offer(on, last_date, today):
    """Pure: offer the bedtime note only when enabled AND not already done today."""
    return bool(on) and last_date != today


def ask_gratitude(win):
    """A soft 'one good thing' prompt with Keep / Skip. Logs + returns the note,
    or None if skipped/empty."""
    dlg = QDialog(win)
    dlg.setWindowTitle("One good thing")
    if win is not None:
        dlg.setStyleSheet(win.styleSheet())
    dlg.setMinimumWidth(420)
    v = QVBoxLayout(dlg)
    q = QLabel("One good thing about today…")
    q.setObjectName("title")
    v.addWidget(q)
    v.addWidget(muted("A small kindness, a quiet moment, anything at all. It stays "
                      "on this device, just for you. You can skip."))
    field = QLineEdit()
    field.setPlaceholderText("…")
    v.addWidget(field)
    saved = {"t": None}

    def keep():
        t = field.text().strip()
        if t:
            saved["t"] = t
        dlg.accept()

    field.returnPressed.connect(keep)
    row = QHBoxLayout()
    kb = QPushButton("Keep")
    kb.setObjectName("accent")
    kb.clicked.connect(keep)
    sk = QPushButton("Skip")
    sk.clicked.connect(dlg.reject)
    row.addWidget(kb)
    row.addWidget(sk)
    v.addLayout(row)
    dlg.exec()
    if saved["t"]:
        store.log_gratitude(saved["t"])
    return saved["t"]


def maybe_offer_bedtime(win):
    """Offer the note once at the start of a Sleep session, if enabled + not done
    today. Off by default, so it never surprises anyone who hasn't opted in."""
    import datetime as _dt
    if getattr(win, "current_mode", None) != "Sleep":
        return None
    today = _dt.date.today().isoformat()
    if not should_offer(getattr(win, "_gratitude_on", False),
                        store.gratitude_last_date(), today):
        return None
    if getattr(win, "_gratitude_offered", "") == today:    # once per app run too
        return None
    win._gratitude_offered = today
    return ask_gratitude(win)
