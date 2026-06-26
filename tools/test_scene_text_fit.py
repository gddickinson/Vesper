"""Offline test: scene overlay text shrinks to fit (no clipping).

The breathing scenes draw a phase label + storyteller **subtitle** centred over
the orb via `scenes._text`. A long subtitle (the spoken story line) used to run
straight off both edges of a narrow scene pane. `_text` now takes a `max_w` and
shrinks the font to fit. This renders the `_text` helper in isolation (on a blank
canvas, so scene stars/motes don't confound the pixel check) and asserts: with
`max_w` no text touches the edges, without it the same line *does* clip (so the
fix is doing real work), and the text still draws either way.

Offscreen Qt; no audio.
"""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# the live subtitle is the spoken line truncated to ~42 chars; use a realistic one
LONG = "and the lanterns drift on the dark water."


def _draw(width, max_w):
    from PySide6.QtGui import QImage, QPainter, QColor
    from vesper import scenes, theme
    W, H = width, 80
    img = QImage(W, H, QImage.Format.Format_ARGB32)
    img.fill(QColor("#000000"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    scenes._text(p, W / 2, H / 2, LONG, theme.TEXT, 30, max_w=max_w)
    p.end()
    return img, W, H


def _edge_pixels(img, W, H):
    cols = list(range(0, 3)) + list(range(W - 3, W))
    n = 0
    for x in cols:
        for y in range(H):
            c = img.pixelColor(x, y)
            if c.red() + c.green() + c.blue() > 200:
                n += 1
    return n


def _any_text(img, W, H):
    n = 0
    for x in range(W // 2 - 20, W // 2 + 20):
        for y in range(H):
            if img.pixelColor(x, y).red() > 80:
                n += 1
    return n


def main():
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])

    W = 300
    # Without a width cap, the long line clips off the edges (the old behaviour).
    img0, W0, H0 = _draw(W, None)
    assert _edge_pixels(img0, W0, H0) > 0, "expected the uncapped line to clip"

    # With max_w it shrinks to fit -- no text at the edges, still drawn in the middle.
    mw = 2 * (W / 2) - 16
    img1, W1, H1 = _draw(W, mw)
    assert _edge_pixels(img1, W1, H1) == 0, "capped subtitle still clips off the edge"
    assert _any_text(img1, W1, H1) > 0, "capped subtitle did not draw"
    print("ok: _text shrinks a long line to fit max_w (uncapped clips, capped does not)")

    print("PASS: scene overlay text fit-to-width")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
