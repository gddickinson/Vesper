"""Offline render test for the whole 2D character cast (vesper/characters).

Every character must register, draw without error into a QPainter for a range of
animation states (idle / breathing / yawning / blinking / tilted), paint
something (not a blank frame), return a valid Head anchor for costume
attachment, and carry a per-character voice profile. Catches a character that
crashes or no-ops. Renders the newest member (Sloth) to a PNG to eyeball.
Offscreen Qt; no audio.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtGui import QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from vesper import char_anim, char_voice, characters  # noqa: E402

W, H = 320, 320


def _anim(**kw):
    a = char_anim.Anim()
    a.breath = kw.get("breath", 0.6)
    a.hue = kw.get("hue", "#86e6bf")
    a.smile = kw.get("smile", 0.2)
    for k, v in kw.items():
        setattr(a, k, v)
    return a


_STATES = [_anim(), _anim(breath=1.0, smile=0.6), _anim(mouth=0.5, blink=0.8),
           _anim(tilt=0.3, sway=0.03, bob=-0.04), _anim(breath=0.0, blink=1.0)]


def _nonblank(img):
    seen = set()
    for y in range(0, H, 8):
        for x in range(0, W, 8):
            seen.add(img.pixelColor(x, y).rgb())
            if len(seen) > 3:
                return True
    return False


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None

    names = characters.names()
    assert "Sloth" in names, names
    print("ok: cast of %d incl. Sloth" % len(names))

    for nm in names:
        ch = characters.get(nm)
        for a in _STATES:
            img = QImage(W, H, QImage.Format.Format_RGB32)
            img.fill(0)
            p = QPainter(img)
            head = ch.draw(p, W, H, a)
            p.end()
            assert head is not None and head.R > 0, (nm, "bad Head", head)
            assert _nonblank(img), (nm, "drew a blank frame")
        # every character has a voice profile (slow rate for the sleepy ones)
        v = char_voice.get(nm)
        assert v.rate > 0 and v.hue.startswith("#"), (nm, v)
    print("ok: every character draws (5 states), returns a Head, has a voice")

    # the Sloth is slow + dreamy, and we eyeball one render
    assert char_voice.get("Sloth").rate <= 0.85, "the Sloth should speak slowly"
    img = QImage(420, 420, QImage.Format.Format_RGB32)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    characters.get("Sloth").draw(p, 420, 420, _anim(breath=0.7, smile=0.4,
                                                     hue="#e8c98a"))
    p.end()
    out = os.path.join(os.environ.get("TMPDIR", "/tmp"), "vesper_sloth.png")
    img.save(out)
    print("ok: Sloth is slow; wrote a preview PNG -> %s" % out)

    print("PASS: character cast")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
