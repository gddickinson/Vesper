"""Offline regression: a scene/overlay fault must never escape paintEvent.

The visual paintEvent runs from the Qt event loop -- NOT inside the _tick
try/except -- so if a per-frame scene or overlay (weather / warm dimming /
captions / hourglass) ever raises, the exception escapes with the QPainter still
active. The next repaint then hits "QPaintDevice: Cannot destroy paint device
that is being painted" and the app hard-crashes -- the worst case during an
overnight sleep session.

The fix wraps both paintEvents (viz.VizWidget, face.FaceWidget) in a
try/finally that always p.end()s, and guards the scene + overlays so a fault is
caught and logged once (``_warned``) instead of escaping. This test forces an
overlay/scene to raise during an offscreen paint and asserts the fault is
contained (``_warned`` flips, no exception escapes) and that painting keeps
working afterwards.  Offscreen Qt, no audio.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from vesper import viz, face  # noqa: E402


def _boom(*_a, **_k):
    raise RuntimeError("forced per-frame fault")


def main():
    app = QApplication.instance() or QApplication([])

    # --- VizWidget: overlay fault and scene fault are both contained ----------
    w = viz.VizWidget()
    w.resize(400, 300)

    orig_caption = viz.captions.paint_caption
    viz.captions.paint_caption = _boom            # an overlay raises every frame
    try:
        w.grab()                                  # forces a synchronous paintEvent
        assert w._warned, "viz overlay fault was not caught inside paintEvent"
    finally:
        viz.captions.paint_caption = orig_caption
    print("ok: viz overlay fault is contained (painter still terminated)")

    w._warned = False
    orig_draw = w._scene.draw
    w._scene.draw = _boom                          # the scene itself raises
    try:
        w.grab()
        assert w._warned, "viz scene fault was not caught inside paintEvent"
    finally:
        w._scene.draw = orig_draw
    # painter was properly ended each time -> a clean paint still works
    pm = w.grab()
    assert not pm.isNull(), "viz could not paint after a contained fault"
    print("ok: viz scene fault is contained; painting recovers")

    # --- FaceWidget: same guarantee for the talking-head paint path ----------
    f = face.FaceWidget()
    f.resize(400, 300)
    orig_fcap = face.captions.paint_caption
    face.captions.paint_caption = _boom
    try:
        f.grab()
        assert f._warned, "face overlay fault was not caught inside paintEvent"
    finally:
        face.captions.paint_caption = orig_fcap
        f.stop()                                   # stop the render worker thread
    print("ok: face overlay fault is contained")

    print("PASS: paintEvent fault-containment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
