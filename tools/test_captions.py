"""Offline test for the accessibility Narration captions toggle.

Checks the pure `captions.wrap` word-wrap/elide helper, that the View toggle
`set_captions` round-trips + persists + clears the overlay, and that with
captions on a Sleep narration line is wrapped onto the viz scene (so a deaf /
hard-of-hearing user sees the spoken text). Offscreen Qt; no audio.
"""
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_wrap():
    from vesper import captions
    assert captions.wrap("") == []
    assert captions.wrap(None) == []
    one = captions.wrap("a calm short line", width=40)
    assert one == ["a calm short line"], one
    many = captions.wrap("the quick brown fox jumps over the lazy dog again", width=18)
    assert all(len(ln) <= 18 + 3 for ln in many), many   # +3 allows the ellipsis
    assert 1 <= len(many) <= 3
    # a very long line is capped at max_lines and elided so it never overflows
    long = captions.wrap(" ".join(["word"] * 60), width=20, max_lines=3)
    assert len(long) == 3 and long[-1].endswith("...")
    print("ok: wrap word-wraps, caps at max_lines, elides overflow")


def test_toggle_and_caption():
    from PySide6.QtWidgets import QApplication
    from breathsim import store
    app = QApplication.instance() or QApplication([])
    from vesper.window import MainWindow
    w = MainWindow()

    # default off, overlay empty
    assert w._captions is False
    assert w.viz._caption == []

    # turn on -> persisted
    w.set_captions(True)
    assert w._captions is True
    assert store.load_settings().get("captions") is True

    # in Sleep + scene view + a spoken line -> the line is wrapped onto the scene
    w.apply_mode("Sleep")
    w.set_view("scene")
    w._story_line = "You let your shoulders soften now, and your breath grows slow."
    w.controller.start()
    w._tick()
    app.processEvents()
    assert w.viz._caption, "captions should appear on the scene during narration"
    joined = " ".join(w.viz._caption)
    assert "shoulders soften" in joined

    # in the talking-head FACE view the same line is wrapped onto the face too
    w.set_captions(True)
    w.set_view("face")
    w._story_line = "You let the warm gold light carry you gently down toward sleep."
    w._tick()
    app.processEvents()
    assert w.face._caption, "captions should appear on the face view during narration"
    assert "warm gold light" in " ".join(w.face._caption)

    # turn off -> BOTH overlays clear immediately + persisted off
    w.set_captions(False)
    assert w.viz._caption == [] and w.face._caption == []
    assert store.load_settings().get("captions") is False
    w.close()
    print("ok: toggle round-trips, persists, wires scene+face caption, clears when off")


def test_paint_caption_renders():
    """The shared paint_caption helper draws onto any QPainter without error and
    is a no-op for empty input (so both views can call it unconditionally)."""
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])             # QFont needs a QGuiApplication
    from vesper import captions
    img = QImage(400, 300, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    captions.paint_caption(p, 400, 300, [])                 # empty -> no-op, no crash
    captions.paint_caption(p, 400, 300, captions.wrap(
        "You breathe out slowly, and the lanterns drift on the dark water."))
    p.end()
    print("ok: paint_caption draws onto a QPainter and no-ops on empty input")


def main():
    test_wrap()
    test_paint_caption_renders()
    test_toggle_and_caption()
    print("PASS: narration captions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
