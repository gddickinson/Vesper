"""Offline render test for the "Snowfall" sleep scene (vesper/scene_snow.py).

Verifies it is registered + selectable, draws without error in the running and
idle states, paints soft (warm-grey, not cold-blue) snow on a dark sky, and
animates over time. Renders to an offscreen QImage and saves a PNG to eyeball.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtGui import QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from vesper import scenes  # noqa: E402

W, H = 480, 360


def _ctx(running=True, vol=0.8, t=6.0):
    return {"volume": vol, "airflow": 0.3, "phase": "inhale", "cycle_frac": 0.4,
            "remaining": 2.0, "label": "Breathe in", "t": t, "prog": 0.3,
            "running": running, "subtitle": "", "status": "", "hint": ""}


def _render(scene, ctx):
    img = QImage(W, H, QImage.Format.Format_RGB32)
    img.fill(0)
    p = QPainter(img)
    scene.draw(p, W, H, ctx)
    p.end()
    return img


def _count(img, pred):
    n = 0
    for y in range(0, H, 6):
        for x in range(0, W, 6):
            if pred(img.pixelColor(x, y)):
                n += 1
    return n


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None

    assert "snow" in scenes.names(), scenes.names()
    scene = scenes.make("snow")
    assert scene.name == "snow"
    print("ok: registered + selectable as 'snow'")

    img = _render(scene, _ctx(running=True))
    snow = _count(img, lambda c: c.red() > 150 and c.green() > 150 and c.blue() > 150)
    assert snow >= 6, f"expected soft snow pixels, got {snow}"
    # warm-grey snow, not a cold-blue wash: no bright pixel where blue dominates red
    cold = _count(img, lambda c: c.blue() > 150 and c.blue() > c.red() + 30)
    assert cold == 0, f"snow should be warm-grey, not cold blue, got {cold}"
    print(f"ok: running render paints soft snow ({snow} samples), warm-grey (0 cold)")

    _render(scenes.make("snow"), _ctx(running=False))      # idle must be safe
    a = _render(scene, _ctx(t=0.0))
    b = _render(scene, _ctx(t=9.0))
    assert a.constBits() != b.constBits(), "the snow should animate over time"
    print("ok: idle render safe; the scene animates")

    out = os.path.join(os.environ.get("TMPDIR", "/tmp"), "vesper_snow.png")
    _render(scene, _ctx(t=6.0)).save(out)
    print(f"ok: wrote a preview PNG -> {out}")
    print("PASS: Snowfall scene")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
