"""Breath session controller -- the single timing authority.

Holds the active :class:`~breathsim.patterns.BreathPattern`, a monotonic
session clock with pause/resume, and an optional session length. Both the GUI
animation loop and the audio engine read breath state from here, so visuals and
sound stay in sync.
"""
from __future__ import annotations

import dataclasses
import time

from . import naturalness as nat_mod
from . import patterns
from .patterns import BreathPattern, BreathState


class BreathController:
    def __init__(self, pattern: BreathPattern):
        self.pattern = pattern
        self.session_seconds = 0.0     # 0 = unlimited
        self.running = False
        self._accum = 0.0              # elapsed seconds banked from prior runs
        self._t0 = None               # monotonic time the current run started
        self._pattern_t0 = 0.0         # session time at which the pattern started
        self.naturalness = nat_mod.Naturalness()   # optional per-breath variation

    # --- transport ---------------------------------------------------------

    def start(self):
        if self.running:
            return
        self._t0 = time.monotonic()
        self.running = True

    def pause(self):
        if not self.running:
            return
        self._accum += time.monotonic() - self._t0
        self._t0 = None
        self.running = False

    def toggle(self):
        self.pause() if self.running else self.start()

    def reset(self):
        self.running = False
        self._t0 = None
        self._accum = 0.0
        self._pattern_t0 = 0.0

    def restart(self):
        """Reset the session clock to zero while keeping the running state — for
        'turning the hourglass over'. The breath cycle realigns to the inhale."""
        self._accum = 0.0
        self._pattern_t0 = 0.0
        self._t0 = time.monotonic() if self.running else None

    # --- time / state ------------------------------------------------------

    def elapsed(self) -> float:
        if self.running and self._t0 is not None:
            return self._accum + (time.monotonic() - self._t0)
        return self._accum

    def state_at(self, t: float) -> BreathState:
        tt = max(0.0, t - self._pattern_t0)
        nat = self.naturalness
        if not nat.on:
            return patterns.state_at(self.pattern, tt)
        # Per-breath variation. Total cycle length is kept fixed (the internal
        # phase split is jittered), so cycle boundaries stay at k*cycle -- the
        # lookup is O(1) and identical on every thread, with no drift.
        cycle = self.pattern.cycle
        k = int(tt // cycle)
        within = tt - k * cycle
        pat = self._jittered_pattern(k) if nat.timing else self.pattern
        base = patterns.state_at(pat, within)
        vol, air = base.volume, base.airflow
        if nat.depth:
            d = nat.depth_factor(k)
            vol *= d
            air *= d
        return dataclasses.replace(
            base, cycle_index=k, volume=vol, airflow=air,
            pitch_mod=(nat.pitch_mod(k) if nat.pitch else 0.0),
            tone_mod=(nat.tone_mod(k) if nat.tone else 1.0))

    def _jittered_pattern(self, k: int) -> BreathPattern:
        """The pattern with per-cycle jittered phase durations, re-normalised to
        the same total cycle length (so the breathing tempo stays steady)."""
        p = self.pattern
        f = self.naturalness.phase_factors(k)
        d = [p.inhale * f[0], p.hold_full * f[1],
             p.exhale * f[2], p.hold_empty * f[3]]
        s = d[0] + d[1] + d[2] + d[3]
        if s <= 0:
            return p
        sc = p.cycle / s
        return BreathPattern(p.name, d[0] * sc, d[1] * sc, d[2] * sc, d[3] * sc)

    def current_state(self) -> BreathState:
        return self.state_at(self.elapsed())

    def lookahead_state(self, dt: float) -> BreathState:
        """State *dt* seconds after now (used for block-end envelope ramps)."""
        return self.state_at(self.elapsed() + dt)

    # --- session bookkeeping ----------------------------------------------

    def set_pattern(self, pattern: BreathPattern):
        """Change the pattern without realigning (for smooth interpolation)."""
        self.pattern = pattern

    def change_pattern(self, pattern: BreathPattern):
        """Switch pattern and restart the breath cycle at the inhale (a clean
        transition for picking a preset or moving to a new session stage)."""
        self.pattern = pattern
        self._pattern_t0 = self.elapsed()

    def cycles_done(self) -> int:
        return int(max(0.0, self.elapsed() - self._pattern_t0) // self.pattern.cycle)

    def session_finished(self) -> bool:
        return self.session_seconds > 0 and self.elapsed() >= self.session_seconds

    def session_remaining(self) -> float:
        if self.session_seconds <= 0:
            return float("inf")
        return max(0.0, self.session_seconds - self.elapsed())
