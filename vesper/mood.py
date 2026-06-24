"""A gentle, optional 1-tap mood check-in (before / after a sit).

A small modal with five calm choices (Tense .. Serene -> 1..5) and a Skip; it
never blocks the breathing and is easy to dismiss. Wired from the window to be
offered, optionally, at the start of a fresh non-Sleep practice and when it ends -
never during Sleep (so it can't wake a drowsy listener). Results go to the
:mod:`breathsim.store` mood log and a kind summary appears in Practice Stats.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout)

from breathsim import store

LABELS = [(1, "Tense"), (2, "Unsettled"), (3, "OK"), (4, "Calm"), (5, "Serene")]


def ask_mood(win, when="after"):
    """Show the picker; return the chosen 1..5, or None if skipped/closed."""
    dlg = QDialog(win)
    dlg.setWindowTitle("How do you feel?")
    if win is not None:
        dlg.setStyleSheet(win.styleSheet())
    v = QVBoxLayout(dlg)
    q = QLabel("How do you feel right now?" if when == "before"
               else "And how do you feel now?")
    q.setObjectName("title")
    v.addWidget(q)
    chosen = {"v": None}
    row = QHBoxLayout()
    for val, name in LABELS:
        b = QPushButton(name)
        b.clicked.connect(lambda _c=False, x=val: (chosen.__setitem__("v", x),
                                                   dlg.accept()))
        row.addWidget(b)
    v.addLayout(row)
    skip = QPushButton("Skip")
    skip.clicked.connect(dlg.reject)
    v.addWidget(skip)
    dlg.exec()
    return chosen["v"]


def maybe_check_in(win, when):
    """Offer a check-in if enabled and not in Sleep mode; log the answer."""
    if not getattr(win, "_mood_on", True):
        return None
    if getattr(win, "current_mode", None) == "Sleep":
        return None                                   # never wake a sleeper
    val = ask_mood(win, when)
    if val:
        store.log_mood(val, when)
    return val


def summary_text():
    """A kind one-line summary for the Stats dialog, or None if no check-ins."""
    n, ab, aa, shift = store.mood_summary()
    if not n:
        return None
    if shift is not None and shift >= 0.2:
        return f"Across {n} check-ins, you usually feel a little calmer afterwards."
    if shift is not None and shift <= -0.2:
        return f"{n} mood check-ins logged - be gentle with yourself."
    return f"{n} mood check-ins logged."
