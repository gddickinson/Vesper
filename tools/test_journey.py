"""Offline test for the "A Gentle Journey Downstream" guided-imagery session.

Checks the session yields well-formed narrator units that step into a boat,
drift on the current, watch the banks pass and let worries go, keeps its
letting-go / being-carried framing, runs endlessly into the shared sleep drift,
honours the guidance flag, uses a registered ambience, and is wired into the
storyteller dispatch (extra_names / ambience_for / story_units).  Pure, no Qt.
"""
import itertools
import os
import random
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import journey, stories, voices  # noqa: E402


def _take(gen, n):
    return list(itertools.islice(gen, n))


def main():
    units = _take(journey.units(random.Random(1)), 70)
    assert all(isinstance(u, dict) and u["text"] and u["pause"] > 0 for u in units)
    blob = " ".join(u["text"].lower() for u in units)
    # steps into the boat, drifts on the current, watches the banks, lets go, rests
    for cue in ("small wooden boat", "the current takes", "banks begin to slip",
                "let the river take it", "eases to a gentle stop"):
        assert cue in blob, f"missing the journey cue '{cue}'"
    # the being-carried / letting-go framing -- the heart of the technique
    for theme in ("do not need to row", "carried", "let them go"):
        assert theme in blob, f"missing the letting-go theme '{theme}'"
    print("ok: embarks, drifts on the current, watches the banks, lets go, rests")

    # the breath-paced guide units appear only with guidance on
    g_on = _take(journey.units(guidance=True), 16)
    g_off = _take(journey.units(guidance=False), 16)
    assert any(u.get("kind") == "guide" for u in g_on)
    assert not any(u.get("kind") == "guide" for u in g_off)
    print("ok: guidance flag adds/removes the breath-paced breaths")

    # it never runs out (endless soft drift into sleep, like the hypnosis tail)
    deep = _take(journey.units(random.Random(2)), 400)
    assert len(deep) == 400 and all(d["text"] for d in deep)
    print("ok: runs endlessly into the shared sleep drift")

    # wired into the storyteller dispatch + a registered ambience
    assert journey.NAME in stories.extra_names()
    assert stories.ambience_for(journey.NAME) == journey.AMBIENCE
    assert voices.get_voice(journey.AMBIENCE) is not None, "ambience not registered"
    via = _take(stories.story_units(journey.NAME, random.Random(3)), 8)
    assert via and via[0]["text"], "story_units should dispatch to journey"
    print("ok: extra_names + ambience_for (registered) + story_units dispatch")

    print("PASS: A Gentle Journey Downstream session")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
