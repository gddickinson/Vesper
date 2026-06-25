"""Offline render test for the "Lanterns" sleep scene (vesper/scene_lanterns.py).

Verifies it is registered + selectable (`scenes.names()` / `make`), draws without
error in both the running and idle states, and actually paints warm amber light
(low-blue, melatonin-friendly) onto the dark sky. Renders to an offscreen QImage
and also saves a PNG to the scratchpad to eyeball.
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


def _warm_pixels(img):
    """Count clearly-warm (amber) pixels: red dominant over blue, and bright."""
    n = 0
    for y in range(0, H, 6):
        for x in range(0, W, 6):
            c = img.pixelColor(x, y)
            if c.red() > 110 and c.red() > c.blue() + 35:
                n += 1
    return n


def _bright_blue_pixels(img):
    """Count bright cool/blue pixels -- a melatonin-friendly scene should have ~none."""
    n = 0
    for y in range(0, H, 6):
        for x in range(0, W, 6):
            c = img.pixelColor(x, y)
            if c.blue() > 120 and c.blue() > c.red() + 30:
                n += 1
    return n


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None

    # registered + selectable
    assert "lanterns" in scenes.names(), scenes.names()
    scene = scenes.make("lanterns")
    assert scene.name == "lanterns"
    print("ok: registered + selectable as 'lanterns'")

    # running render: draws, not uniform, and shows warm lantern light
    img = _render(scene, _ctx(running=True))
    warm = _warm_pixels(img)
    assert warm >= 6, f"expected warm lantern pixels, got {warm}"
    # melatonin-friendly: the scene is warm/low-blue -- no bright cool/blue region
    blue = _bright_blue_pixels(img)
    assert blue == 0, f"a low-blue sleep scene should have no bright-blue pixels, got {blue}"
    print(f"ok: running render draws warm light ({warm} amber samples), low-blue (0 cool)")

    # idle ("Ready") render must not crash either
    _render(scenes.make("lanterns"), _ctx(running=False))
    print("ok: idle render is safe")

    # a couple of animation steps differ (it actually animates)
    a = _render(scene, _ctx(t=0.0))
    b = _render(scene, _ctx(t=9.0))
    assert a.constBits() != b.constBits()
    print("ok: the scene animates over time")

    out = os.path.join(os.environ.get("TMPDIR", "/tmp"), "vesper_lanterns.png")
    _render(scene, _ctx(t=6.0)).save(out)
    print(f"ok: wrote a preview PNG -> {out}")
    print("PASS: Lanterns scene")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
