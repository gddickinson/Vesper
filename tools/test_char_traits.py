"""Offline test for per-character motion traits (char_anim + char_traits).

Every 2D character shares one animation engine, but `AnimState.set_traits` gives
each a motion *signature* -- tail swish, blink interval, yawn interval, ear/nose
twitch, head-swivel and energy multipliers. This checks the multipliers really
flow through (a swishier tail moves more; a rarer blinker blinks less; a twitchier
character perks more often), that defaults are a no-op, and that every registered
character has a traits entry so the map can't drift from the cast. Pure, no Qt.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vesper import char_anim, char_traits  # noqa: E402

SEED = 7
IDLE = {"vol": 0.5, "eye_open": 1.0, "excite": 0.0, "mouth": 0.0}


def _run(traits, steps, dt):
    """Step a seeded AnimState with *traits*, collecting each Anim frame."""
    a = char_anim.AnimState(rng=random.Random(SEED))
    a.set_traits(traits)
    return [a.step(dt, IDLE) for _ in range(steps)]


def test_tr_defaults():
    a = char_anim.AnimState()
    assert a._tr("tail") == 1.0 and a._tr("anything") == 1.0   # missing -> 1.0
    a.set_traits({"tail": 1.6})
    assert a._tr("tail") == 1.6 and a._tr("blink") == 1.0
    a.set_traits(None)
    assert a.traits == {}                                       # None -> empty
    print("ok: _tr defaults to 1.0; set_traits stores / clears")


def test_tail_amplitude_scales():
    # same seed + zero excite -> the tail phase is identical, so peak swish scales
    # directly with the tail multiplier
    swishy = max(abs(f.tail) for f in _run({"tail": 2.0}, 240, 0.05))
    still = max(abs(f.tail) for f in _run({"tail": 0.4}, 240, 0.05))
    assert swishy > still * 2.5, (swishy, still)
    print("ok: a swishier tail trait moves the tail much more (%.3f vs %.3f)"
          % (swishy, still))


def test_blink_rate_scales():
    # count blink "events" (rising edges) over a long idle run
    def blinks(traits):
        frames = _run(traits, 4000, 0.1)              # ~400 s
        n, prev = 0, 0.0
        for f in frames:
            if f.blink > 0.5 and prev <= 0.5:
                n += 1
            prev = f.blink
        return n
    frequent = blinks({"blink": 0.4})
    rare = blinks({"blink": 2.4})
    assert frequent > rare, (frequent, rare)
    print("ok: a rarer blinker blinks less (%d vs %d events)" % (frequent, rare))


def test_twitch_activity_scales():
    twitchy = sum(f.ear for f in _run({"twitch": 2.0}, 3000, 0.1))
    placid = sum(f.ear for f in _run({"twitch": 0.4}, 3000, 0.1))
    assert twitchy > placid * 1.5, (twitchy, placid)
    print("ok: a twitchier trait perks the ears much more (%.1f vs %.1f)"
          % (twitchy, placid))


def test_every_character_has_traits():
    from vesper import characters
    for name in characters.names():
        t = char_traits.get(name)
        assert isinstance(t, dict), name
        # any declared trait must be a sane positive multiplier
        for k, v in t.items():
            assert isinstance(v, (int, float)) and 0.0 <= v <= 3.0, (name, k, v)
    # the two newest animals carry a signature
    assert char_traits.get("Koala").get("yawn", 1.0) < 1.0     # sleepy -> yawns often
    assert char_traits.get("Red Panda").get("tail", 1.0) > 1.0  # swishy tail
    print("ok: all %d characters have valid traits" % len(characters.names()))


def main():
    test_tr_defaults()
    test_tail_amplitude_scales()
    test_blink_rate_scales()
    test_twitch_activity_scales()
    test_every_character_has_traits()
    print("PASS: per-character motion traits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
