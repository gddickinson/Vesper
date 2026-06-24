"""Headless drive check: cycle every scene + mode, assert thread-stability.

Builds a real ``MainWindow`` offscreen, then:
  - cycles through every registered scene (``scenes.names()``), ticking + grabbing
    each so the draw path actually runs;
  - applies every mode (``modes``) so each workspace/scene/voice combo is exercised;
  - asserts ``threading.active_count()`` never grows (catches a render/worker thread
    leaking per frame).

Run for BOTH faces:  python tools/drive_check.py        (3D / default)
                     VESPER_FACE=cat python tools/drive_check.py   (2D cast)
"""
from __future__ import annotations

import os
import sys
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import modes  # noqa: E402
from vesper import scenes  # noqa: E402
from vesper.window import MainWindow  # noqa: E402


def _ticks(win, n=8):
    for _ in range(n):
        win._tick()


def main() -> int:
    face = os.environ.get("VESPER_FACE", "3d")
    app = QApplication.instance() or QApplication([])
    win = MainWindow()
    win.resize(1100, 720)
    _ticks(win, 6)
    base = threading.active_count()
    worst = base
    issues = []

    for name in scenes.names():
        win.set_scene(name)
        _ticks(win)
        win.grab()
        ac = threading.active_count()
        worst = max(worst, ac)
        if ac > base + 1:
            issues.append(f"scene {name!r}: threads {base} -> {ac}")

    for m in modes.names():
        try:
            win.apply_mode(m)
        except Exception as e:                       # noqa: BLE001
            issues.append(f"mode {m!r}: {e!r}")
            continue
        _ticks(win)
        win.grab()
        ac = threading.active_count()
        worst = max(worst, ac)
        if ac > base + 1:
            issues.append(f"mode {m!r}: threads {base} -> {ac}")

    app.processEvents()
    print(f"[{face}] scenes={len(scenes.names())} base_threads={base} "
          f"worst_threads={worst} issues={len(issues)}")
    for s in issues:
        print("  !", s)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
