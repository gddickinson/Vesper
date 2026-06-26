"""Regression: pressing Play on a FINISHED (or stale) book reads from the start.

`books.set_position` doesn't clamp and `bookreader.units` clips the start to the
sentence count, so a saved resume position at/past the end -- a book read to the
end, or a position left over after the book was re-imported/replaced with fewer
sentences -- used to yield an EMPTY narration: you press Play and get silence.
`win_read.start_reading` now detects that and restarts from the beginning (with a
gentle status note), while a genuine mid-book resume is left untouched. Offscreen
Qt; no audio device.
"""
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import books, bookreader  # noqa: E402


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None

    b = books.from_text(
        "One quiet sentence. Two quiet sentences. Three of them now. "
        "Four in the dark. Five and then sleep.", "A Tiny Book", "Tester")
    books.save(b)
    total = len(b.sentences())
    assert total >= 5, total

    from vesper.window import MainWindow
    w = MainWindow()
    w.apply_mode("Read")
    w.set_reading_book(b.id)

    # 1) FINISHED: position parked at the very end -> Play must restart, not go silent
    books.set_position(b.id, total)
    w.start_reading()
    assert w._reading, "should be reading"
    assert w._read_idx == 0, ("finished book: Play should restart from 0, got",
                              w._read_idx)
    assert books.position(b.id) == 0, "finished book: resume position reset to 0"
    # and there is actually something to narrate from here
    assert len(list(bookreader.units(b, start=w._read_idx))) == total
    w.stop_reading()
    print("ok: Play on a finished book restarts from the beginning (not silence)")

    # 2) STALE: position past the end (book shrank after a re-import) -> restart too
    books.set_position(b.id, total + 50)
    w.start_reading()
    assert w._read_idx == 0 and books.position(b.id) == 0, "stale position -> restart"
    w.stop_reading()
    print("ok: a stale position past the (changed) end also restarts cleanly")

    # 3) MID-BOOK: a genuine resume must be preserved, NOT reset
    books.set_position(b.id, 2)
    w.start_reading()
    assert w._read_idx == 2, ("mid-book resume must be preserved", w._read_idx)
    assert books.position(b.id) == 2, "mid-book resume must not be reset"
    w.stop_reading()
    print("ok: a genuine mid-book resume is preserved")

    print("PASS: finished/stale book restarts; mid-book resume preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
