"""Practice streak + a calendar heatmap for the Stats dialog.

Gentle and non-judgemental: a current/best streak phrased kindly, the minutes this
week, and a GitHub-style 13-week grid where each square is a day shaded by how long
you practised (brighter = more). Reads the per-day log in :mod:`breathsim.store`;
shows a friendly empty state until there is data.
"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from breathsim import store

from . import theme

WEEKS = 13


def streak_text(cur, best):
    """A kind one-liner for the current streak (never scolding)."""
    if cur <= 0:
        return "No streak just now - tonight is a lovely time to begin."
    s = "day" if cur == 1 else "days"
    msg = f"{cur} {s} in a row"
    if cur >= 3:
        msg += " - lovely"
    if best > cur:
        msg += f"   (best: {best})"
    return msg


def _qc(hexstr, a=1.0):
    c = QColor(hexstr)
    c.setAlphaF(a)
    return c


class _Heatmap(QWidget):
    def __init__(self, dm, today=None):
        super().__init__()
        self.dm = dm
        self.today = today or dt.date.today()
        self.cell, self.gap = 13, 3
        step = self.cell + self.gap
        self.setFixedSize(WEEKS * step + 2, 7 * step + 2)
        self.peak = max(list(dm.values()) + [1.0])

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), _qc(theme.CARD))
        p.setPen(Qt.PenStyle.NoPen)
        step = self.cell + self.gap
        # oldest column = the Monday (WEEKS-1) weeks before this week's Monday
        first = (self.today - dt.timedelta(days=self.today.weekday())
                 - dt.timedelta(weeks=WEEKS - 1))
        for col in range(WEEKS):
            for row in range(7):
                day = first + dt.timedelta(weeks=col, days=row)
                if day > self.today:
                    continue
                m = self.dm.get(day.isoformat(), 0.0)
                if m > 0:
                    frac = 0.3 + 0.7 * min(1.0, m / self.peak)
                    cc = _qc(theme.blend(theme.CARD, theme.ACCENT, frac))
                else:
                    cc = _qc(theme.blend(theme.CARD, theme.BORDER, 0.7))
                p.setBrush(cc)
                p.drawRoundedRect(
                    QRectF(col * step + 1, row * step + 1, self.cell, self.cell),
                    3, 3)


def build(win=None):
    """A widget with the streak line, this-week minutes and the heatmap (or a
    friendly empty state if there's no practice logged yet)."""
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    dm = store.daily_minutes()
    cur, best = store.streak()
    head = QLabel(streak_text(cur, best))
    head.setObjectName("title")
    v.addWidget(head)
    if dm:
        wk = QLabel(f"This week: {store.week_minutes():.0f} min")
        v.addWidget(wk)
        v.addWidget(_Heatmap(dm))
        legend = QLabel("Last 13 weeks - each square is a day; brighter is more time.")
        legend.setStyleSheet(f"color:{theme.MUTED};")
        v.addWidget(legend)
    else:
        empty = QLabel("Your practice days will appear here as a calendar once "
                       "you have sat for a little while.")
        empty.setWordWrap(True)
        empty.setStyleSheet(f"color:{theme.MUTED};")
        v.addWidget(empty)
    from breathsim import insights                   # gentle, honest summaries
    for line in insights.lines():
        il = QLabel(line)
        il.setWordWrap(True)
        il.setStyleSheet(f"color:{theme.MUTED};")
        v.addWidget(il)
    from . import mood                               # a kind mood-trend line
    mt = mood.summary_text()
    if mt:
        ml = QLabel(mt)
        ml.setWordWrap(True)
        ml.setStyleSheet(f"color:{theme.MUTED};")
        v.addWidget(ml)
    return w
