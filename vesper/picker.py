"""A searchable, grouped **picker popup** + a button that opens it.

Long combo-boxes are poor UX: the bedtime-story list holds 200+ lectures across
46 branches, the breath-voice list 148 voices, the narration list ~50. This
replaces them with a friendlier chooser -- a dialog with a **search box** and a
**grouped, filterable list** (type to filter, Enter or double-click to pick).
`choose()` returns the picked value (or None); `PickerButton` shows the current
choice on its face and opens the dialog. Short selectors keep their combos.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLineEdit, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout)

_VALUE = Qt.ItemDataRole.UserRole


def _norm(groups, label_fn):
    """Normalise groups to ``[(header, [(value, label), ...]), ...]``. Each item
    may be a bare value (label = label_fn(value)) or a (value, label) tuple."""
    out = []
    for header, items in groups:
        norm = []
        for it in items:
            v, lab = it if isinstance(it, tuple) else (it, label_fn(it))
            norm.append((v, str(lab)))
        out.append((header, norm))
    return out


def _first_visible_leaf(tree):
    for i in range(tree.topLevelItemCount()):
        grp = tree.topLevelItem(i)
        if grp.isHidden():
            continue
        for j in range(grp.childCount()):
            it = grp.child(j)
            if not it.isHidden():
                return it
    return None


def choose(parent, title, groups, current=None, label_fn=str,
           placeholder="Type to search..."):
    """Open the picker; return the chosen value or None. ``groups`` is an ordered
    ``[(header, [value | (value, label), ...]), ...]``."""
    groups = _norm(groups, label_fn)
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    if parent is not None:
        dlg.setStyleSheet(parent.styleSheet())
    dlg.setMinimumSize(440, 560)
    v = QVBoxLayout(dlg)
    search = QLineEdit()
    search.setPlaceholderText(placeholder)
    search.setClearButtonEnabled(True)
    v.addWidget(search)
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.setIndentation(12)
    v.addWidget(tree, 1)

    cur_item = None
    for header, items in groups:
        if not items:
            continue
        grp = QTreeWidgetItem(tree, [str(header)])
        grp.setFlags(Qt.ItemFlag.ItemIsEnabled)        # header: shown, not selectable
        f = grp.font(0)
        f.setBold(True)
        grp.setFont(0, f)
        grp.setExpanded(True)
        for value, label in items:
            it = QTreeWidgetItem(grp, [label])
            it.setData(0, _VALUE, value)
            if current is not None and value == current:
                cur_item = it
    if cur_item is not None:
        tree.setCurrentItem(cur_item)
        tree.scrollToItem(cur_item)

    def filter_(txt):
        txt = txt.strip().lower()
        for i in range(tree.topLevelItemCount()):
            grp = tree.topLevelItem(i)
            any_vis = False
            for j in range(grp.childCount()):
                it = grp.child(j)
                vis = (not txt) or (txt in it.text(0).lower())
                it.setHidden(not vis)
                any_vis = any_vis or vis
            grp.setHidden(not any_vis)

    search.textChanged.connect(filter_)

    picked = {"v": None}

    def accept(it):
        if it is not None and it.data(0, _VALUE) is not None:
            picked["v"] = it.data(0, _VALUE)
            dlg.accept()

    tree.itemDoubleClicked.connect(lambda it, _c: accept(it))
    search.returnPressed.connect(lambda: accept(
        tree.currentItem() if (tree.currentItem() and not tree.currentItem().isHidden()
                               and tree.currentItem().data(0, _VALUE) is not None)
        else _first_visible_leaf(tree)))

    row = QHBoxLayout()
    ok = QPushButton("Choose")
    ok.setObjectName("accent")
    ok.clicked.connect(lambda: accept(tree.currentItem()))
    cancel = QPushButton("Cancel")
    cancel.clicked.connect(dlg.reject)
    row.addWidget(ok)
    row.addWidget(cancel)
    v.addLayout(row)
    search.setFocus()
    dlg.exec()
    return picked["v"]


class PickerButton(QPushButton):
    """A button that shows the current choice and opens the searchable picker.

    Duck-types the slice of QComboBox that ``control_panel`` sync uses
    (`current_value`/`set_value`/`is_open`), so live state-push keeps it in sync.
    """

    def __init__(self, current, groups_fn, on_pick, *, title="Choose",
                 label_fn=str, prefix="", win=None, empty="Choose..."):
        super().__init__()
        self._groups_fn = groups_fn        # () -> groups
        self._on_pick = on_pick
        self._label_fn = label_fn
        self._title = title
        self._prefix = prefix
        self._win = win
        self._empty = empty
        self._value = None
        self._open = False
        self.setToolTip("Click to search and choose")
        self.set_value(current)
        self.clicked.connect(self._open_dialog)

    def current_value(self):
        return self._value

    def is_open(self):
        return self._open

    def set_value(self, value):
        self._value = value
        lab = self._label_fn(value) if value not in (None, "") else self._empty
        self.setText(f"{self._prefix}{lab}")

    def _open_dialog(self):
        self._open = True
        try:
            v = choose(self._win or self.window(), self._title, self._groups_fn(),
                       current=self._value, label_fn=self._label_fn)
        finally:
            self._open = False
        if v is not None:
            self.set_value(v)
            if self._on_pick:
                self._on_pick(v)
