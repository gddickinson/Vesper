"""Offscreen test for the Read-mode opt-in sleep fade (win_read + sections_read).

Verifies: the reading narrator is started with the window's `_read_level` as its
level function (so the *voice* quietens, not just the bed); with the fade off the
level is a constant 1.0; with a fade armed the level eases from 1.0 down to 0.0
across the ramp; and once the fade completes `_read_follow` stops the reading.
The clock is driven deterministically by back-dating `_read_fade_t0` (no real
waiting); the narrator is stubbed so no audio is produced; threads stay stable.
"""
import os
import sys
import tempfile
import threading
import time

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import books  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")


def main():
    app = QApplication.instance() or QApplication([])
    bid = books.save(books.from_text(
        " ".join(f"Line {i} of the tale." for i in range(30)), "A Novel", "Anon"))

    from vesper.window import MainWindow
    win = MainWindow()
    win.show()
    for _ in range(5):
        app.processEvents()
    base = threading.active_count()

    captured = {}
    win.narrator.start = lambda units, level=None, *a, **k: captured.update(
        level=level, units=list(units))
    win.narrator.stop = lambda: captured.update(stopped=True)

    win.apply_mode("Read")
    win.set_reading_book(bid)

    # fade off -> the level function is a constant 1.0
    win.set_read_fade(0)
    win.start_reading()
    assert captured.get("level") == win._read_level, "narrator must get _read_level"
    assert win._read_level() == 1.0
    print("ok: reading uses _read_level as its level function; off -> 1.0")

    captured.pop("stopped", None)        # ignore the mode-switch narrator.stop()

    # arm a 15-minute fade; before the mark the level is still full
    win.set_read_fade(15)
    win._read_fade_t0 = time.monotonic() - (10 * 60)        # 10 min in -> pre-mark
    assert win._read_level() == 1.0, win._read_level()
    # halfway through the 30s ramp after the mark -> ~0.5, not done
    win._read_fade_t0 = time.monotonic() - (15 * 60 + 15)
    mid = win._read_level()
    assert 0.0 < mid < 1.0, mid
    win._read_follow()
    assert win._reading and not captured.get("stopped"), "mid-fade must keep reading"
    print(f"ok: mid-fade eases the narration level ({mid:.2f}), still reading")

    # past the end of the ramp -> level 0 and _read_follow stops the reading
    win._read_fade_t0 = time.monotonic() - (15 * 60 + 31)
    assert win._read_level() == 0.0
    win._read_follow()
    assert captured.get("stopped") and not win._reading
    print("ok: completed fade quietens to 0 and stops the reading")

    # the Read card exposes the sleep-fade combo
    win.apply_mode("Read")
    assert "read_fade" in win.panel._w, "Read card should have a sleep-fade combo"
    print("ok: Read card exposes the sleep-fade control")

    for _ in range(12):
        win._tick()
        app.processEvents()
    now = threading.active_count()
    win.close()
    for _ in range(3):
        app.processEvents()
    assert now <= base + 1, (base, now)
    print(f"ok: threads stable ({base} -> {now})")
    print("PASS: Read-mode opt-in sleep fade")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
