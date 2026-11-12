"""First-run welcome / Getting Started overlay.

A gentle, skippable onboarding shown once on first launch (gated on a persisted
``onboarded`` flag) and re-openable any time from Help > Welcome. It is modeless
(uses ``show()``, never a blocking ``exec()``) so it can never trap the user or
hang a headless session; ``maybe_show`` additionally never auto-pops in an
offscreen/headless run, so tests and offline renders stay quiet.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout)

from breathsim import disclaimer, store

from . import theme

# Each step: (title, body). Short, calm, honest about what the app does — no
# wellness claims beyond "a quiet place to breathe".
STEPS = [
    ("Welcome to Vesper",
     "A quiet place to breathe, unwind and drift off to sleep.\n\n"
     "Vesper paces your breath with a softly glowing face, builds all of its "
     "sound from scratch -- breath, voice and nature -- and can read you a slow "
     "bedtime story to fall asleep to. Nothing is downloaded; it all just plays."),
    ("Choose how you want to feel",
     "The mode bar along the top is the main way to steer Vesper. Pick one and "
     "the whole app reshapes around it:\n\n"
     "Meditate  -  paced, resonance breathing\n"
     "Breathwork  -  techniques + a breath-hold timer\n"
     "Chant / Sing  -  voice tools + a live pitch trainer\n"
     "Relax  -  a layered nature soundscape\n"
     "Sleep  -  wind-down, gentle dimming + the storyteller"),
    ("Press play, then settle",
     "Press the play button -- or tap the spacebar -- to begin, and let your "
     "breathing follow the circle: breathe in as it grows, out as it shrinks.\n\n"
     "There is nothing you need to get right. Just follow along gently, and let "
     "the sound carry you."),
    (disclaimer.TITLE, "\n\n".join(disclaimer.POINTS)),
    ("Everything else is in the menus",
     "The menu bar holds every voice, pattern, scene, sound and guided session, "
     "along with your practice stats and the whole story library.\n\n"
     "You can re-open this welcome any time from Help > Welcome.\n\n"
     "Rest well."),
]


def _mark_onboarded(win):
    """Persist the flag without clobbering other settings (save_settings
    overwrites the whole file, so read-modify-write)."""
    try:
        s = store.load_settings()
        s["onboarded"] = True
        store.save_settings(s)
    except Exception:
        pass
    win._onboarded = True


def open_onboarding(win):
    """Build + show the paged welcome (modeless; returns the dialog)."""
    dlg = QDialog(win)
    dlg.setWindowTitle("Welcome to Vesper")
    dlg.setStyleSheet(win.styleSheet() or theme.STYLESHEET)
    dlg.setWindowModality(Qt.WindowModality.WindowModal)
    dlg.setMinimumSize(440, 340)

    v = QVBoxLayout(dlg)
    title = QLabel()
    title.setObjectName("title")
    body = QLabel()
    body.setWordWrap(True)
    body.setAlignment(Qt.AlignmentFlag.AlignTop)
    dots = QLabel()
    dots.setObjectName("muted")
    v.addWidget(title)
    v.addWidget(body, 1)
    v.addWidget(dots)

    state = {"i": 0}
    row = QHBoxLayout()
    skip = QPushButton("Skip")
    back = QPushButton("Back")
    nxt = QPushButton("Next")
    nxt.setObjectName("accent")
    row.addWidget(skip)
    row.addStretch(1)
    row.addWidget(back)
    row.addWidget(nxt)
    v.addLayout(row)

    def render():
        i = state["i"]
        t, b = STEPS[i]
        title.setText(t)
        body.setText(b)
        dots.setText("   ".join("o" if k == i else "." for k in range(len(STEPS))))
        back.setEnabled(i > 0)
        nxt.setText("Begin" if i == len(STEPS) - 1 else "Next")

    def finish():
        _mark_onboarded(win)
        dlg.accept()

    def go(step):
        i = state["i"] + step
        if i >= len(STEPS):
            finish()
            return
        state["i"] = max(0, i)
        render()

    skip.clicked.connect(finish)
    back.clicked.connect(lambda: go(-1))
    nxt.clicked.connect(lambda: go(1))
    dlg.finished.connect(lambda _r: _mark_onboarded(win))   # X / Esc also counts

    render()
    win._onboarding_dlg = dlg            # keep a ref so it isn't garbage-collected
    dlg.show()
    return dlg


def maybe_show(win):
    """Show the welcome once, on first launch only. Never auto-pops in a
    headless/offscreen session (tests, offline renders) so it can't block."""
    try:
        if store.load_settings().get("onboarded"):
            return None
    except Exception:
        return None
    app = QApplication.instance()
    if app is not None and app.platformName() == "offscreen":
        return None
    return open_onboarding(win)
