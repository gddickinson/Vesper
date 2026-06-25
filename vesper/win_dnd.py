"""Drag-and-drop file loading for the MainWindow (a mixin).

Drop a ``.txt`` or ``.epub`` anywhere on the window and it is imported into the
local book library (never uploaded anywhere), then the Sleep story picker and
menus refresh so the new novel is ready to read at bedtime. Other files are
politely ignored. The path filtering (`book_paths`) and the import driver
(`import_dropped_books`) are plain and unit-testable; the Qt event handlers are
thin wrappers.
"""
from __future__ import annotations

BOOK_EXT = (".txt", ".epub")


def book_paths(paths):
    """Keep only the importable book files from a list of local paths (pure)."""
    return [p for p in paths if isinstance(p, str)
            and p.lower().endswith(BOOK_EXT)]


class _DnDMixin:
    def dragEnterEvent(self, ev):
        md = ev.mimeData()
        if md.hasUrls() and book_paths([u.toLocalFile() for u in md.urls()]):
            ev.acceptProposedAction()
        else:
            ev.ignore()

    def dragMoveEvent(self, ev):
        self.dragEnterEvent(ev)

    def dropEvent(self, ev):
        md = ev.mimeData()
        paths = book_paths([u.toLocalFile() for u in md.urls()]) \
            if md.hasUrls() else []
        if not paths:
            ev.ignore()
            return
        ev.acceptProposedAction()
        self.import_dropped_books(paths)

    def import_dropped_books(self, paths):
        """Import dropped .txt/.epub files into the library; refresh + report.
        Returns the list of new book ids (empty if none read)."""
        from breathsim import bookimport
        from . import booklib
        added = []
        for p in book_paths(paths):
            try:
                bid = bookimport.import_file(p)
            except Exception:
                bid = None
            if bid:
                added.append(bid)
        if added:
            booklib._refresh_app(self)
            n = len(added)
            self.status.showMessage(
                f"Added {n} book{'s' if n != 1 else ''} - pick it under "
                "'Your novels' in the Sleep bedtime story.", 6000)
        else:
            self.status.showMessage(
                "Could not read that file - try a plain .txt or a standard "
                ".epub.", 5000)
        return added
