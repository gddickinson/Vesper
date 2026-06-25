"""Offline test for the "Distant Surf (night)" sleep ambience.

Checks it is registered as a Nature voice, renders finite and stays comfortably
below clipping (its calibrated gain keeps the peak well under 1.0), is softer
than the brighter "Ocean Waves", and is part of the gentle ambience-rotation set.
Pure, no Qt, no audio device.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from breathsim import ambrotate, tracks, voices  # noqa: E402
from breathsim.patterns import BreathPattern, state_at  # noqa: E402

NAME = "Distant Surf (night)"


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
    assert NAME in voices.names(), "Distant Surf should be registered"
    cfg = voices.get_voice(NAME)
    assert cfg is not None and cfg.group == voices.GROUP_NATURE
    assert cfg.noise == "brown", cfg.noise
    print("ok: registered as a Nature (brown-noise) voice")

    # finite + safely below clipping, and audible
    peak, rms = _render(cfg)
    assert peak <= 1.0, f"peak {peak} must stay <= 1.0"
    assert peak < 0.7, f"calibrated peak should have headroom, got {peak:.3f}"
    assert rms > 0.01, f"should be audible, rms={rms:.4f}"
    print(f"ok: renders finite, peak={peak:.3f} (<1.0), rms={rms:.4f}")

    # softer than the brighter Ocean Waves (a calmer, more distant bed)
    _po, ro = _render(voices.get_voice("Ocean Waves"))
    assert rms <= ro + 1e-4, f"Distant Surf rms {rms:.4f} should be <= Ocean {ro:.4f}"
    print(f"ok: softer than Ocean Waves (rms {rms:.4f} <= {ro:.4f})")

    # part of the gentle ambience-rotation set
    assert NAME in ambrotate.BEDS, "should join the ambience rotation"
    # the rotation still cycles cleanly with the new bed present
    seen = {ambrotate.next_ambience(ambrotate.BEDS, i * ambrotate.DEFAULT_PERIOD)
            for i in range(len(ambrotate.BEDS))}
    assert NAME in seen and len(seen) == len(ambrotate.BEDS)
    print(f"ok: in the ambience rotation ({len(ambrotate.BEDS)} beds, all reachable)")

    print("PASS: Distant Surf (night) ambience")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
