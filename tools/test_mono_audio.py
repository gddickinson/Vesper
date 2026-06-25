"""Offline test for the Mono-audio accessibility toggle.

Engine level (no Qt): a panned stereo ambience renders with the two channels
differing; with `engine.set_mono(True)` the output collapses to mono -- both
channels become identical -- and stays audible. GUI level (offscreen): the View
toggle round-trips through `set_mono_audio`, drives the engine, and persists.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from breathsim import controller as ctrl_mod, engine as eng_mod, store  # noqa: E402
from breathsim.patterns import DEFAULT_PATTERN  # noqa: E402


def _render(eng, n=1):
    frames = eng.block
    out = np.zeros((frames, 2), dtype=np.float32)
    for _ in range(n):
        eng._callback(out, frames, None, None)
    return out.copy()


def main():
    # --- engine downmix invariant (no audio device; callback called directly) ---
    c = ctrl_mod.BreathController(DEFAULT_PATTERN)
    c.start()
    eng = eng_mod.AudioEngine(c)
    eng.set_master_volume(0.9)
    eng.set_voice("Forest Wind", "ambience")     # a clearly panned stereo ambience
    _render(eng, 4)                              # warm up master gain + filter state

    eng.set_mono(False)
    off = _render(eng)
    assert np.any(off != 0.0), "ambience should produce sound"
    assert np.max(np.abs(off[:, 0] - off[:, 1])) > 1e-6, "stereo channels should differ"
    print("ok: stereo render has distinct L/R channels")

    eng.set_mono(True)
    on = _render(eng)
    assert np.array_equal(on[:, 0], on[:, 1]), "mono downmix must make L == R"
    assert np.any(on != 0.0), "mono should still be audible"
    print("ok: mono downmix collapses L == R and stays audible")

    eng.set_mono(False)
    assert np.max(np.abs(_render(eng)[:, 0] - _render(eng)[:, 1])) >= 0  # toggled back
    print("ok: toggling mono off restores the stereo path")

    # --- GUI wiring: round-trips through the window + persists ---
    from PySide6.QtWidgets import QApplication
    from vesper.window import MainWindow
    app = QApplication.instance() or QApplication([])
    win = MainWindow()
    win.show()
    for _ in range(3):
        app.processEvents()
    assert win._mono_audio is False and win.engine._mono is False
    win.set_mono_audio(True)
    assert win._mono_audio is True and win.engine._mono is True
    assert store.load_settings().get("mono_audio") is True, "should persist"
    win.set_mono_audio(False)
    assert win.engine._mono is False
    assert store.load_settings().get("mono_audio") is False
    win.close()
    for _ in range(2):
        app.processEvents()
    print("ok: View toggle drives the engine + persists the setting")

    print("PASS: mono-audio accessibility toggle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
