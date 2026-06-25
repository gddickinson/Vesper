"""Offline test for the Loving-Kindness (Metta) guided session.

Checks the session yields well-formed narrator units that move through the
widening circles of metta (self, a loved one, a neutral person, a difficult one,
all beings) with the four classic wishes, runs endlessly into the shared sleep
drift, honours the guidance flag, and is wired into the storyteller dispatch
(extra_names / ambience_for / story_units).  Pure, no Qt, no audio.
"""
import itertools
import os
import random
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import lovingkindness, stories  # noqa: E402


def _take(gen, n):
    return list(itertools.islice(gen, n))


def main():
    units = _take(lovingkindness.units(random.Random(1)), 70)
    assert all(isinstance(u, dict) and u["text"] and u["pause"] > 0 for u in units)
    blob = " ".join(u["text"].lower() for u in units)
    # the four classic wishes
    for wish in ("may i be safe", "may i be happy", "may i be healthy",
                 "may i live with ease"):
        assert wish in blob, f"missing the wish '{wish}'"
    # the widening circles of metta
    for circle in ("yourself", "someone you love", "barely know",
                   "difficult", "all beings"):
        assert circle in blob, f"missing the '{circle}' circle"
    print("ok: yields well-formed units with the four wishes + widening circles")

    # the breath-paced guide units appear only with guidance on
    g_on = _take(lovingkindness.units(guidance=True), 20)
    g_off = _take(lovingkindness.units(guidance=False), 20)
    assert any(u.get("kind") == "guide" for u in g_on)
    assert not any(u.get("kind") == "guide" for u in g_off)
    print("ok: guidance flag adds/removes the breath-paced breaths")

    # it never runs out (endless soft drift into sleep, like the hypnosis tail)
    deep = _take(lovingkindness.units(random.Random(2)), 400)
    assert len(deep) == 400 and all(d["text"] for d in deep)
    print("ok: runs endlessly into the shared sleep drift")

    # wired into the storyteller dispatch
    assert lovingkindness.NAME in stories.extra_names()
    assert stories.ambience_for(lovingkindness.NAME) == lovingkindness.AMBIENCE
    via = _take(stories.story_units(lovingkindness.NAME, random.Random(3)), 8)
    assert via and via[0]["text"], "story_units should dispatch to lovingkindness"
    print("ok: appears in extra_names + ambience_for + story_units dispatch")

    print("PASS: Loving-Kindness (Metta) session")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
