"""Offscreen test for chapter navigation in the standalone Reader dialog
(vesper/reader.py), mirroring the Read-mode jump.

Verifies: a book with chapter headings enables the "Jump to a chapter" button and
exposes the chapters; `_jump_to_chapter` moves + persists the resume position and
the read-along highlight while paused, and restarts the narrator from the chapter
while reading; a heading-less book disables the button. The narrator is stubbed so
no audio is produced; threads stay stable.
"""
import os
import sys
import tempfile
import threading

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import bookreader, books  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")


def _novel_text():
    out = []
    for c in ["I", "II", "III", "IV"]:
        out.append(f"CHAPTER {c}")
        out.append(" ".join(f"Sentence {i} of chapter {c}." for i in range(8)))
    return "\n\n".join(out)


def main():
    app = QApplication.instance() or QApplication([])
    bid = books.save(books.from_text(_novel_text(), "A Test Novel", "Anon"))
    flat = books.save(books.from_text("Just prose with no headings here at all. "
                                      "A second sentence follows.", "Flat Book"))
    chs = bookreader.chapters(books.load(bid))
    assert len(chs) == 4, chs

    from vesper.window import MainWindow
    from vesper import reader
    win = MainWindow()
    win.show()
    for _ in range(5):
        app.processEvents()
    base = threading.active_count()
    win.narrator.start = lambda *a, **k: None
    win.narrator.stop = lambda: None

    dlg = reader.open_reader(win)
    # the chaptered book is selected first -> button enabled, chapters cached
    assert dlg.chapters_btn.isEnabled(), "Chapters button should enable"
    assert len(dlg._chapters) == 4
    print("ok: Reader lists chapters + enables the Jump button")

    # jump while paused -> position moves + persists + the pane highlights it
    target = chs[2][0]
    dlg._jump_to_chapter(target)
    assert dlg._reader_idx == target and books.position(bid) == target
    assert dlg._last_hl == target, (dlg._last_hl, target)
    print(f"ok: jump (paused) moves to sentence {target}, persists + highlights")

    # jump while reading -> restarts the narrator from the chapter (stubbed)
    dlg._start()
    assert dlg.stop_btn.isEnabled()
    target2 = chs[1][0]
    dlg._jump_to_chapter(target2)
    assert dlg.stop_btn.isEnabled() and dlg._reader_idx == target2
    assert books.position(bid) == target2
    dlg._stop()
    print(f"ok: jump (while reading) restarts from sentence {target2}")

    # a heading-less book disables the button (select it in the combo + reload)
    idx = dlg._ids.index(flat) if flat in dlg._ids else None
    assert idx is not None
    dlg.combo.setCurrentIndex(idx)
    dlg._load_selected()
    assert dlg._chapters == [] and not dlg.chapters_btn.isEnabled()
    print("ok: a heading-less book disables the Jump button")

    dlg.close()
    for _ in range(10):
        win._tick()
        app.processEvents()
    now = threading.active_count()
    win.close()
    for _ in range(3):
        app.processEvents()
    assert now <= base + 1, (base, now)
    print(f"ok: threads stable ({base} -> {now})")
    print("PASS: Reader-dialog chapter navigation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
