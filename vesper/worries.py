"""A gentle, optional **bedtime "park your worries"** note -- a tomorrow's-list.

The idea (explored by Scullin et al., 2018): writing a short to-do / worry list
just before bed sets tomorrow's concerns down on paper, so the mind can stop
rehearsing them. This is a small, kind
brain-dump: jot whatever is on your mind for tomorrow (or skip), kept only on
this device, never scored. It is **off by default**; when on, it is offered once
at the start of a Sleep session (and any time from the Sessions menu). Mirrors
the gratitude plumbing; a count appears in Practice Stats. Distinct in purpose
from gratitude (set worries down vs. savour the good).
"""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QVBoxLayout)

from breathsim import store

from .widgets import muted


def should_offer(on, last_date, today):
    """Pure: offer the note only when enabled AND not already done today."""
    return bool(on) and last_date != today


def ask_worries(win):
    """A soft 'park your worries' prompt with Keep / Skip. Logs + returns the
    note text, or None if skipped/empty."""
    dlg = QDialog(win)
    dlg.setWindowTitle("Park your worries")
    if win is not None:
        dlg.setStyleSheet(win.styleSheet())
    dlg.setMinimumWidth(460)
    v = QVBoxLayout(dlg)
    q = QLabel("Anything on your mind for tomorrow?")
    q.setObjectName("title")
    v.addWidget(q)
    v.addWidget(muted("Set it down here - a worry, a to-do, anything you don't "
                      "want to carry into sleep - so your mind can let it go for "
                      "tonight. It stays on this device. You can skip."))
    field = QPlainTextEdit()
    field.setPlaceholderText("Tomorrow I want to...")
    field.setMinimumHeight(120)
    v.addWidget(field)
    saved = {"t": None}

    def keep():
        t = field.toPlainText().strip()
        if t:
            saved["t"] = t
        dlg.accept()

    row = QHBoxLayout()
    kb = QPushButton("Set it down")
    kb.setObjectName("accent")
    kb.clicked.connect(keep)
    sk = QPushButton("Skip")
    sk.clicked.connect(dlg.reject)
    row.addWidget(kb)
    row.addWidget(sk)
    v.addLayout(row)
    dlg.exec()
    if saved["t"]:
        store.log_worry(saved["t"])
    return saved["t"]


def maybe_offer_bedtime(win):
    """Offer the note once at the start of a Sleep session, if enabled + not done
    today. Off by default, so it never surprises anyone who hasn't opted in."""
    import datetime as _dt
    if getattr(win, "current_mode", None) != "Sleep":
        return None
    today = _dt.date.today().isoformat()
    if not should_offer(getattr(win, "_worry_on", False),
                        store.worry_last_date(), today):
        return None
    if getattr(win, "_worry_offered", "") == today:        # once per app run too
        return None
    win._worry_offered = today
    return ask_worries(win)
