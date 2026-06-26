"""Window-level regression for the storyteller's character + costume follow.

When "Character follows the story" is on, `win_story._apply_story_character` should
set BOTH the fitting character AND a fitting costume for the scene (a cosy cat in a
chef hat for a baking tale), then restore the user's own character + costume when a
later scene has no themed costume -- and fully on `_restore_user_character`. The
matcher itself is unit-tested elsewhere; this checks the *window wiring* that ties
`story_char.costume_for_scene` to `face.set_costume`, which the menu-driven GUI
drive does not exercise. Offscreen Qt; no audio device.
"""
import os
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402

from vesper import story_char  # noqa: E402


def main():
    app = QApplication.instance() or QApplication([])
    assert app is not None

    from vesper.window import MainWindow
    w = MainWindow()
    w.face.set_use_cat(True)                       # the costume-follow only runs on the 2D face

    # the user's own pick (must be restored after any story-driven swap)
    w.set_character("Dog")
    w.set_costume("Nightcap")
    assert w.face.character() == "Dog" and w.face.costume() == "Nightcap"

    w._story_char_follow = True                    # the opt-in toggle (default off)

    # sanity: the mapper still picks what we expect for these scenes
    assert story_char.char_for_scene("The Night Baker") == "Cat"
    assert story_char.costume_for_scene("The Night Baker") == "Chef Hat"

    # a baking tale -> a cosy cat in a chef hat (character + costume both follow)
    w._story_scene = "The Night Baker"
    w._apply_story_character()
    assert w.face.character() == "Cat", ("baking tale should pick the Cat",
                                         w.face.character())
    assert w.face.costume() == "Chef Hat", ("baking tale should add the Chef Hat",
                                            w.face.costume())
    print("ok: a baking tale dresses the storyteller as a cat in a chef hat")

    # a later, un-themed scene -> the themed costume reverts to the user's own,
    # the character follows the new scene (Bear for hibernation)
    assert story_char.costume_for_scene("Hibernation") == "None"
    w._story_scene = "Hibernation"
    w._apply_story_character()
    assert w.face.character() == "Bear", w.face.character()
    assert w.face.costume() == "Nightcap", ("un-themed scene must restore the user's "
                                            "costume", w.face.costume())
    print("ok: an un-themed scene reverts the costume to the user's own")

    # leaving the story-follow restores the user's character + costume entirely
    w._restore_user_character()
    assert w.face.character() == "Dog", w.face.character()
    assert w.face.costume() == "Nightcap", w.face.costume()
    print("ok: restoring puts the user's own character + costume back")

    # with the toggle OFF, a scene must not change anything
    w._story_char_follow = False
    w._story_scene = "The Night Baker"
    w._apply_story_character()
    assert w.face.character() == "Dog" and w.face.costume() == "Nightcap", \
        "follow is off -> the storyteller must not touch the user's look"
    print("ok: with follow off, the storyteller leaves the user's look alone")

    print("PASS: story-driven character + costume follow (window wiring)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
