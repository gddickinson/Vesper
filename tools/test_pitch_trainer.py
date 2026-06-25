"""Regression test for the Sing pitch-trainer exercise selector.

Bug: changing the exercise from 'Hold note' to a scale did nothing -- the target
sat on the base note. Cause: the trainer read ``controller.elapsed()`` (frozen
until a breathing session is *playing*), so at t=0 every spec returns step[0] and
all exercises looked identical. Fix: drive the exercise from the always-advancing
animation clock (``pitch_clock()`` = ``_anim_t - _pitch_t0``), so a scale scrolls
as a standalone warm-up. This asserts the target now advances with no running
session, and that Hold note stays put.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import vocaltrainer as vt  # noqa: E402


def main():
    app = QApplication.instance() or QApplication([])
    from vesper.window import MainWindow
    win = MainWindow()
    win.apply_mode("Sing")

    # No breathing session is playing -- the exact condition the bug appeared in.
    assert not win.controller.running
    assert win.controller.elapsed() < 0.5      # the old (frozen) clock

    # Turn on the guide with a SCALE exercise.
    win.show_pitch_guide(vt.scale_spec("Major scale (do-re-mi)", "C4"))
    base_t0 = win._pitch_t0

    # At the start the target is the base note (C4 ~ 261.6 Hz).
    win._anim_t = base_t0
    first = win.pitch_context(win.pitch_clock())["target"]
    assert abs(first - 261.6) < 1.0, first

    # ~6 s of animation time later (still NOT playing), the scale has stepped on:
    # i = int(6 / 2.5) = 2 -> step[2] = 4 semitones -> E4 ~ 329.6 Hz.
    win._anim_t = base_t0 + 6.0
    later = win.pitch_context(win.pitch_clock())["target"]
    assert abs(later - 329.6) < 1.0, later
    assert abs(later - first) > 1.0, (first, later)
    print(f"ok: scale advances with no session playing: {first:.1f} -> {later:.1f} Hz")

    # Collect several distinct targets across the scale to prove it scrolls.
    seen = set()
    for k in range(8):
        win._anim_t = base_t0 + k * 2.6
        seen.add(round(win.pitch_context(win.pitch_clock())["target"], 1))
    assert len(seen) >= 5, seen
    print(f"ok: {len(seen)} distinct scale targets seen while idle")

    # Hold note stays on its single note across the same time span.
    win.show_pitch_guide(vt.hold_spec("C4"))
    h0 = win._pitch_t0
    hold_vals = set()
    for k in range(6):
        win._anim_t = h0 + k * 2.6
        hold_vals.add(round(win.pitch_context(win.pitch_clock())["target"], 1))
    assert len(hold_vals) == 1, hold_vals
    print(f"ok: Hold note stays put: {hold_vals}")

    # Switching exercise re-anchors the clock so the new exercise starts fresh.
    win._anim_t = h0 + 99.0
    win.show_pitch_guide(vt.scale_spec("Major arpeggio", "C4"))
    assert abs(win.pitch_clock()) < 1e-6           # restarts at 0
    start = win.pitch_context(win.pitch_clock())["target"]
    assert abs(start - 261.6) < 1.0, start          # arpeggio begins on the tonic
    print("ok: choosing a new exercise restarts it from its first note")

    win.close()
    print("PASS: pitch-trainer exercise selector drives the scale")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
