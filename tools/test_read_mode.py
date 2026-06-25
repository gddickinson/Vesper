"""Offscreen test for the dedicated Read mode (vesper/win_read.py + read_pane.py).

Verifies: Read is a mode; entering it shows the read-along pane below the
face/scene and loads a book; start/stop reading drives the (stubbed) narrator and
persists resume; the read pane builds per-sentence ranges and highlights; leaving
Read hides the pane and stops reading; threads stay stable. The narrator is
stubbed so no real `say`/Kokoro audio is produced.
"""
import os
import sys
import tempfile
import threading

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import books, modes  # noqa: E402


def main():
    assert "Read" in modes.names(), modes.names()
    app = QApplication.instance() or QApplication([])
    text = " ".join(f"Sentence {i} of the tale." for i in range(25))
    bid = books.save(books.from_text(text, "A Test Novel", source="upload"))

    from vesper.window import MainWindow
    win = MainWindow()
    win.show()
    for _ in range(5):
        app.processEvents()
    base = threading.active_count()

    captured = {}
    win.narrator.start = lambda units, *a, **k: captured.__setitem__("units", list(units))
    win.narrator.stop = lambda: captured.__setitem__("stopped", True)

    # enter Read: pane shows, the in-progress/first book loads, ranges built
    win.apply_mode("Read")
    assert win.current_mode == "Read"
    assert win.read_pane.isVisible(), "read-along pane should show in Read mode"
    assert win._read_bid == bid
    assert len(win.read_pane._ranges) == 25, len(win.read_pane._ranges)
    print("ok: Read mode shows the read-along pane and loads a book")

    # start reading -> units flow to the (stubbed) narrator; pane shows Pause
    win.start_reading()
    assert win._reading and captured.get("units")
    assert win.read_pane.play.text() == "Pause"
    # a narrated unit advances the resume position + the highlight
    win._on_read_unit({"sentence": 4})
    assert win._read_idx == 4 and books.position(bid) == 4
    win._read_follow()
    assert win.read_pane._last_hl == 4
    print("ok: reading starts, advances resume position + highlight")

    # audio-only hides the text pane; back on shows it
    win.set_read_along(False)
    assert not win.read_pane.isVisible()
    win.set_read_along(True)
    assert win.read_pane.isVisible()
    print("ok: read-along toggle shows/hides the text")

    # stop reading persists position and resets the button
    win.stop_reading()
    assert not win._reading and captured.get("stopped")
    assert win.read_pane.play.text() == "Read"
    assert books.position(bid) == 4

    # leaving Read hides the pane and stops any reading
    win.apply_mode("Meditate")
    assert not win.read_pane.isVisible()
    assert not win._reading
    print("ok: leaving Read hides the pane and stops reading")

    for _ in range(20):
        win._tick()
        app.processEvents()
    now = threading.active_count()
    win.close()
    for _ in range(3):
        app.processEvents()
    assert now <= base + 1, (base, now)
    print(f"ok: threads stable ({base} -> {now})")
    print("PASS: dedicated Read mode")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
