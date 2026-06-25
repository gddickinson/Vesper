"""Offline test for drag-and-drop book loading (vesper/win_dnd.py).

Covers the pure path filter (book_paths) and the import driver
(import_dropped_books) end to end: a dropped .txt is imported into the local
library and shows up under the Sleep story picker. Needs an offscreen
QApplication (it builds the window to exercise the mixin) but no network.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vesper import win_dnd  # noqa: E402


def main():
    # pure filter: keep .txt/.epub (any case), drop everything else + non-strings
    keep = win_dnd.book_paths(
        ["/a/book.txt", "/b/Novel.EPUB", "/c/song.mp3", "/d/pic.png", "", None, 7])
    assert keep == ["/a/book.txt", "/b/Novel.EPUB"], keep
    assert win_dnd.book_paths([]) == []
    print("ok: book_paths keeps only .txt/.epub")

    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from vesper.window import MainWindow
    from breathsim import stories
    win = MainWindow()

    # write a temp .txt and 'drop' it
    d = tempfile.mkdtemp()
    p = os.path.join(d, "My Dropped Novel.txt")
    with open(p, "w") as f:
        f.write(" ".join(f"Sentence {i}." for i in range(30)))
    before = len(stories.book_names())
    added = win.import_dropped_books([p, "/not/a/book.mp3"])
    assert len(added) == 1, added
    names = stories.book_names()
    assert len(names) == before + 1
    assert any("My Dropped Novel" in n for n in names), names
    print(f"ok: dropped .txt imported -> appears in Sleep picker as {names[-1]!r}")

    # a drop with no importable files reports gracefully, imports nothing
    none = win.import_dropped_books(["/x/y.mp3", "/z/w.png"])
    assert none == []
    print("ok: a drop with no books imports nothing (handled gracefully)")

    win.close()
    print("PASS: drag-and-drop book loading")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
