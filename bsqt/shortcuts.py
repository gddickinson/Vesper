"""Global keyboard shortcuts + Zen (focus) mode for the Qt app.

Space play/pause · R reset · F fullscreen · Z Zen · Esc exit fullscreen/Zen.
Zen mode hides the mode bar + control panel, leaving only the breathing face.
"""
from __future__ import annotations

from PySide6.QtGui import QKeySequence, QShortcut


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
    sc("Escape", lambda: exit_overlays(win))


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
    if win.isFullScreen():
        win.showNormal()
    elif getattr(win, "_zen", False):
        toggle_zen(win)
