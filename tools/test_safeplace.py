"""Offline test for the "A Safe and Peaceful Place" guided-imagery session.

Checks the session yields well-formed narrator units that build a safe place and
move through the senses (see / hear / feel / smell), keeps its safety framing,
runs endlessly into the shared sleep drift, honours the guidance flag, uses a
registered ambience, and is wired into the storyteller dispatch (extra_names /
ambience_for / story_units).  Pure, no Qt, no audio.
"""
import itertools
import os
import random
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import safeplace, stories, voices  # noqa: E402


def _take(gen, n):
    return list(itertools.islice(gen, n))


def main():
    units = _take(safeplace.units(random.Random(1)), 60)
    assert all(isinstance(u, dict) and u["text"] and u["pause"] > 0 for u in units)
    blob = " ".join(u["text"].lower() for u in units)
    # builds a place, then engages each sense in turn
    for cue in ("peaceful place", "look around", "sounds of this place",
                "warmth", "breathe in"):
        assert cue in blob, f"missing the sensory cue '{cue}'"
    # the safety framing -- the heart of the technique
    for safe in ("entirely safe", "you belong here", "no worry can follow"):
        assert safe in blob, f"missing the safety line '{safe}'"
    print("ok: builds a safe place + engages sight/sound/touch/scent")

    # the breath-paced guide units appear only with guidance on
    g_on = _take(safeplace.units(guidance=True), 16)
    g_off = _take(safeplace.units(guidance=False), 16)
    assert any(u.get("kind") == "guide" for u in g_on)
    assert not any(u.get("kind") == "guide" for u in g_off)
    print("ok: guidance flag adds/removes the breath-paced breaths")

    # it never runs out (endless soft drift into sleep, like the hypnosis tail)
    deep = _take(safeplace.units(random.Random(2)), 400)
    assert len(deep) == 400 and all(d["text"] for d in deep)
    print("ok: runs endlessly into the shared sleep drift")

    # wired into the storyteller dispatch + a registered ambience
    assert safeplace.NAME in stories.extra_names()
    assert stories.ambience_for(safeplace.NAME) == safeplace.AMBIENCE
    assert voices.get_voice(safeplace.AMBIENCE) is not None, "ambience not registered"
    via = _take(stories.story_units(safeplace.NAME, random.Random(3)), 8)
    assert via and via[0]["text"], "story_units should dispatch to safeplace"
    print("ok: extra_names + ambience_for (registered) + story_units dispatch")

    print("PASS: A Safe and Peaceful Place session")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
