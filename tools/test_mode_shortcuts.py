"""Offline test: number keys 1-N jump straight to a mode.

The mode bar is the app's primary navigation, but a keyboard-only user could
only reach it by tabbing or via the Modes menu. `shortcuts.bind` wires a digit
key to each mode (1 = the first mode ... up to 9). This checks there is exactly
one shortcut per mode, that the key and the target mode line up in order, and
that firing a shortcut actually switches ``current_mode`` -- so the binding can
never silently drift from ``modes.names()``. Qt only (offscreen), no audio.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QKeySequence  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from vesper.window import MainWindow  # noqa: E402
from breathsim import modes  # noqa: E402


def test_mode_number_shortcuts():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()

    sc = win._mode_shortcuts
    names = modes.names()
    # one shortcut per mode (capped at the 9 single-digit keys)
    assert len(sc) == min(len(names), 9), (len(sc), len(names))

    for idx, (key, name, shortcut) in enumerate(sc, start=1):
        assert key == str(idx), (key, idx)
        assert name == names[idx - 1], (name, names[idx - 1])
        # the QShortcut really carries that digit
        assert shortcut.key() == QKeySequence(str(idx)), key
        # firing it switches the mode (start from a different one each time)
        other = names[(idx) % len(names)]
        win.apply_mode(other)
        assert win.current_mode == other
        shortcut.activated.emit()
        assert win.current_mode == name, (win.current_mode, name)

    win.close()
    print("ok: %d mode number-keys all switch the mode in order" % len(sc))


def main():
    test_mode_number_shortcuts()
    print("PASS: number-key mode shortcuts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
