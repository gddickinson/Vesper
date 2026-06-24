"""Offline loudness audit for the ambience beds (and any voice group).

Renders each voice in a group for a fixed time and reports peak + rms, flagging
rms outliers versus the group median, so we can spot any bed that is jarringly
louder or quieter than its neighbours when the soundscape switches. Read-only;
it changes nothing -- it just measures, so the numbers are auditable.

Usage: python -m tools.loudness            # GROUP_NATURE (the ambience beds)
       python -m tools.loudness <GROUP>    # any voices group name
"""
from __future__ import annotations

import sys

import numpy as np

from breathsim import tracks, voices
from breathsim.patterns import BreathPattern, state_at

SR, BLOCK, SECONDS = 44100, 2048, 12.0


def measure(name, sr=SR):
    cfg = voices.get_voice(name)
    if cfg is None:
        return None
    tr = tracks.build_track(cfg, sr)
    pat = BreathPattern("t", 2, 1, 3, 1)
    peak = 0.0
    sq = 0.0
    n = 0
    for b in range(int(SECONDS * sr / BLOCK)):
        t0, t1 = b * BLOCK / sr, (b + 1) * BLOCK / sr
        out = tr.render(BLOCK, state_at(pat, t0), state_at(pat, t1))
        a = np.abs(out)
        peak = max(peak, float(a.max()))
        sq += float(np.square(out).sum())
        n += out.size
    rms = (sq / max(1, n)) ** 0.5
    return peak, rms


def main(group=None):
    group = group or voices.GROUP_NATURE
    names = voices.names(group)
    rows = []
    for nm in names:
        m = measure(nm)
        if m:
            rows.append((nm, m[0], m[1]))
    if not rows:
        print("no voices in", group)
        return
    rmss = sorted(r[2] for r in rows)
    median = rmss[len(rmss) // 2]
    print(f"\n{group}: {len(rows)} beds, median rms {median:.4f}\n")
    print(f"{'bed':24s} {'peak':>7s} {'rms':>8s} {'x median':>9s}  flag")
    for nm, pk, rms in sorted(rows, key=lambda r: r[2]):
        ratio = rms / median if median else 0.0
        flag = "LOUD" if ratio > 2.0 else ("quiet" if ratio < 0.4 else "")
        print(f"{nm:24s} {pk:7.3f} {rms:8.4f} {ratio:8.2f}x  {flag}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
