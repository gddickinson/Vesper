"""Offline test for the costume registry + the story->costume matcher.

Every registered costume (including the new profession + sci-fi modules) must draw
over a Head anchor without error and actually paint something; the new translucent
Space Helmet must keep the face area visible; and ``story_char.costume_for_scene``
must only ever return a registered costume, fire on the right themed scenes, and --
critically -- NOT false-fire (Sacred Spaces is not a space helmet, a Marsh is not a
Martian, the Shepherd's Night Watch is not a policeman). Offscreen Qt; no audio.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtGui import QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from vesper import char_anim, char_base as B, characters, story_char  # noqa: E402

W = 300


def _anim(**kw):
    a = char_anim.Anim()
    a.breath = kw.get("breath", 0.6)
    for k, v in kw.items():
        setattr(a, k, v)
    return a


def _painted(img):
    seen = set()
    for y in range(0, W, 6):
        for x in range(0, W, 6):
            seen.add(img.pixelColor(x, y).rgb())
    return len(seen) > 2


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None

    costumes = characters.costume_names()
    # the new pieces are all present in the single merged registry
    for need in ("Space Helmet", "Sci-fi Visor", "Alien Antennae", "Robot Aerial",
                 "Police Cap", "Fire Helmet", "Nurse Cap", "Head Mirror",
                 "Chef Hat", "Hard Hat", "Graduation Cap"):
        assert need in costumes, ("costume not registered: " + need)
    assert len(costumes) >= 28, ("expected the expanded costume set", len(costumes))
    print("ok: %d costumes registered (incl. professions + sci-fi)" % len(costumes))

    # every costume draws over a Head without error, for a few anim states
    hd = B.Head(W / 2, W * 0.5, W * 0.22, W * 0.5 - W * 0.22)
    for name in costumes:
        for a in (_anim(), _anim(breath=1.0, sway=0.04), _anim(t=2.0, mouth=0.5)):
            img = QImage(W, W, QImage.Format.Format_RGB32)
            img.fill(0)
            p = QPainter(img)
            characters.draw_costume(p, hd, name, a, "#86e6bf")
            p.end()
            if name != "None":
                assert _painted(img), (name, "drew nothing")
    print("ok: every costume draws over a Head (3 states) without error")

    # the Space Helmet is translucent -- the face area under the dome stays visible
    # (draw a bright character, then the helmet on top; the centre must not go dark)
    img = QImage(W, W, QImage.Format.Format_RGB32)
    img.fill(0)
    p = QPainter(img)
    head = characters.get("Cat").draw(p, W, W, _anim(hue="#86e6bf"))
    characters.draw_costume(p, head, "Space Helmet", _anim(), "#7fd0ff")
    p.end()
    cy = int(head.cy)
    bright = max(img.pixelColor(int(head.cx), cy).lightness(),
                 img.pixelColor(int(head.cx - head.R * 0.3), cy).lightness())
    assert bright > 60, ("Space Helmet hides the face (too dark under the dome)", bright)
    print("ok: Space Helmet stays translucent (face visible under the dome)")

    # the matcher only ever returns a registered costume
    reg = set(costumes)
    for c, _ in story_char._COSTUME_THEMES:
        assert c in reg, ("matcher returns an unregistered costume: " + c)

    # it fires on the right themed scenes...
    want = {
        "The First Bread": "Chef Hat", "The Night Baker": "Chef Hat",
        "Sourdough": "Chef Hat",
        "The Library of Ashurbanipal": "Graduation Cap",
        "The Monastic Scriptorium": "Graduation Cap",
        "Himeji Castle": "Crown", "The Night Watchman": "Police Cap",
        "Earth from Space": "Space Helmet", "The Treasure Fleet": "Pirate Hat",
        "A tale of the firefighter": "Fire Helmet",
        "The Doctor's Round": "Head Mirror",
    }
    for scene, costume in want.items():
        got = story_char.costume_for_scene(scene)
        assert got == costume, (scene, "->", got, "expected", costume)
    print("ok: themed scenes get a fitting costume")

    # ...and must NOT false-fire (the whole point of the =exact / prefix guards)
    for scene in ("Sacred Spaces", "The Hearth", "Hadrian's Wall",
                  "The Shepherd's Night Watch", "Hibernation", "Quiet Cafe"):
        assert story_char.costume_for_scene(scene) == "None", \
            (scene, "wrongly got a costume", story_char.costume_for_scene(scene))
    print("ok: untargeted scenes keep the user's costume (no false-fire)")

    print("PASS: costumes + story->costume matcher")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
