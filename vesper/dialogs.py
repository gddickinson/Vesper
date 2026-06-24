"""Pop-up dialogs: practice Stats, the per-slot Mixer, the Story Library and About.

All read/write through the MainWindow + the breathsim core (store, story_db,
engine), so they stay thin views. Kept together because each is small.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QTextEdit, QVBoxLayout)

from breathsim import store, story_db

from . import theme
from .widgets import LabeledSlider, muted

_ROLE = Qt.ItemDataRole.UserRole

_MIX_SLOTS = [("primary", "Breath / voice"), ("ambience", "Ambience"),
              ("effects", "Heartbeat / effects")]


def open_stats(win):
    dlg = QDialog(win)
    dlg.setWindowTitle("Practice Stats")
    dlg.setStyleSheet(win.styleSheet())
    v = QVBoxLayout(dlg)
    h = store.history()
    sits = h.get("sits", 0)
    mins = h.get("minutes", 0.0)
    holds = h.get("holds", [])
    title = QLabel("Your practice")
    title.setObjectName("title")
    v.addWidget(title)
    v.addWidget(QLabel(f"Sessions: {sits}"))
    v.addWidget(QLabel(f"Total time: {mins:.0f} min"))
    if holds:
        best = max(x.get("s", 0) for x in holds)
        v.addWidget(QLabel(f"Breath-holds logged: {len(holds)}  (best {best:.0f}s)"))
    else:
        v.addWidget(muted("No breath-holds logged yet."))
    from . import stats_heatmap                      # streak + calendar heatmap
    v.addWidget(stats_heatmap.build(win))
    row = QHBoxLayout()
    clr = QPushButton("Clear history")
    clr.clicked.connect(lambda: (store.clear_history(), dlg.accept()))
    close = QPushButton("Close")
    close.clicked.connect(dlg.accept)
    row.addWidget(clr)
    row.addWidget(close)
    v.addLayout(row)
    dlg.exec()


def open_mixer(win):
    dlg = QDialog(win)
    dlg.setWindowTitle("Mixer")
    dlg.setStyleSheet(win.styleSheet())
    dlg.setMinimumWidth(320)
    v = QVBoxLayout(dlg)
    title = QLabel("Layer mix")
    title.setObjectName("title")
    v.addWidget(title)
    eng = win.engine
    for slot, label in _MIX_SLOTS:
        lvl = eng.slot_levels.get(slot, 0.85)
        s = LabeledSlider(label, 0.0, 1.0, lvl, decimals=2,
                          on_change=lambda val, sl=slot: eng.set_slot_level(sl, val))
        v.addWidget(s)
    close = QPushButton("Close")
    close.clicked.connect(dlg.accept)
    v.addWidget(close)
    dlg.exec()


def open_story_library(win):
    """Browse + search the SQLite record of every lecture and scene."""
    if not (story_db.available() and story_db.ensure()):
        dlg = QDialog(win)
        dlg.setWindowTitle("Story Library")
        dlg.setStyleSheet(win.styleSheet())
        v = QVBoxLayout(dlg)
        t = QLabel("Story Library")
        t.setObjectName("title")
        v.addWidget(t)
        msg = QLabel("The stories database is unavailable — sqlite3 isn't working "
                     "in this Python environment.\n\nThe stories themselves are "
                     "fine; they live in breathsim/lectures_*.py and play normally.")
        msg.setWordWrap(True)
        v.addWidget(msg)
        b = QPushButton("Close")
        b.clicked.connect(dlg.accept)
        v.addWidget(b)
        dlg.exec()
        return
    con = story_db.connect()
    dlg = QDialog(win)
    dlg.setWindowTitle("Story Library")
    dlg.setStyleSheet(win.styleSheet())
    dlg.resize(760, 540)
    v = QVBoxLayout(dlg)
    title = QLabel("Story Library")
    title.setObjectName("title")
    v.addWidget(title)
    s = story_db.stats(con)
    v.addWidget(muted(f"{s['lectures']} lectures · {s['branches']} branches · "
                      f"{s['lines']} lines · {s['words']:,} words · "
                      f"{s['scenes']} scenes"))
    box = QLineEdit()
    box.setPlaceholderText("Search every story…")
    v.addWidget(box)
    body = QHBoxLayout()
    lst = QListWidget()
    lst.setFixedWidth(280)
    txt = QTextEdit()
    txt.setReadOnly(True)
    body.addWidget(lst)
    body.addWidget(txt, 1)
    v.addLayout(body)

    def show_story(name):
        lines = story_db.lines_of(con, name)
        txt.setPlainText(name + "\n\n" + "\n\n".join(lines))

    def fill_all():
        lst.clear()
        for cat in story_db.categories(con):
            for r in story_db.lectures_in(con, cat):
                it = QListWidgetItem(f"  {r['name']}")
                it.setData(_ROLE, r["name"])
                lst.addItem(it)

    def on_pick(item):
        if item and item.data(_ROLE):
            show_story(item.data(_ROLE))

    def on_search(term):
        lst.clear()
        term = term.strip()
        if not term:
            fill_all()
            return
        for r in story_db.search(con, term):
            it = QListWidgetItem(f"{r['story']}: {r['text'][:46]}…")
            it.setData(_ROLE, r["story"])
            lst.addItem(it)

    lst.currentItemChanged.connect(lambda cur, _prev: on_pick(cur))
    box.textChanged.connect(on_search)
    fill_all()
    close = QPushButton("Close")
    close.clicked.connect(dlg.accept)
    v.addWidget(close)
    dlg.exec()
    con.close()


def open_shortcuts(win):
    """A calm cheatsheet of the real keyboard shortcuts. Modeless (show(), never
    a blocking exec) so '?' and tests never trap or hang."""
    from . import shortcuts
    dlg = QDialog(win)
    dlg.setWindowTitle("Keyboard Shortcuts")
    dlg.setStyleSheet(win.styleSheet() or theme.STYLESHEET)
    dlg.setWindowModality(Qt.WindowModality.WindowModal)
    v = QVBoxLayout(dlg)
    t = QLabel("Keyboard shortcuts")
    t.setObjectName("title")
    v.addWidget(t)
    grid = QGridLayout()
    grid.setHorizontalSpacing(18)
    for i, (key, desc) in enumerate(shortcuts.SHORTCUTS):
        k = QLabel(key)
        k.setStyleSheet(f"color:{theme.ACCENT}; font-weight:600;")
        grid.addWidget(k, i, 0)
        grid.addWidget(QLabel(desc), i, 1)
    v.addLayout(grid)
    b = QPushButton("Close")
    b.clicked.connect(dlg.accept)
    v.addWidget(b)
    win._shortcuts_dlg = dlg                          # keep a ref so it isn't GC'd
    dlg.show()
    return dlg


def open_about(win):
    dlg = QDialog(win)
    dlg.setWindowTitle("About")
    dlg.setStyleSheet(win.styleSheet())
    v = QVBoxLayout(dlg)
    t = QLabel("Vesper")
    t.setObjectName("title")
    v.addWidget(t)
    body = QLabel(
        "A meditation / breathing pacer with a 3D talking-head Claude avatar that "
        "breathes and lip-syncs a procedural bedtime story.\n\n"
        "Audio, breath and voice logic are the shared breathsim core; this is the "
        "Qt front-end.")
    body.setWordWrap(True)
    v.addWidget(body)
    close = QPushButton("Close")
    close.clicked.connect(dlg.accept)
    v.addWidget(close)
    dlg.exec()
