"""Offline test for the master-bus "space" reverb (breathsim.reverb.SpaceReverb).

The sacred-space send (Room / Cave / Hall / Cathedral / Canyon) sits on the
master bus and runs for a whole session, so it must stay **stable** (no
feedback blow-up) and **finite** even under a loud transient, must leave the dry
signal untouched when **Off**, and every preset's comb feedback must be clamped
below 1.0.  This pins those invariants and that the two newer spaces (Cave,
Canyon) are wired in.  Pure NumPy; no audio device.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from breathsim import reverb  # noqa: E402

SR = 22050


def test_spaces_present():
    names = reverb.space_names()
    for want in ("Off", "Room", "Cave", "Hall", "Cathedral", "Canyon"):
        assert want in names, ("missing space", want, names)
    print("ok: Off/Room/Cave/Hall/Cathedral/Canyon all offered")


def test_gains_clamped():
    """Every comb's feedback gain stays < 1.0 -- the stability condition."""
    for nm in reverb.space_names():
        sp = reverb.SpaceReverb(SR)
        sp.set_space(nm)
        gains = [c.g for c in sp.cl] + [c.g for c in sp.cr]
        assert all(g < 1.0 for g in gains), (nm, "feedback >= 1", max(gains))
    print("ok: every space clamps comb feedback < 1.0 (stable)")


def test_finite_and_bounded():
    """A loud impulse + occasional noise bursts stay finite and bounded over a
    long run for every space (catches a comb-filter feedback blow-up)."""
    for nm in reverb.space_names():
        sp = reverb.SpaceReverb(SR)
        sp.set_space(nm)
        buf = np.zeros((512, 2))
        buf[0] = 3.0                                # a big transient to ring the tail
        peak = 0.0
        for i in range(2500):                       # ~58s of audio
            out = sp.process(buf)
            assert np.all(np.isfinite(out)), (nm, "non-finite at block", i)
            peak = max(peak, float(np.abs(out).max()))
            buf = (np.random.randn(512, 2) * 0.3
                   if i % 60 < 3 else np.zeros((512, 2)))
        assert peak < 12.0, (nm, "reverb tail blew up", peak)
    print("ok: every space stays finite + bounded under a loud run")


def test_off_is_identity():
    """Off must leave the dry signal exactly untouched (and report inactive)."""
    sp = reverb.SpaceReverb(SR)
    sp.set_space("Off")
    assert sp.active() is False
    buf = np.random.randn(512, 2) * 0.4
    out = sp.process(buf)
    assert np.array_equal(out, buf), "Off should pass the dry signal through unchanged"
    print("ok: Off is active=False and a pure pass-through (dry preserved)")


def test_wet_adds_a_decaying_tail():
    """A wet space is active, adds energy (a tail), and that tail decays after
    an impulse rather than sustaining or growing."""
    sp = reverb.SpaceReverb(SR)
    sp.set_space("Hall")
    assert sp.active() is True
    impulse = np.zeros((512, 2))
    impulse[0] = 1.0
    silence = np.zeros((512, 2))
    sp.process(impulse)                              # excite the tail
    # the comb delay exceeds one block, so the echo returns over the next many
    # blocks -- collect a stretch and look at the whole tail.
    energies = [float(np.abs(sp.process(silence)).sum()) for _ in range(60)]
    peak = max(energies)
    assert peak > 1e-4, "expected an audible reverb tail after the impulse"
    assert energies[-1] < peak, ("the tail should decay, not sustain or grow", peak)
    print("ok: a wet space adds a tail that rings out and decays after the impulse")


def main():
    test_spaces_present()
    test_gains_clamped()
    test_finite_and_bounded()
    test_off_is_identity()
    test_wet_adds_a_decaying_tail()
    print("PASS: master-bus space reverb")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
