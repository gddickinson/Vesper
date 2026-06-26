"""Deep GUI drive-test: start a real session in EVERY mode and assert that the
mode actually does its defining thing -- not just that nothing throws.

This is the regression that catches "I pressed Play in Read mode and just got
breathing": the main transport must start the **novel narration** in Read, arm
the **storyteller** in Sleep, and run the **breath session** (with no narration)
in Meditate / Breathwork / Chant / Sing / Relax. It then ticks the ~40fps loop in
each mode (so a bad per-mode frame is caught), pauses (and confirms reading stops
in Read), and finally smoke-opens every menu dialog + editor (with modal `exec()`
neutralised) so a broken dialog is caught too. Offscreen Qt; no audio device.
"""
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox  # noqa: E402

from breathsim import books, modes  # noqa: E402

# Neutralise modal dialogs so opening one never blocks the headless run.
QDialog.exec = lambda self: 0
QMessageBox.exec = lambda self: 0

# Qt swallows an exception raised inside a slot and routes it to sys.excepthook
# (it does NOT propagate to the trigger() caller). Record those so a handler that
# blows up -- e.g. touching a deleted QAction after a menu rebuild -- still FAILS
# this test instead of just printing a traceback nobody reads.
_SLOT_ERRORS = []
_real_hook = sys.excepthook


def _hook(exc_type, exc, tb):
    _SLOT_ERRORS.append("%s: %s" % (exc_type.__name__, exc))
    _real_hook(exc_type, exc, tb)


sys.excepthook = _hook


def _make_book():
    b = books.from_text(
        "The night was calm and deep. A gentle wind moved through the tall trees. "
        "She walked slowly along the quiet lane toward home. Far overhead the "
        "stars were bright and still. Nothing stirred, and all was peaceful now. "
        "She paused at the gate to listen. The world was asleep around her.",
        "A Quiet Night", "Tester")
    books.save(b)
    return b.id


def _drive_mode(w, name):
    w.apply_mode(name)
    assert w.current_mode == name, ("apply_mode did not take", name)
    assert w.panel is not None, ("panel missing after", name)

    # start a session via the MAIN transport (the big Play / Space)
    w.toggle_transport()
    assert w.controller.running, (name, "session did not start on Play")
    for _ in range(6):                          # drive the ~40fps loop a little
        w._tick()

    if name == "Read":
        assert w._reading, "Read mode: main Play must start the novel narration"
        assert w.read_pane.isVisibleTo(w) or w._read_along, "Read pane should show"
    elif name == "Sleep":
        assert w._story_scene, "Sleep mode: the storyteller scene must be armed"
        assert not getattr(w, "_reading", False), "Sleep should not be book-reading"
    else:
        assert not getattr(w, "_reading", False), (name, "should not be reading")

    # pause via the main transport
    w.toggle_transport()
    assert not w.controller.running, (name, "session did not pause")
    if name == "Read":
        assert not w._reading, "Read mode: pause must stop the narration"
    w.reset()


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None
    _make_book()                                # so Read mode has something to read

    from vesper.window import MainWindow
    w = MainWindow()
    w.face.set_use_cat(True)                     # exercise the 2D face path

    names = modes.names()
    for need in ("Meditate", "Breathwork", "Chant", "Sing", "Relax", "Sleep", "Read"):
        assert need in names, ("missing mode", need)

    for nm in names:
        _drive_mode(w, nm)
        print("ok: %-10s starts + does its thing + pauses cleanly" % nm)
    print("ok: every mode drives correctly (incl. Read narrates on the main Play)")

    # smoke-open every menu dialog + editor (modal exec() neutralised above)
    from vesper import dialogs, pattern_editor, presets, voice_editor
    from vesper import booklib, onboarding, reader
    openers = [
        ("Stats", dialogs.open_stats), ("Mixer", dialogs.open_mixer),
        ("About", dialogs.open_about), ("Shortcuts", dialogs.open_shortcuts),
        ("Story Library", dialogs.open_story_library),
        ("Pattern Editor", pattern_editor.open_pattern_editor),
        ("Presets", presets.open_presets),
        ("Voice Editor", voice_editor.open_editor),
        ("Onboarding", onboarding.open_onboarding),
        ("Library", booklib.open_library),
        ("Reader", reader.open_reader),
    ]
    w.apply_mode("Meditate")                     # a neutral mode for dialog smoke
    failures = []
    for label, fn in openers:
        try:
            fn(w)
        except Exception as e:                   # noqa: BLE001 -- report, don't hide
            import traceback
            failures.append((label, repr(e)))
            traceback.print_exc()
    assert not failures, ("dialogs/editors raised on open: " + str(failures))
    print("ok: all %d menu dialogs + editors open without error" % len(openers))

    # rebuild the native menu bar (every action wired) -- must not raise
    from vesper import menus
    menus.build(w)
    print("ok: menu bar rebuilds cleanly")

    # drive EVERY checkable menu action through its real handler: the Sound /
    # View / Session toggles plus the character / costume / scene / face-style
    # radio selections. Triggering fires the wired callback with the correct
    # argument -- so a broken toggle or selection is caught here. (Non-checkable
    # actions open dialogs / file pickers, already covered / skipped.) Several
    # handlers REBUILD the menu bar, so we snapshot menu *paths* and re-resolve
    # each action live before triggering -- robust to those rebuilds.
    def _checkable_paths(menubar):
        paths = []

        def walk(menu, prefix):
            for a in menu.actions():
                sub = a.menu()
                if sub is not None:
                    walk(sub, prefix + [a.text()])
                elif a.isCheckable() and a.text():
                    paths.append(prefix + [a.text()])
        for a in menubar.actions():
            if a.menu() is not None:
                walk(a.menu(), [a.text()])
        return paths

    def _resolve(menubar, path):
        *titles, leaf = path
        actions = menubar.actions()
        for t in titles:
            nxt = next((a.menu() for a in actions
                        if a.menu() is not None and a.text() == t), None)
            if nxt is None:
                return None
            actions = nxt.actions()
        return next((a for a in actions
                     if a.isCheckable() and a.text() == leaf), None)

    paths = _checkable_paths(w.menuBar())
    assert len(paths) >= 20, ("expected many checkable menu actions", len(paths))
    act_fail = []
    fired = 0
    for path in paths:
        a = _resolve(w.menuBar(), path)          # re-find live (survives rebuilds)
        if a is None:
            continue
        try:
            a.trigger()                          # fires the real handler with its arg
            w._tick()                            # let one frame absorb the change
            fired += 1
        except Exception as e:                   # noqa: BLE001
            import traceback
            act_fail.append((" > ".join(path), repr(e)))
            traceback.print_exc()
    assert not act_fail, ("checkable menu actions raised: " + str(act_fail))
    assert not _SLOT_ERRORS, ("unhandled slot exceptions during the GUI drive "
                              "(Qt swallowed these): " + str(_SLOT_ERRORS))
    print("ok: %d/%d checkable menu actions fire cleanly, no swallowed slot errors "
          "(toggles + character/costume/scene/style)" % (fired, len(paths)))

    print("PASS: deep GUI drive (every mode + every dialog + every toggle)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
