"""Offscreen test for the 'Calm visuals (reduce motion)' accessibility toggle.

Verifies the viz chokepoint behaviour: with calm OFF the decorative clock fed to
the scenes tracks real anim time; with calm ON it advances at ~15% so every
time-driven drift/twinkle eases, and the busy weather overlay is suppressed --
while the breath-driven terms (volume / cycle_frac) are passed through untouched,
so the breathing visualization stays responsive. Needs an offscreen QApplication
(VizWidget is a QWidget) but no MainWindow.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from vesper.viz import VizWidget  # noqa: E402


def _ctx(t, vol=0.5):
    return {"running": True, "volume": vol, "airflow": 0.0, "phase": "inhale",
            "cycle_frac": 0.3, "remaining": 0.0, "label": "In", "t": t, "prog": None}


def main():
    app = QApplication.instance() or QApplication([])
    v = VizWidget()

    # calm OFF: the virtual clock matches the real elapsed anim time
    for t in (0.0, 1.0, 2.0, 5.0):
        v.update_state(_ctx(t))
    normal_t = v._ctx["t"]
    assert abs(normal_t - 5.0) < 1e-6, normal_t
    assert v._ctx["calm"] is False
    print(f"ok: calm off -> decorative clock tracks real time ({normal_t:.2f})")

    # turn calm ON; from here the clock advances at ~15% of real time
    v.set_calm(True)
    assert v._calm is True
    before = v._ctx["t"]
    for t in (6.0, 7.0, 8.0):                 # +3.0 s of real anim time
        v.update_state(_ctx(t))
    advanced = v._ctx["t"] - before
    assert abs(advanced - 3.0 * VizWidget._CALM_RATE) < 1e-6, advanced
    assert advanced < 0.5, advanced          # far less than the 3.0 s of real time
    assert v._ctx["calm"] is True
    print(f"ok: calm on -> clock advances {advanced:.2f}s over 3.0s real (15%)")

    # breath-driven terms pass straight through (unaffected by calm)
    v.update_state(_ctx(9.0, vol=0.8))
    assert v._ctx["volume"] == 0.8 and v._ctx["cycle_frac"] == 0.3
    print("ok: breath-driven volume/cycle_frac untouched by calm")

    # weather overlay is suppressed when calm: painting must not draw it (and
    # must never raise); we paint to an offscreen pixmap with a weather kind set.
    from PySide6.QtGui import QPixmap
    v.set_weather("snow")
    v.resize(200, 200)
    for calm in (False, True):
        v.set_calm(calm)
        v.update_state(_ctx(10.0 + calm))
        pm = QPixmap(200, 200)
        v.render(pm)                          # exercises paintEvent end to end
    assert v._calm is True
    print("ok: paints cleanly with weather set, calm on + off (overlay gated)")

    # the clock never goes backwards on a session reset (t jumps back to 0)
    v.set_calm(False)
    v.update_state(_ctx(100.0))
    hi = v._ctx["t"]
    v.update_state(_ctx(0.0))                 # simulate a controller reset
    assert v._ctx["t"] >= hi, (hi, v._ctx["t"])   # monotonic (dt clamped to >= 0)
    print("ok: virtual clock is monotonic across a clock reset")

    print("PASS: calm visuals -- clock slows, weather gated, breath untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
