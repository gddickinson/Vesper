"""Offscreen test for Read-mode chapter navigation (win_read + sections_read).

Verifies: a book with chapter headings exposes `book_chapters()`; the Read card's
"Jump to a chapter" button is enabled when a book has chapters and disabled
otherwise; `jump_to_chapter` moves the read position (and persists it) and the
read-along highlight while paused; and, while narrating, a jump restarts the
narrator from the chapter. The narrator is stubbed so no real audio is produced;
threads stay stable.
"""
import os
import sys
import tempfile
import threading

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import books, bookreader  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")


def _novel_text():
    out = []
    for c in ["I", "II", "III", "IV", "V"]:
        out.append(f"CHAPTER {c}")
        out.append(" ".join(f"Sentence {i} of chapter {c}." for i in range(8)))
    return "\n\n".join(out)


def main():
    app = QApplication.instance() or QApplication([])
    bid = books.save(books.from_text(_novel_text(), "A Test Novel", "Anon"))
    flat = books.save(books.from_text("Just prose with no headings at all here. "
                                      "And a second sentence.", "Flat Book"))
    chs = bookreader.chapters(books.load(bid))
    assert len(chs) == 5, chs

    from vesper.window import MainWindow
    win = MainWindow()
    win.show()
    for _ in range(5):
        app.processEvents()
    base = threading.active_count()
    win.narrator.start = lambda *a, **k: None
    win.narrator.stop = lambda: None

    win.apply_mode("Read")
    win.set_reading_book(bid)
    assert win.current_mode == "Read"
    assert len(win.book_chapters()) == 5, win.book_chapters()
    btn = win.panel._w.get("read_chapters")
    assert btn is not None and btn.isEnabled(), "Chapters button should enable"
    print("ok: a book with chapters exposes them + enables the Jump button")

    # jump while paused -> position moves + persists + the pane highlights it
    target = chs[3][0]
    win.jump_to_chapter(target)
    assert win._read_idx == target and books.position(bid) == target
    assert win.read_pane._last_hl == target
    print(f"ok: jump (paused) moves to sentence {target}, persists + highlights")

    # jump while narrating -> restarts from the chapter (stubbed narrator)
    win.start_reading()
    assert win._reading
    target2 = chs[1][0]
    win.jump_to_chapter(target2)
    assert win._reading and win._read_idx == target2
    assert books.position(bid) == target2
    win.stop_reading()
    print(f"ok: jump (while reading) restarts from sentence {target2}")

    # a heading-less book disables the button (via the refresh hook)
    win.set_reading_book(flat)
    assert win.book_chapters() == []
    assert not btn.isEnabled(), "Chapters button should disable for a flat book"
    print("ok: a heading-less book disables the Jump button")

    for _ in range(15):
        win._tick()
        app.processEvents()
    now = threading.active_count()
    win.close()
    for _ in range(3):
        app.processEvents()
    assert now <= base + 1, (base, now)
    print(f"ok: threads stable ({base} -> {now})")
    print("PASS: Read-mode chapter navigation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
