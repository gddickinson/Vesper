"""Global keyboard shortcuts + Zen (focus) mode for the Qt app.

Space play/pause · R reset · F fullscreen · Z Zen · Esc exit fullscreen/Zen.
Zen mode hides the mode bar + control panel, leaving only the breathing face.
"""
from __future__ import annotations

from PySide6.QtGui import QKeySequence, QShortcut

# The real bindings, defined once here so the on-screen cheatsheet can never
# drift from what is actually wired (the first six are bound in bind() below;
# the Ctrl+ ones are the menu accelerators in menus.py).
SHORTCUTS = [
    ("Space", "Play / pause"),
    ("R", "Reset the session"),
    ("V", "Switch face / scene view"),
    ("F", "Fullscreen"),
    ("Z", "Focus (Zen) mode"),
    ("B", "Blackout (near-dark sleep screen)"),
    ("Esc", "Exit fullscreen / Focus / Blackout"),
    ("?", "Show this shortcuts list"),
    ("Ctrl+S", "Save a screenshot"),
    ("Ctrl+Q", "Quit"),
]


def bind(win):
    def sc(key, fn):
        s = QShortcut(QKeySequence(key), win)
        s.activated.connect(fn)
        return s

    sc("Space", win.toggle_transport)
    sc("R", win.reset)
    sc("V", win.toggle_view)
    sc("F", lambda: toggle_fullscreen(win))
    sc("Z", lambda: toggle_zen(win))
    sc("B", lambda: win.toggle_blackout())
    sc("Escape", lambda: exit_overlays(win))
    from . import dialogs                              # "?" -> the shortcuts cheatsheet
    sc("?", lambda: dialogs.open_shortcuts(win))


def toggle_fullscreen(win):
    if win.isFullScreen():
        win.showNormal()
    else:
        win.showFullScreen()


def toggle_zen(win):
    win._zen = not getattr(win, "_zen", False)
    win.panel.setVisible(not win._zen)
    win.menuBar().setVisible(not win._zen)
    win.statusBar().setVisible(not win._zen)


def exit_overlays(win):
    if getattr(win, "_blackout", False):
        win.toggle_blackout(False)
    elif win.isFullScreen():
        win.showNormal()
    elif getattr(win, "_zen", False):
        toggle_zen(win)
