"""Offscreen test for the "Always warm (low-blue) screen" accessibility toggle.

Off by default the screen is unwarmed; on, a gentle 0.18 warm floor is held on
both the face and the scene at any time (composed via max with the clock/Sleep
warmth, so Sleep wind-down still deepens beyond it), persisted across the
settings round-trip, and exposed as a View-menu toggle. Threads stay stable.
"""
import os
import sys
import tempfile
import threading

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import store  # noqa: E402


def main():
    app = QApplication.instance() or QApplication([])
    from vesper.window import MainWindow
    win = MainWindow()
    win.show()
    for _ in range(5):
        app.processEvents()
    base = threading.active_count()

    win._clock_light = False          # isolate the always-warm floor from clock warmth
    win.apply_mode("Meditate")        # not Sleep, not running -> floor is the only warmth

    # default off -> no warmth
    assert win._always_warm is False
    for _ in range(3):
        win._tick()
        app.processEvents()
    assert win.face._warm < 1e-6 and win.viz._warm < 1e-6, (win.face._warm, win.viz._warm)
    print("ok: default off -> screen is unwarmed")

    # on -> a gentle 0.18 floor on both face + scene, and it persists
    win.set_always_warm(True)
    assert win._always_warm is True
    assert store.load_settings().get("always_warm") is True
    for _ in range(3):
        win._tick()
        app.processEvents()
    assert abs(win.face._warm - 0.18) < 1e-6, win.face._warm
    assert abs(win.viz._warm - 0.18) < 1e-6, win.viz._warm
    print("ok: on -> 0.18 warm floor on face + scene; persisted")

    # off again clears it
    win.set_always_warm(False)
    for _ in range(3):
        win._tick()
        app.processEvents()
    assert win.face._warm < 1e-6 and win.viz._warm < 1e-6
    assert store.load_settings().get("always_warm") is False
    print("ok: off again -> cleared + persisted")

    # the View menu carries the toggle
    labels = []
    for act in win.menuBar().actions():
        mm = act.menu()
        if not mm:
            continue
        labels += [a.text() for a in mm.actions()]
    assert any("Warm screen" in x for x in labels), "menu toggle missing"
    print("ok: View menu carries the toggle")

    for _ in range(15):
        win._tick()
        app.processEvents()
    now = threading.active_count()
    win.close()
    for _ in range(3):
        app.processEvents()
    assert now <= base + 1, (base, now)
    print(f"ok: threads stable ({base} -> {now})")
    print("PASS: always-warm low-blue screen toggle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
