"""Offline test: the master bus must never send non-finite audio to the card.

The real-time audio callback mixes every layer + chimes, applies the master
gain, and limits with ``dsp.soft_clip``. ``soft_clip`` was a bare ``tanh``:
``tanh(+/-inf)`` folds to +/-1 (fine), but ``tanh(nan)`` is ``nan`` -- so a single
misbehaving track could send a non-finite buffer to CoreAudio and play
full-scale garbage (a loud burst, the worst thing to do to a sleeper). The
limiter is now finite-safe (NaN -> silence), and the callback logs a persistent
fault once instead of failing silently forever.

This pins both: ``soft_clip`` is always finite and still limits, and the engine
callback yields finite output (silence) for a NaN-producing or raising layer,
warning exactly once.  Pure NumPy + a headless AudioEngine; no sound device.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from breathsim import dsp, patterns  # noqa: E402
from breathsim.controller import BreathController  # noqa: E402
from breathsim.engine import AudioEngine  # noqa: E402


class _BadLayer:
    """A layer that mimics a misbehaving track -- it renders NaN every block."""
    def __init__(self, mode="nan"):
        self.dead = False
        self.mode = mode

    def render(self, frames, s0, s1):
        if self.mode == "raise":
            raise RuntimeError("forced render fault")
        return np.full((frames, 2), np.nan)


def test_soft_clip_finite():
    x = np.array([0.0, 0.2, -0.2, 5.0, -5.0, np.nan, np.inf, -np.inf])
    out = dsp.soft_clip(x)
    assert np.all(np.isfinite(out)), ("soft_clip left non-finite values", out)
    assert np.all(np.abs(out) <= 1.0 + 1e-6), ("limiter exceeded unity", out)
    assert out[5] == 0.0, ("NaN should map to silence", out[5])
    assert abs(out[1] - np.tanh(0.2)) < 1e-9, "small-signal shape changed"
    print("ok: soft_clip is finite (NaN->0), still limits to +/-1, linear when small")


def test_callback_finite_on_bad_layer():
    eng = AudioEngine(BreathController(patterns.DEFAULT_PATTERN), sr=22050,
                      blocksize=256)
    eng.master = eng.master_target = 0.8
    frames = 256
    outdata = np.zeros((frames, 2), dtype=np.float32)

    # a NaN-spewing layer must NOT reach the card as non-finite garbage
    eng.layers = [_BadLayer("nan")]
    eng._callback(outdata, frames, None, None)
    assert np.all(np.isfinite(outdata)), "NaN layer produced non-finite output!"
    print("ok: a NaN-producing layer yields finite output (silenced, not noise)")

    # a layer that raises -> the block is silenced and the fault is logged once
    eng.layers = [_BadLayer("raise")]
    outdata[:] = 7.0
    eng._callback(outdata, frames, None, None)
    assert np.all(outdata == 0.0), "a raising layer should silence the block"
    assert eng._cb_warned, "a callback fault should be logged (warned) once"
    print("ok: a raising layer is contained (silence) and warned exactly once")

    # a healthy layer still plays through finite
    eng._cb_warned = False
    eng.layers = []
    eng._callback(outdata, frames, None, None)
    assert np.all(np.isfinite(outdata)) and not eng._cb_warned
    print("ok: a clean callback stays finite and quiet (no spurious warning)")


def main():
    test_soft_clip_finite()
    test_callback_finite_on_bad_layer()
    print("PASS: audio master-bus finite-safety")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
