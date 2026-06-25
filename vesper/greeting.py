"""An optional, gentle **spoken greeting by name** at the start of a story.

When the listener has set a name (off by default -- the field starts empty), the
storyteller opens a Sleep session with one soft, time-aware line ("Good evening,
Alex. Let's settle in and unwind.") before the tale begins, spoken by the same
narrator. It is purely a warm settling-in touch: said once per fresh session,
never repeated on a mid-session voice/scene change, and it vanishes the moment
the name is cleared.

The name is the listener's own and stays on this device; it is sanitised to a
short, plain-ASCII first name before it is ever spoken or shown (so it is safe
for the speech engines and the on-screen subtitle). The pure helpers
(`sanitize_name`, `greeting_line`, `prepend`) carry no Qt and are unit-tested;
`ask_name` is the small Save/Clear dialog.
"""
from __future__ import annotations

import unicodedata

_MAX = 24                                  # a first name, not an essay


def sanitize_name(raw):
    """Fold to a short, plain-ASCII name: letters, spaces, hyphen and apostrophe
    only, single-spaced, capped at 24 chars. Returns '' for empty/garbage input,
    which everywhere means 'no greeting'."""
    s = unicodedata.normalize("NFKD", str(raw or ""))
    s = s.encode("ascii", "ignore").decode("ascii")     # drop accents/non-ASCII
    out = []
    for ch in s:
        if ch.isalpha() or ch in " -'":
            out.append(ch)
    s = " ".join("".join(out).split())                  # collapse whitespace
    return s[:_MAX].strip()


def _part_of_day(hour):
    """Map an hour (0-23) to a soft daypart key; None -> a neutral greeting."""
    if hour is None:
        return None
    h = int(hour) % 24
    if 5 <= h < 12:
        return "morning"
    if 12 <= h < 18:
        return "afternoon"
    if 18 <= h < 22:
        return "evening"
    return "night"


_LINES = {
    "morning": "Good morning, {name}. Let's ease gently into the day.",
    "afternoon": "Good afternoon, {name}. Let's take a slow, easy breath together.",
    "evening": "Good evening, {name}. Let's settle in and unwind.",
    "night": "Good night, {name}. Let's settle down softly now, and rest.",
    None: "Hello, {name}. Let's settle in, slow and easy.",
}


def greeting_line(name, hour=None):
    """A single soft greeting for this name and hour, or None when no name is set.
    Time-aware (morning/afternoon/evening/night); always gentle and sleep-safe."""
    name = sanitize_name(name)
    if not name:
        return None
    return _LINES[_part_of_day(hour)].format(name=name)


def greeting_unit(line, pause=1900):
    """Wrap a greeting line in a narrator unit (same shape as a story unit). Its
    own kind 'greeting' means it is shown + spoken but carries no section index."""
    return {"text": line, "pause": int(pause), "phase": None, "kind": "greeting"}


def prepend(line, units):
    """Yield the greeting unit first, then the rest of the story stream. Pure +
    lazy, so it composes with the existing generator without materialising it."""
    yield greeting_unit(line)
    yield from units


def ask_name(win):
    """A tiny 'your name' dialog (Save / Clear / Cancel), prefilled with the
    current name. Saves the sanitised name via win.set_listener_name and returns
    it ('' if cleared, None if cancelled)."""
    from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit,
                                   QPushButton, QVBoxLayout)
    from .widgets import muted

    dlg = QDialog(win)
    dlg.setWindowTitle("Your name")
    if win is not None:
        dlg.setStyleSheet(win.styleSheet())
    dlg.setMinimumWidth(420)
    v = QVBoxLayout(dlg)
    q = QLabel("A gentle greeting by name")
    q.setObjectName("title")
    v.addWidget(q)
    v.addWidget(muted("If you like, the storyteller can greet you softly by name "
                      "when a Sleep session begins. Optional, and it stays on this "
                      "device. Leave it empty for no greeting."))
    field = QLineEdit()
    field.setText(getattr(win, "_listener_name", "") or "")
    field.setPlaceholderText("Your first name (optional)")
    v.addWidget(field)
    result = {"name": None}

    def save():
        result["name"] = win.set_listener_name(field.text())
        dlg.accept()

    def clear():
        result["name"] = win.set_listener_name("")
        dlg.accept()

    field.returnPressed.connect(save)
    row = QHBoxLayout()
    sb = QPushButton("Save")
    sb.setObjectName("accent")
    sb.clicked.connect(save)
    cl = QPushButton("Clear")
    cl.clicked.connect(clear)
    ca = QPushButton("Cancel")
    ca.clicked.connect(dlg.reject)
    row.addWidget(sb)
    row.addWidget(cl)
    row.addWidget(ca)
    v.addLayout(row)
    dlg.exec()
    return result["name"]
