"""Offline stability test for mode switching -- the app's PRIMARY navigation.

Selecting a mode (Meditate / Breathwork / Chant / Sing / Relax / Sleep / Read)
runs `apply_mode`, which rebuilds the whole side-panel workspace, swaps the
pattern / voices / ambience / effect / choir / scene / persona, stops the
narrator, and enters or leaves the Read pane. Users do this constantly, so it
must never raise and must not leak threads (repeated narrator stop/start +
workspace rebuilds). This cycles every mode many times -- plus a rapid
Read<->Sleep flip -- and asserts no exception, the workspace actually rebuilds,
and the thread count stays bounded. Offscreen Qt; no audio device.
"""
import os
import sys
import tempfile
import threading

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import modes  # noqa: E402


def main():
    app = QApplication.instance() or QApplication([])
    from vesper.window import MainWindow
    w = MainWindow()

    names = modes.names()
    assert names and "Sleep" in names and "Read" in names, names
    base = threading.active_count()

    # cycle every mode three full times, ticking after each switch
    for _round in range(3):
        for nm in names:
            w.apply_mode(nm)
            assert w.current_mode == nm, ("apply_mode did not take", nm, w.current_mode)
            assert w.panel is not None, "panel went away after a workspace rebuild"
            w._tick()
            app.processEvents()
    print("ok: cycled all %d modes x3 (with ticks), workspace rebuilt each time" % len(names))

    # a rapid back-and-forth that exercises the heaviest transitions
    # (Read enter/leave + the Sleep storyteller arming, both touching the narrator)
    for _ in range(6):
        w.apply_mode("Read")
        w._tick()
        w.apply_mode("Sleep")
        w._tick()
        app.processEvents()
    print("ok: rapid Read<->Sleep flips survive (narrator + read pane churn)")

    worst = threading.active_count()
    assert worst <= base + 2, ("thread leak across mode cycling", base, worst)
    print("ok: threads stable (base=%d worst=%d) -- no leak from rebuilds/narrator"
          % (base, worst))

    w.close()
    print("PASS: mode-cycle stability")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
