"""Offline test for the "Tonight's pick / Surprise me" random chooser.

`tonight.pick` returns a random name avoiding recent ones; `tonight.pick_any`
spreads the surprise across the WHOLE storyteller library -- the hundreds of
lectures AND the small special set of guided sessions + poetry -- with a gentle
bias so those ~20 sessions/poems are not drowned out and actually come up once in
a while. This checks the avoid-recent + determinism + fallbacks of both, and that
pick_any reaches both pools at roughly the intended rate. Pure, no Qt.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import tonight  # noqa: E402


def test_pick():
    assert tonight.pick([]) is None and tonight.pick(None) is None
    assert tonight.pick(["a"]) == "a"
    # prefers a non-recent name; falls back to the full list if all are recent
    got = tonight.pick(["a", "b"], recent=["a"], rng=random.Random(1))
    assert got == "b", got
    assert tonight.pick(["a"], recent=["a"]) == "a"          # only choice -> reuse
    # deterministic with a seeded rng
    assert (tonight.pick(list("abcdef"), rng=random.Random(7))
            == tonight.pick(list("abcdef"), rng=random.Random(7)))
    print("ok: pick avoids recent, falls back, is deterministic")


def test_pick_any_reaches_both():
    lec = ["L%d" % i for i in range(300)]
    ext = ["E%d" % i for i in range(20)]
    rng = random.Random(3)
    picks = [tonight.pick_any(lec, ext, rng=rng) for _ in range(3000)]
    assert all(p is not None for p in picks)
    extras = sum(1 for p in picks if p.startswith("E"))
    frac = extras / len(picks)
    # the bias should land near extra_chance (0.34), NOT the ~6% a uniform pick
    # over 320 names would give -- so the special set is genuinely surfaced
    assert 0.25 < frac < 0.45, ("extras share off target", frac)
    assert extras > 0 and extras < len(picks), "both pools must be reachable"
    print("ok: pick_any reaches both pools; extras ~%.0f%% (not drowned)" % (100 * frac))


def test_pick_any_edges():
    # only one pool present -> always pick from it
    assert tonight.pick_any(["a", "b"], [], rng=random.Random(1)).startswith(("a", "b"))
    assert tonight.pick_any([], ["x", "y"], rng=random.Random(1)).startswith(("x", "y"))
    assert tonight.pick_any([], []) is None
    # deterministic with a seeded rng
    a = tonight.pick_any(list("abc"), list("xyz"), rng=random.Random(5))
    b = tonight.pick_any(list("abc"), list("xyz"), rng=random.Random(5))
    assert a == b, (a, b)
    print("ok: pick_any handles empty pools + is deterministic")


def test_wired_into_the_library():
    """pick_any over the real lecture + extra names returns a valid storyteller
    name (it must round-trip through the story dispatch)."""
    from breathsim import stories
    lec, ext = list(stories.lecture_names()), list(stories.extra_names())
    assert lec and ext
    name = tonight.pick_any(lec, ext, rng=random.Random(11))
    assert name in set(lec) | set(ext), name
    # the chosen name resolves to a registered ambience (so set_story can arm it)
    from breathsim import voices
    amb = stories.ambience_for(name)
    assert amb is None or voices.get_voice(amb) is not None, (name, amb)
    print("ok: a real surprise pick resolves to a dispatchable storyteller item")


def main():
    test_pick()
    test_pick_any_reaches_both()
    test_pick_any_edges()
    test_wired_into_the_library()
    print("PASS: tonight's pick / surprise me")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
