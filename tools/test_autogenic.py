"""Offline test for the Autogenic Training guided session (breathsim/autogenic).

Checks the session yields well-formed narrator units covering the six standard
exercises (heaviness, warmth, calm heart, calm breath, warm belly, cool brow),
runs endlessly into the shared sleep drift, honours the guidance flag, and is
wired into the storyteller dispatch (extra_names / ambience_for / story_units).
Pure, no Qt, no audio.
"""
import itertools
import os
import random
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import autogenic, stories  # noqa: E402


def _take(gen, n):
    return list(itertools.islice(gen, n))


def main():
    units = _take(autogenic.units(random.Random(1)), 70)
    assert all(isinstance(u, dict) and u["text"] and u["pause"] > 0 for u in units)
    blob = " ".join(u["text"].lower() for u in units)
    for word in ("heavy", "warm", "heartbeat", "breath", "belly", "cool"):
        assert word in blob, f"missing the '{word}' exercise"
    assert "calm and regular" in blob and "it breathes you" in blob
    print("ok: yields well-formed units covering the six standard exercises")

    # the breath-paced guide units appear only with guidance on
    g_on = _take(autogenic.units(guidance=True), 20)
    g_off = _take(autogenic.units(guidance=False), 20)
    assert any(u.get("kind") == "guide" for u in g_on)
    assert not any(u.get("kind") == "guide" for u in g_off)
    print("ok: guidance flag adds/removes the breath-paced breaths")

    # it never runs out (endless soft drift into sleep, like the hypnosis tail)
    deep = _take(autogenic.units(random.Random(2)), 400)
    assert len(deep) == 400 and all(d["text"] for d in deep)
    print("ok: runs endlessly into the shared sleep drift")

    # wired into the storyteller dispatch
    assert autogenic.NAME in stories.extra_names()
    assert stories.ambience_for(autogenic.NAME) == autogenic.AMBIENCE
    via = _take(stories.story_units(autogenic.NAME, random.Random(3)), 8)
    assert via and via[0]["text"], "story_units should dispatch to autogenic"
    print("ok: appears in extra_names + ambience_for + story_units dispatch")

    print("PASS: Autogenic Training session")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
