"""Export a small, friendly session summary as text or a themed PNG card.

Mirrors the existing I/O helpers (`app_io.export_wav`, `window.save_screenshot`):
a save dialog, write, then report the path in the status bar; never crash the
app on failure. The summary lines themselves come from the pure
:mod:`breathsim.summary`. It only summarises logged data -- no claims.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QFileDialog

from breathsim import summary

from . import theme


def _last(win):
    """The just-finished/in-progress sit as a dict, or None if too short."""
    mins = win.controller.elapsed() / 60.0
    if mins < 0.5:
        return None
    return {"minutes": mins, "mode": getattr(win, "current_mode", None)}


def write_summary_txt(win, path):
    text = summary.summary_text(_last(win))
    with open(path, "w") as fh:
        fh.write(text + "\n")
    return path


def save_summary_card(win, path):
    """A small themed PNG 'card' of the summary lines (shareable)."""
    lines = summary.summary_lines(_last(win))
    w, h = 600, 360
    pm = QPixmap(w, h)
    pm.fill(QColor(theme.BG))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(QColor(theme.CARD))
    p.setPen(QColor(theme.BORDER))
    p.drawRoundedRect(20, 20, w - 40, h - 40, 16, 16)
    y = 70
    for i, ln in enumerate(lines):
        f = QFont()
        if i == 0:
            p.setPen(QColor(theme.ACCENT))
            f.setPointSize(20)
            f.setBold(True)
        elif i == 1 or ln.startswith("Be well"):
            p.setPen(QColor(theme.MUTED))
            f.setPointSize(12)
        else:
            p.setPen(QColor(theme.TEXT))
            f.setPointSize(14)
        p.setFont(f)
        p.drawText(50, y, ln)
        y += 38
    p.end()
    pm.save(path)
    return path


def export_summary(win):
    path, _ = QFileDialog.getSaveFileName(
        win, "Export Session Summary", "vesper-summary.txt", "Text (*.txt)")
    if not path:
        return
    try:
        write_summary_txt(win, path)
        win.status.showMessage(f"Saved {path}", 4000)
    except Exception as exc:                          # never crash on export
        win.status.showMessage(f"Export failed: {exc}", 5000)


def save_card(win):
    path, _ = QFileDialog.getSaveFileName(
        win, "Save Summary Card", "vesper-summary.png", "PNG (*.png)")
    if not path:
        return
    try:
        save_summary_card(win, path)
        win.status.showMessage(f"Saved {path}", 4000)
    except Exception as exc:
        win.status.showMessage(f"Card failed: {exc}", 5000)
