"""Offline test for the talking-Skull character.

Checks the Skull is registered in the character cast with a voice, draws without
error returning a Head anchor, and -- the point of it -- that its **mandible
hinges open** with ``anim.mouth`` (so it lip-syncs the narration): an open jaw
shows a markedly larger dark mouth-cavity than a closed one.

Offscreen Qt; no audio.
"""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _cavity_pixels(mouth):
    """Render the skull at a given mouth-open and count dark mouth-cavity pixels
    in the lower-central face band (between the upper teeth and the chin)."""
    from PySide6.QtGui import QImage, QPainter, QColor
    from vesper import char_skull, char_anim
    W, H = 360, 400
    img = QImage(W, H, QImage.Format.Format_ARGB32)
    img.fill(QColor("#0c1622"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    head = char_skull.Skull().draw(
        p, W, H, char_anim.Anim(t=1.0, breath=0.5, mouth=mouth, hue="#9fe6dc"))
    p.end()
    dark = 0
    for y in range(int(H * 0.55), int(H * 0.82)):
        for x in range(int(W * 0.38), int(W * 0.62)):
            c = img.pixelColor(x, y)
            if c.red() + c.green() + c.blue() < 90:
                dark += 1
    return dark, head


def main():
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from vesper import characters, char_voice

    # registered in the cast + has its own hollow voice
    assert "Skull" in characters.names(), characters.names()
    assert characters.get("Skull").__class__.__name__ == "Skull"
    cv = char_voice.get("Skull")
    assert cv.hue and cv.rate < 1.0, ("skull voice should be slow + tinted", cv)
    print("ok: Skull registered in the cast with a slow, tinted voice")

    closed, head = _cavity_pixels(0.0)
    openj, _ = _cavity_pixels(0.5)
    assert head is not None and head.R > 0, "draw should return a Head anchor"
    assert openj > closed * 2.5 + 200, ("jaw should open with mouth", closed, openj)
    print("ok: mandible hinges open with mouth (cavity %d -> %d px)" % (closed, openj))

    print("PASS: talking Skull character")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
