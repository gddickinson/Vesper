"""Drive every workspace's SIDE-PANEL controls -- the part users touch most.

The menu-driven GUI drive (test_gui_drive) exercises the menu bar; this one walks
the ControlPanel widget tree in EVERY mode and works the interactive controls --
each QComboBox through its options, each slider across min / mid / max, each
checkbox / radio toggled -- firing their real wired handlers. Buttons are skipped
(they open dialogs / file pickers / downloads). A bad slider or combo handler --
or one that touches a deleted object after a panel rebuild, which Qt swallows
silently in a slot -- is caught here (via a sys.excepthook recorder). Offscreen
Qt; no audio device.
"""
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDial,  # noqa: E402
                               QDialog, QMessageBox, QRadioButton, QSlider)

from breathsim import books, modes  # noqa: E402

# Keep any incidental dialog from blocking the headless run.
QDialog.exec = lambda self: 0
QMessageBox.exec = lambda self: 0

# Qt routes a slot exception to sys.excepthook instead of propagating it; record
# those so a handler that blows up still fails this test.
_SLOT_ERRORS = []
_real_hook = sys.excepthook


def _hook(t, v, tb):
    _SLOT_ERRORS.append("%s: %s" % (t.__name__, v))
    _real_hook(t, v, tb)


sys.excepthook = _hook


def _alive(w):
    try:
        w.objectName()
        return True
    except RuntimeError:                          # C++ side deleted by a rebuild
        return False


def _drive_panel(w, fired):
    panel = w.panel
    # combos: step through (capped) options, firing currentIndexChanged
    for cb in panel.findChildren(QComboBox):
        if not _alive(cb):
            continue
        n = cb.count()
        for i in list(range(min(n, 16))) + ([n - 1] if n > 16 else []):
            if not _alive(cb):
                break
            cb.setCurrentIndex(i)
            w._tick()
            fired[0] += 1
    # sliders / dials: min, middle, max
    for sl in panel.findChildren(QSlider) + panel.findChildren(QDial):
        if not _alive(sl):
            continue
        lo, hi = sl.minimum(), sl.maximum()
        for v in (lo, (lo + hi) // 2, hi):
            if not _alive(sl):
                break
            sl.setValue(v)
            w._tick()
            fired[0] += 1
    # checkboxes / radios: flip and flip back
    for ck in panel.findChildren(QCheckBox) + panel.findChildren(QRadioButton):
        if not _alive(ck) or not ck.isEnabled():
            continue
        was = ck.isChecked()
        ck.toggle()
        w._tick()
        if _alive(ck) and ck.isChecked() == (not was):
            ck.toggle()                           # restore
            w._tick()
        fired[0] += 2


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None
    books.save(books.from_text(
        "The night was calm. A soft wind moved the trees. She walked home. "
        "The stars were bright. All was quiet now.", "A Quiet Night", "Tester"))

    from vesper.window import MainWindow
    w = MainWindow()
    w.face.set_use_cat(True)

    fired = [0]
    for nm in modes.names():
        w.apply_mode(nm)
        before = fired[0]
        _drive_panel(w, fired)
        assert not _SLOT_ERRORS, ("%s panel raised a (swallowed) slot error: %s"
                                  % (nm, _SLOT_ERRORS))
        print("ok: %-10s panel -- drove %d controls cleanly" % (nm, fired[0] - before))

    assert fired[0] >= 40, ("expected to drive many panel controls", fired[0])
    print("ok: %d side-panel controls fired across all workspaces, no slot errors"
          % fired[0])
    print("PASS: panel drive (every workspace's combos / sliders / checkboxes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
