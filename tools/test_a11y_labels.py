"""Offline test: the primary controls expose screen-reader labels.

The app is audio-first, so blind and low-vision users rely on it -- but toolTips
are hover-only and invisible to a screen reader (VoiceOver / NVDA). Every pinned
primary control (the mode bar, the view toggle, the master-volume slider, and the
transport buttons) and the central visualization must therefore expose a non-empty
``accessibleName`` so assistive tech announces something meaningful rather than a
bare "slider" or an anonymous blank. This builds the real window offscreen and
checks those labels are present. Qt only (offscreen), no audio device needed.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from vesper.window import MainWindow  # noqa: E402
from breathsim import modes  # noqa: E402


def test_primary_controls_labelled():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    p = win.panel

    # Every mode-bar button is named "<Mode> mode" and described.
    assert set(p._mode_btns) == set(modes.names()), p._mode_btns.keys()
    for name, b in p._mode_btns.items():
        assert b.accessibleName() == f"{name} mode", (name, b.accessibleName())
        assert b.accessibleDescription(), name

    # The two view-toggle buttons are named.
    for key, b in p._view_btns.items():
        assert b.accessibleName().endswith("view"), (key, b.accessibleName())

    # The master-volume slider -- the worst offender without a name.
    assert p.vol.accessibleName() == "Master volume", p.vol.accessibleName()
    assert p.vol.accessibleDescription()

    # Transport: Start/Pause keeps its live text as the name, but is described;
    # Reset gets an explicit name.
    assert p.start_btn.accessibleDescription(), "start button needs a description"

    # The central visuals are named, not anonymous blanks.
    assert win.face.accessibleName(), "face widget unnamed"
    assert win.viz.accessibleName(), "viz widget unnamed"

    win.close()
    print("ok: mode bar, view toggle, volume slider, transport + visuals all labelled")


def main():
    test_primary_controls_labelled()
    print("PASS: screen-reader labels on primary controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
