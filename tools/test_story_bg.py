"""Offline test for the story backdrop matcher (story_bg.bg_for_text).

The backdrop quietly follows the narrated words (a hearth -> Embers, a night sky
-> Stars, a city street -> City...). The matcher must fire on the real imagery but
NOT on innocent longer words that merely contain a trigger -- the old substring
match wrongly hit "start"/"stared" (Stars), "season" (Underwater), "street"
(Forest, via "tree"!), "cloak" (Forest, via "oak"), "currently" (Underwater). This
checks the intended matches, the false-hit traps, the backdrops are real face_bg
names, and the per-scene base. Offscreen-free; pure string logic.
"""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"   # face_bg import may touch Qt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vesper import story_bg  # noqa: E402


def main():
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from vesper import face_bg

    # every backdrop a theme can return (and every scene base) is a real face_bg
    valid = set(face_bg.names())
    for name, _ in story_bg._THEMES:
        assert name in valid, ("theme maps to unknown backdrop", name)
    for base in list(story_bg._SCENE_BASE.values()) + [story_bg.DEFAULT_BASE]:
        assert base in valid, ("scene base is unknown backdrop", base)
    print("ok: every backdrop name is a registered face_bg")

    # real imagery still fires the right backdrop
    good = {
        "the hearth glows with warm firelight": "Embers",
        "a single candle on the sill": "Embers",
        "the whole night sky full of stars": "Stars",
        "the moon rises over the hill": "Stars",
        "rain falls softly on the roof": "Rain",
        "snow drifts past the window": "Rain",  # 'snow' -> Rain before 'window' -> City
        "waves roll in from the sea": "Underwater",
        "a quiet stream in the wood": "Underwater",  # 'stream' (Underwater) leads 'wood'
        "tall pine trees in the forest": "Forest",
        "an oak at the meadow's edge": "Forest",
        "down the narrow city street": "City",
        "a lamplit cafe on the square": "City",
    }
    for line, want in good.items():
        got = story_bg.bg_for_text(line)
        assert got == want, (line, "->", got, "expected", want)
    print("ok: %d imagery lines map to the right backdrop" % len(good))

    # the false-hit traps must NOT fire (these are the substring bugs)
    traps = {
        "the story starts now": None,          # 'start' is not 'star'
        "she stared into the dark": None,      # 'stared' is not 'star'
        "the season was changing": None,       # 'season' is not 'sea'
        "down the busy street": "City",        # 'street' must be City, not Forest via 'tree'
        "he pulled his cloak tight": None,     # 'cloak' is not 'oak'
        "currently she was resting": None,     # 'currently' is not 'current'
        "the plane flew overhead": None,       # 'plane' is not 'lane'
        "nothing left to do tonight": None,    # purely abstract
    }
    for line, want in traps.items():
        got = story_bg.bg_for_text(line)
        assert got == want, ("trap", line, "->", got, "expected", want)
    print("ok: substring false-hit traps no longer fire (start/season/street/cloak/...)")

    # per-scene base + empty input
    assert story_bg.bg_for_text("") is None
    assert story_bg.base_for_scene("Rainy Cottage") == "Rain"
    assert story_bg.base_for_scene("an unknown scene") == story_bg.DEFAULT_BASE
    print("ok: empty -> None; scene bases resolve")

    print("PASS: story backdrop matcher")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
