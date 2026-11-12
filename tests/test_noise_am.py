"""Regression: noise voices honour ``am_rate`` / ``am_depth`` (tremolo).

"Deep Sleep (Pink Noise)" is a ``kind="noise"`` voice declared with
``am_rate=0.8, am_depth=0.35`` and described as swelling at ~0.8 Hz, but
``NoiseTrack`` used to ignore the AM fields, so it played as plain steady noise.
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from breathsim import tracks, voices  # noqa: E402
from breathsim.patterns import BreathState  # noqa: E402

SR = 22050


def _state():
    return BreathState(phase="inhale", progress=0.5, remaining=1.0, volume=1.0,
                       airflow=1.0, cycle_index=0, label="Breathe In")


def _render(cfg, seconds=12.0, block=512):
    tr = tracks.build_track(cfg, SR)
    s = _state()
    out = [tr.render(block, s, s) for _ in range(int(seconds * SR / block))]
    return np.concatenate(out)[:, 0]


def _peak_trough_ratio(x, rate):
    """Mean RMS at the AM troughs divided by the mean RMS at the peaks."""
    t = np.arange(len(x)) / SR
    ph = (2 * math.pi * rate * t) % (2 * math.pi)       # sin(ph): +1 trough, -1 peak
    trough = np.abs(ph - math.pi / 2) < 0.4
    peak = np.abs(ph - 3 * math.pi / 2) < 0.4
    skip = t > 1.0                                       # let the filters settle
    return (np.sqrt(np.mean(x[trough & skip] ** 2))
            / np.sqrt(np.mean(x[peak & skip] ** 2)))


def test_deep_sleep_noise_swells_at_am_rate():
    cfg = voices.get_voice("Deep Sleep (Pink Noise)")
    assert cfg.kind == "noise" and cfg.am_rate == 0.8
    ratio = _peak_trough_ratio(_render(cfg), cfg.am_rate)
    # trough gain 1 - am_depth = 0.65 relative to the peaks
    assert abs(ratio - (1 - cfg.am_depth)) < 0.08, ratio


def test_plain_noise_is_unmodulated():
    cfg = voices.get_voice("Pink Noise")
    assert cfg.am_rate == 0.0
    ratio = _peak_trough_ratio(_render(cfg), 0.8)
    assert abs(ratio - 1.0) < 0.08, ratio
