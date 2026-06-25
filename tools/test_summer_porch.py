"""Offline test for the "Summer Porch" sleep ambience.

Checks it is registered as a Nature voice, renders finite and stays comfortably
below clipping (its calibrated gain keeps the peak well under 1.0), is audible at
a gentle sleep-bed level, and is part of the gentle ambience-rotation set. Pure,
no Qt, no audio device.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from breathsim import ambrotate, tracks, voices  # noqa: E402
from breathsim.patterns import BreathPattern, state_at  # noqa: E402

NAME = "Summer Porch"


def _render(cfg, seconds=8):
    sr, block = 44100, 1024
    pat = BreathPattern("t", 2, 1, 3, 1)
    tr = tracks.build_track(cfg, sr)
    peak, acc = 0.0, []
    for b in range(int(seconds * sr / block)):
        t0, t1 = b * block / sr, (b + 1) * block / sr
        out = tr.render(block, state_at(pat, t0), state_at(pat, t1))
        assert np.all(np.isfinite(out)), "non-finite output"
        peak = max(peak, float(np.abs(out).max()))
        acc.append(out)
    a = np.concatenate(acc)
    return peak, float(np.sqrt(np.mean(a ** 2)))


def main():
    # registered as a Nature voice
    assert NAME in voices.names(), "Summer Porch should be registered"
    cfg = voices.get_voice(NAME)
    assert cfg is not None and cfg.group == voices.GROUP_NATURE
    assert cfg.noise == "pink", cfg.noise
    print("ok: registered as a Nature (pink-noise) voice")

    # finite + safely below clipping, and audible at a calm sleep-bed level
    peak, rms = _render(cfg)
    assert peak <= 1.0, f"peak {peak} must stay <= 1.0"
    assert peak < 0.7, f"calibrated peak should have headroom, got {peak:.3f}"
    assert 0.03 < rms < 0.12, f"should be a gentle bed, rms={rms:.4f}"
    print(f"ok: renders finite, peak={peak:.3f} (<1.0), rms={rms:.4f}")

    # comparable in loudness to the other nature beds (consistency)
    _po, ro = _render(voices.get_voice("Ocean Waves"))
    assert abs(rms - ro) < 0.03, f"loudness should sit near the beds ({rms:.4f} vs {ro:.4f})"
    print(f"ok: loudness consistent with the beds (rms {rms:.4f} ~ Ocean {ro:.4f})")

    # part of the gentle ambience-rotation set, which still cycles cleanly
    assert NAME in ambrotate.BEDS, "should join the ambience rotation"
    seen = {ambrotate.next_ambience(ambrotate.BEDS, i * ambrotate.DEFAULT_PERIOD)
            for i in range(len(ambrotate.BEDS))}
    assert NAME in seen and len(seen) == len(ambrotate.BEDS)
    print(f"ok: in the ambience rotation ({len(ambrotate.BEDS)} beds, all reachable)")

    print("PASS: Summer Porch ambience")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
