"""Read mode defaults: narrator-only audio + a normal awake-reading pace.

User request: starting a Read session should give **just the voice** -- no breath
bed, ambience or effects -- and read at a normal pace (short gaps), with the slow
sleep-style spacing left as an opt-in toggle. Asserts the engine slot targets are
muted on enter_read (the breath VISUAL still runs), the Sound-menu checkmarks
reflect that, the default pace tuple is the short one, and that toggling "Longer
pauses" restores the slow spacing. Switching to another mode restores the breath
bed. Offscreen Qt; no audio device.
"""
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from breathsim import books  # noqa: E402


def _slot_targets(engine, slot):
    return [ly.target for ly in engine.layers if ly.slot == slot]


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None
    b = books.from_text(
        "The night was calm and deep. A gentle wind moved through the trees. "
        "She walked slowly home. The stars were bright and still.", "Quiet", "T")
    books.save(b)

    from vesper.window import MainWindow
    w = MainWindow()

    # --- entering Read mutes the breath bed / ambience / effects ----------
    w.apply_mode("Read")
    assert w.current_mode == "Read"
    for slot in ("primary", "ambience", "effects"):
        tg = _slot_targets(w.engine, slot)
        assert all(t == 0.0 for t in tg), (slot, "should be muted in Read", tg)
    # the Sound > Background-sounds checkmarks reflect the mute
    for slot in ("primary", "ambience", "effects"):
        a = w._bg_acts.get(slot)
        assert a is not None and not a.isChecked(), (slot, "menu should show off")
    print("ok: Read starts narrator-only (breath/ambience/effects muted + reflected)")

    # the breath VISUAL still runs: a Play starts the controller (scene animates)
    w.toggle_transport()
    assert w.controller.running, "Read still runs the breath clock for the visual"
    assert w._reading, "main Play narrates the book"
    w.toggle_transport()
    w.reset()

    # --- default pace is the short, awake one; toggle restores the slow one
    assert w._read_long is False, "Read should default to normal (short) pacing"
    import vesper.win_read as wr
    # capture the pause tuple start_reading would use, both ways
    src = open(wr.__file__).read()
    assert "(700, 1600) if self._read_long else (250, 750)" in src, \
        "expected normal=(250,750), sleep=(700,1600) pacing"
    w.set_reading_pauses(True)
    assert w._read_long is True, "the Longer-pauses toggle should flip the flag"
    w.set_reading_pauses(False)
    print("ok: default pace short (250/750); 'Longer pauses' restores slow (700/1600)")

    # --- leaving Read restores the breath bed (other modes audible) -------
    w.apply_mode("Meditate")
    tg = _slot_targets(w.engine, "primary")
    assert tg and any(t > 0.0 for t in tg), ("breath bed restored outside Read", tg)
    for slot in ("primary", "ambience", "effects"):
        a = w._bg_acts.get(slot)
        assert a is not None and a.isChecked(), (slot, "menu back on outside Read")
    print("ok: leaving Read restores the breath bed + menu checkmarks")

    print("PASS: Read-mode narrator-only + normal-pace defaults")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
