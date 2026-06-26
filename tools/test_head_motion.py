"""Offline test for the 3D head's natural idle motion.

The talking-head now tilts side-to-side (roll), lifts its chin now and then, and
drifts gently in yaw/pitch on top of the breath nod -- eased toward stillness as a
session winds down and softened under the reduce-motion accessibility flag. This
checks that `FaceWidget.set_state` drives a real, time-varying head **roll** (which
the GPU rotation now honours), that the wind-down and reduce-motion both damp it,
and that nothing throws. Skips cleanly when faceView isn't installed.

Offscreen Qt; no audio.
"""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from vesper.face import FaceWidget
    f = FaceWidget()
    if not f._faceview_ok:
        print("ok: faceView not installed -- head-motion test skipped")
        return 0

    def sample(t, prog=0.0, calm=False):
        f._calm_anim = calm
        f.set_state(0.5, t, prog, mouth=0.0, phase="inhale")
        p = f._params
        return getattr(p, "roll", 0.0), getattr(p, "pitch", 0.0), getattr(p, "yaw", 0.0)

    # roll is driven and varies over time (a real side-to-side tilt, not constant)
    rolls = [sample(t)[0] for t in range(0, 80, 2)]
    rng = max(rolls) - min(rolls)
    assert rng > 0.02, ("head roll should vary with time", rng)
    assert all(abs(r) < 0.5 for r in rolls), "roll stays gentle"
    print("ok: head rolls side-to-side over time (range %.3f rad)" % rng)

    # pitch and yaw also drift (more than a perfectly still head)
    pitches = [sample(t)[1] for t in range(0, 80, 2)]
    yaws = [sample(t)[2] for t in range(0, 80, 2)]
    assert max(pitches) - min(pitches) > 0.01 and max(yaws) - min(yaws) > 0.01
    print("ok: pitch + yaw drift naturally")

    # reduce-motion shrinks the idle head motion
    amp_full = max(abs(sample(t, calm=False)[0]) for t in range(0, 80, 2))
    amp_calm = max(abs(sample(t, calm=True)[0]) for t in range(0, 80, 2))
    assert amp_calm < amp_full, ("reduce-motion should damp idle roll", amp_calm, amp_full)
    print("ok: reduce-motion damps idle head roll (%.3f < %.3f)" % (amp_calm, amp_full))

    # late in a wind-down the head grows stiller, too
    amp_early = max(abs(sample(t, prog=0.0)[0]) for t in range(0, 80, 2))
    amp_late = max(abs(sample(t, prog=1.0)[0]) for t in range(0, 80, 2))
    assert amp_late < amp_early, ("wind-down should still the head", amp_late, amp_early)
    print("ok: head grows stiller late in the wind-down (%.3f < %.3f)"
          % (amp_late, amp_early))

    print("PASS: 3D head idle motion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
