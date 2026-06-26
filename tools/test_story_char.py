"""Offline test for the storyteller's "character follows the story" mapping.

`story_char.char_for_scene(name)` picks a fitting cartoon character for a scene /
lecture so the talking-head can look the part. This checks: every character it can
return is actually registered in the cast; a spread of representative scenes map to
sensible characters (incl. the newer cast members so the map keeps up with the 18
characters); unknown / empty input falls back to the default; and the deliberately
manual-only members (Skull, Woman, Man) are never auto-assigned.

Pure (no Qt) -- story_char is plain data + a string match.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vesper import story_char  # noqa: E402


def main():
    names = {n for n, _ in story_char._THEMES}

    # every theme target + the default is a real, registered character
    from vesper import characters
    registered = set(characters.names())
    for n in names | {story_char.DEFAULT}:
        assert n in registered, ("maps to an unregistered character", n)
    print("ok: every mapped character is registered in the cast")

    # the map now reaches a broad spread of the cast (not just the original 8)
    assert len(names) >= 14, ("character-follow should use most of the cast", len(names))
    for newcomer in ("Sheep", "Chicken", "Robot", "Mouse", "Dog", "Hedgehog",
                     "Panda", "Sloth", "Snowman"):
        assert newcomer in names, ("newer cast member unused: " + newcomer)
    print("ok: %d distinct characters reachable (incl. the newer cast)" % len(names))

    # the sleepy Sloth narrates the explicitly sleep/slow-themed content
    for sleepy in ("How the World Sleeps", "The Sleeping Brain",
                   "How Dolphins Sleep", "Sleep Hypnosis", "A slow afternoon",
                   "The Sloth"):
        assert story_char.char_for_scene(sleepy) == "Sloth", (sleepy, "should be Sloth")
    # ...but its broad triggers (slow/rest) must not steal non-sleepy scenes
    assert story_char.char_for_scene("The Black Forest") == "Bear"
    assert story_char.char_for_scene("The Constellations") == "Owl"
    print("ok: the Sloth gets the sleep/slow themes without stealing others")

    # the Snowman narrates the snow / frost / ice themed content (the Winter's Hush
    # branch + wintry scenes), but must not steal the polar sea or the woodland
    for snowy in ("The First Snow", "Frost", "The Icicle", "The Frozen Lake",
                  "Winter Cabin", "Snowfall", "A blizzard at midnight"):
        assert story_char.char_for_scene(snowy) == "Snowman", (snowy, "-> Snowman")
    assert story_char.char_for_scene("Icebergs") == "Penguin"      # polar sea, not snow
    assert story_char.char_for_scene("The Arctic") == "Penguin"
    assert story_char.char_for_scene("A Winter's Tale") == "Snowman"   # winter -> Snowman
    assert story_char.char_for_scene("Hibernation") == "Bear"          # bear winter kept
    assert story_char.char_for_scene("The Black Forest") == "Bear"     # woodland kept
    assert story_char.char_for_scene("Riverside") == "Duckling"        # lake/river kept
    print("ok: the Snowman gets snow/frost/ice without stealing sea/forest/river")

    # representative scenes / lecture names map to a fitting character
    cases = {
        "Seaside": "Penguin",
        "Riverside": "Duckling",
        "The Shepherd's Night Watch": "Sheep",
        "Lullabies of the World": "Sheep",
        "Sunrise over the farm": "Chicken",
        "Great Train Journeys": "Robot",
        "The Caravan": "Dog",
        "The Night Watchman": "Dog",
        "Small Wonders": "Mouse",
        "Quiet Cafe": "Cat",
        "The Night Baker": "Cat",
        "The Constellations": "Owl",
    }
    for scene, want in cases.items():
        got = story_char.char_for_scene(scene)
        assert got == want, (scene, "->", got, "expected", want)
    print("ok: representative scenes map to fitting characters")

    # fallbacks + manual-only members
    assert story_char.char_for_scene("") == story_char.DEFAULT
    assert story_char.char_for_scene("a topic with no theme word xyzzy") == story_char.DEFAULT
    for manual in ("Skull", "Woman", "Man"):
        assert manual not in names, (manual + " should stay a manual-only pick")
    print("ok: empty/unknown -> default; Skull/Woman/Man stay manual-only")

    print("PASS: storyteller character-follow map")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
