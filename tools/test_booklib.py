"""Offscreen test for the Find & manage books dialog (vesper/booklib.py).

The regression this guards: a freshly added book must appear in the **Read** book
picker immediately (the dialog used to rebuild only the Sleep workspace). Also
checks the management handlers -- typed download outcomes shown plainly, rename,
delete (with the confirm auto-accepted), and the live library report -- with no
sockets (all fetches are simulated through Outcome objects).
"""
import os
import sys
import tempfile
import threading

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QApplication, QInputDialog,  # noqa: E402
                               QMessageBox)

from breathsim import books, booksource  # noqa: E402
from breathsim.booksource import Outcome  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")
books._meta_write("_seeded.json", {"sample": True})   # opt out of the sample seed here


def main():
    app = QApplication.instance() or QApplication([])
    bid = books.save(booksource.text_to_book(
        "It is a truth. A single man wants a wife. However little known.",
        "Pride and Prejudice", "Jane Austen"))

    from vesper import booklib
    from vesper.window import MainWindow
    win = MainWindow()
    win.show()
    for _ in range(5):
        app.processEvents()
    base = threading.active_count()

    dlg = booklib.open_library(win)
    assert dlg.library.count() == 1, dlg.library.count()
    assert "1 book" in dlg.lib_header.text(), dlg.lib_header.text()
    print("ok: dialog lists the library + a report header")

    # THE FIX: a new book added while in Read mode appears in the Read picker.
    win.apply_mode("Read")
    assert win.current_mode == "Read"
    before = list(win.panel._w.get("read_ids") or [])
    nbid = books.save(booksource.text_to_book(
        "Call me Ishmael. Some years ago, never mind how long precisely.",
        "Moby Dick", "Herman Melville"))
    booklib._refresh_app(win)
    after = list(win.panel._w.get("read_ids") or [])
    assert nbid in after and nbid not in before, (before, after)
    print(f"ok: downloaded book shows in the Read picker ({len(before)} -> {len(after)})")

    # a successful download Outcome is shown with length + size; library refreshes
    dlg._on_downloaded(Outcome(True, book_id=nbid, reason="saved",
                               title="Moby Dick", sentences=2, byte_size=4096))
    assert "Saved" in dlg.note.text() and "sentences" in dlg.note.text()
    assert dlg.library.count() == 2
    print("ok: successful download shows length/size + refreshes the library")

    # a failed download shows its specific reason, not a blank message
    dlg._on_downloaded(Outcome(False, reason="incomplete",
                               detail="The download arrived incomplete."))
    assert dlg.note.text() == "The download arrived incomplete.", dlg.note.text()
    print("ok: a failed download surfaces its specific reason")

    # rename (auto-answer the two input dialogs)
    seq = iter([("Pride & Prejudice", True), ("Jane Austen", True)])
    QInputDialog.getText = staticmethod(lambda *a, **k: next(seq))
    dlg.library.setCurrentRow(0)
    dlg._rename()
    titles = {b["title"] for b in books.list_books()}
    assert "Pride & Prejudice" in titles, titles
    print("ok: rename updates the saved book in place")

    # delete (auto-accept the confirm) removes it + refreshes app without crashing
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    n0 = dlg.library.count()
    dlg.library.setCurrentRow(0)
    dlg._delete()
    assert dlg.library.count() == n0 - 1, (n0, dlg.library.count())
    print(f"ok: delete removes a book ({n0} -> {dlg.library.count()})")

    dlg.accept()
    for _ in range(10):
        win._tick()
        app.processEvents()
    now = threading.active_count()
    win.close()
    for _ in range(3):
        app.processEvents()
    assert now <= base + 1, (base, now)
    print(f"ok: threads stable ({base} -> {now})")
    print("PASS: Find & manage books dialog (refresh fix + management)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
