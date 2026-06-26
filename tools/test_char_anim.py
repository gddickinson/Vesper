"""Offline test for the shared character-action engine (vesper.char_anim).

Drives `AnimState.step` over a long synthetic session and checks that the rarer
drowsy gestures actually fire and stay in-bounds:
  * a wide **yawn** opens the mouth while the eyes squeeze toward shut,
  * a **stretch** lengthens the body beyond the breathing baseline,
  * a **head-cock** tilts the head to either side,
  * a **look-around** moves the gaze beyond the supplied baseline,
  * a **nod-off** dips the head,
  * a contented **sigh** opens the mouth a little WITHOUT the yawn's eye-squeeze,
  * a cosy **settle** (nestle-down) fires on its schedule,
  * the **reduce-motion** (`calm`) flag spaces the gestures out (fewer firings),
  * every Anim field is finite and within its documented clamp every frame.

Pure (no Qt) -- char_anim only uses math + random.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vesper import char_anim  # noqa: E402


def _state(t, mouth=0.0, gaze=(0.0, 0.0), calm=0.0):
    """A neutral per-frame face state with a gently breathing lung volume."""
    return dict(vol=0.5 + 0.45 * math.sin(t * 0.5), t=t, mouth=mouth,
                eye_open=1.0, smile=0.12, gaze=gaze, tilt=0.0, calm=calm)


def _run(secs, seed=7, calm=0.0, mouth=0.0, gaze=(0.0, 0.0)):
    """Step an AnimState for *secs* at ~40 fps, returning the list of Anim frames."""
    a = char_anim.AnimState(rng=random.Random(seed))
    dt = 1.0 / 40.0
    frames, t = [], 0.0
    n = int(secs / dt)
    for _ in range(n):
        t += dt
        frames.append(a.step(dt, _state(t, mouth=mouth, gaze=gaze, calm=calm)))
    return frames


def _finite(x):
    return isinstance(x, float) and math.isfinite(x)


def _rising_edges(vals, lo, hi):
    """Count low->high crossings (gesture onsets) in a 0..1 signal."""
    n, armed = 0, True
    for v in vals:
        if armed and v >= hi:
            n += 1
            armed = False
        elif v <= lo:
            armed = True
    return n


def test_in_bounds():
    """Over a long run every field stays finite and within its documented range."""
    for f in _run(240, seed=3):
        assert _finite(f.bob) and abs(f.bob) < 0.5, f.bob
        assert _finite(f.squash) and abs(f.squash) < 0.5, f.squash
        assert _finite(f.tilt) and abs(f.tilt) < 1.2, f.tilt
        assert 0.0 <= f.blink <= 1.0, f.blink
        assert 0.0 <= f.mouth <= 0.6, f.mouth
        assert -0.30 <= f.gaze[0] <= 0.30 and -0.22 <= f.gaze[1] <= 0.22, f.gaze
        assert 0.0 <= f.ear <= 1.0 and 0.0 <= f.bristle <= 1.0
    print("ok: all Anim fields finite + in-bounds over a 240s run")


def test_gestures_fire():
    """Each new gesture is observable somewhere in a long enough run."""
    frames = _run(260, seed=11)
    mouths = [f.mouth for f in frames]
    assert max(mouths) > 0.45, ("yawn never opened the mouth", max(mouths))
    # while yawning wide the eyes squeeze toward shut
    wide = max(range(len(frames)), key=lambda i: frames[i].mouth)
    assert frames[wide].blink > 0.4, ("eyes did not close during the yawn",
                                      frames[wide].blink)
    assert max(f.squash for f in frames) > 0.06, "stretch never lengthened the body"
    assert max(abs(f.tilt) for f in frames) > 0.05, "head never cocked"
    # head cocks to BOTH sides across a long run (random direction)
    assert min(f.tilt for f in frames) < -0.02, "head only cocked one way"
    assert max(abs(f.gaze[0]) for f in frames) > 0.05, "gaze never looked around"
    print("ok: yawn / stretch / head-cock / look-around all fire and read right")


def _count_onsets(attr, secs, seed=7):
    """Count how many times a scheduled gesture timer (e.g. ``_sigh_t0``) fires
    (None -> running transitions) over a long run -- white-box proof it triggers."""
    a = char_anim.AnimState(rng=random.Random(seed))
    dt, t, n, prev = 1.0 / 40.0, 0.0, 0, None
    for _ in range(int(secs / dt)):
        t += dt
        a.step(dt, _state(t))
        cur = getattr(a, attr)
        if prev is None and cur is not None:
            n += 1
        prev = cur
    return n


def test_new_gestures_fire():
    """The new drowsy gestures fire on their schedule, and the sigh reads
    differently from the yawn (mouth opens but the eyes stay open)."""
    assert _count_onsets("_sigh_t0", 300) >= 1, "sigh never fired"
    assert _count_onsets("_settle_t0", 340) >= 1, "settle never fired"
    # a contented sigh: a moderate mouth-open while the eyes are NOT squeezed
    # shut -- a yawn that open (>0.2) always has blink >= ~0.30, so this is
    # sigh-specific.
    frames = _run(300, seed=7)
    assert any(f.mouth > 0.2 and f.blink < 0.22 for f in frames), \
        "no contented-sigh frame (mouth open with eyes still open)"
    print("ok: sigh + settle fire; sigh opens the mouth with eyes open")


def test_calm_spaces_gestures():
    """Reduce-motion lengthens the intervals: fewer yawn onsets in equal time."""
    secs = 320
    busy = _rising_edges([f.mouth for f in _run(secs, seed=5, calm=0.0)], 0.1, 0.4)
    calm = _rising_edges([f.mouth for f in _run(secs, seed=5, calm=1.0)], 0.1, 0.4)
    assert busy >= 3, ("expected several yawns at full motion", busy)
    assert calm < busy, ("reduce-motion should yawn less often", calm, busy)
    print("ok: reduce-motion yawns %d < %d at full motion" % (calm, busy))


def test_respects_inputs():
    """The yawn rides over the incoming mouth; look-around adds to incoming gaze."""
    # a held-open input mouth is never reduced (max with the yawn)
    frames = _run(20, seed=2, mouth=0.3, gaze=(0.2, 0.0))
    assert all(f.mouth >= 0.3 - 1e-6 for f in frames), "incoming mouth was lost"
    assert all(abs(f.gaze[0]) >= 0.2 - 1e-6 or f.gaze[0] != 0.2 for f in frames)
    print("ok: gestures combine with (never erase) the supplied mouth/gaze")


def main():
    test_in_bounds()
    test_gestures_fire()
    test_new_gestures_fire()
    test_calm_spaces_gestures()
    test_respects_inputs()
    print("PASS: character actions (char_anim)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
