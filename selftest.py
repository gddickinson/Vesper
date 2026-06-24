#!/usr/bin/env python3
"""Headless self-test for the self-contained vesper project.

Checks the **vendored** core (`./breathsim`): every voice renders finite and peaks
<= 1.0 (airflow voices silent on holds), and every lecture loads, is finite, has a
registered ambience, a unique name, and no malformed lines. Exits non-zero on any
problem. Run: `python selftest.py`. (No GUI / audio device needed.)
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

from breathsim import lectures, phrases, stories, tracks, voices  # noqa: E402
from breathsim.patterns import BreathPattern, preset_by_name, state_at  # noqa: E402
from breathsim.vocal import VocalTrack  # noqa: E402


def main() -> int:
    problems = []
    sr, block = 44100, 1024
    pat = BreathPattern("t", 2, 1, 3, 1)
    cfgs = voices.all_configs()
    for cfg in cfgs:
        tr = tracks.build_track(cfg, sr)
        holds, peak = [], 0.0
        for b in range(int(8 * sr / block)):
            t0, t1 = b * block / sr, (b + 1) * block / sr
            s0, s1 = state_at(pat, t0), state_at(pat, t1)
            out = tr.render(block, s0, s1)
            if not np.all(np.isfinite(out)):
                problems.append(f"{cfg.name}: non-finite output")
                break
            peak = max(peak, float(np.abs(out).max()))
            if s0.phase == "hold_full" and s0.progress > 0.4:
                holds.append(float(np.abs(out).max()))
        if peak > 1.0:
            problems.append(f"{cfg.name}: peak {peak:.2f} > 1.0")
        if cfg.env == "airflow" and holds and max(holds) > 0.02:
            problems.append(f"{cfg.name}: not silent on hold ({max(holds):.3f})")
    print(f"Checked {len(cfgs)} voices, {len(voices.names())} voice names.")

    # Chant/song/word phrases: render a few breaths (in each phrase's own style,
    # plus a reciting-tone pass) and check the sequence voice is finite and safe.
    for ph in phrases.PHRASES:
        pat = preset_by_name(ph.pattern) or BreathPattern("t", 2, 1, 3, 1)
        # the reciting tone only ever applies to Mantra / Chant Sounds (engine).
        recite_opts = (False, True) if ph.category in ("Mantra", "Chant Sounds") \
            else (False,)
        for monotone in recite_opts:
            tr = VocalTrack(phrases.config(ph), sr)
            tr.set_sequence(ph.segments, ph.base_pitch, ph.style, ph.groups,
                            monotone=monotone)
            peak = 0.0
            steps = int(pat.cycle * 2 * sr / block)
            for b in range(steps):
                t0, t1 = b * block / sr, (b + 1) * block / sr
                out = tr.render(block, state_at(pat, t0), state_at(pat, t1))
                if not np.all(np.isfinite(out)):
                    problems.append(f"phrase {ph.name}: non-finite output")
                    break
                peak = max(peak, float(np.abs(out).max()))
            if peak > 1.0:
                problems.append(f"phrase {ph.name}: peak {peak:.2f} > 1.0")
    print(f"Checked {len(phrases.PHRASES)} chant/song/word phrases.")

    names = lectures.names()
    if len(set(names)) != len(names):
        problems.append("duplicate lecture names")
    for nm in names:
        amb = stories.ambience_for(nm)
        if voices.get_voice(amb) is None:
            problems.append(f"{nm}: unregistered ambience {amb!r}")
        units = list(stories.story_units(nm, rng=random.Random(1)))
        lec = [u for u in units if u["kind"] == "lecture"]
        if len(units) >= 400 or len(lec) < 55:
            problems.append(f"{nm}: unexpected length ({len(units)} units)")
        if any(not u["text"].strip() or u["text"].strip()[-1] not in ".?!"
               for u in lec):
            problems.append(f"{nm}: malformed line")
    print(f"Checked {len(names)} lectures across "
          f"{len(lectures.categories())} branches.")

    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print("Self-test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
