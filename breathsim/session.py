"""Session director: drives the morph over time and runs guided programs.

Modes
-----
``Manual``      morph follows the slider.
``Auto drift``  morph eases A<->B on a slow cosine (``period`` seconds).
``Random``      every ``period`` seconds glide to a new random morph amount and
                occasionally swap Voice B.
``Program``     a multi-stage guided session (see :mod:`breathsim.programs`):
                each stage applies its own pattern/voice/scene and advances
                automatically, with an on-screen + spoken instruction.

Also runs the Sleep wind-down (continuous pattern slowing + volume fade).
"""
from __future__ import annotations

import math

import numpy as np

from . import programs, voices
from .patterns import BreathPattern


class SessionDirector:
    MODES = ["Manual", "Auto drift", "Random"]

    def __init__(self, app):
        self.app = app
        self.mode = "Manual"
        self.manual = 0.0
        self.period = 30.0
        self.sleep = False
        self.sleep_duration = 1200.0
        self.sleep_a = None
        self.sleep_b = None
        self.wake = False                 # Sunrise dawn-simulation (inverse of sleep)
        self.wake_duration = 900.0
        self.wake_a = None
        self.wake_b = None
        self.program = None
        self.program_stage = -1
        self.program_t0 = 0.0
        self._starts: list[float] = []
        self._total = 0.0
        self._rng = np.random.default_rng()
        self._cur = 0.0
        self._from = 0.0
        self._to = 0.0
        self._seg_t0 = 0.0
        self._seg_t1 = 1.0
        self._next_t = 0.0

    # --- control -----------------------------------------------------------

    def set_mode(self, mode: str):
        self.sleep = False
        self.wake = False
        self.program = None
        if programs.get(mode):
            self.start_program(mode)
            return
        self.mode = mode
        self._next_t = 0.0

    def start_program(self, name):
        prog = programs.get(name) if isinstance(name, str) else name
        if not prog:
            return
        self.mode = "Program"
        self.sleep = False
        self.program = prog
        self.program_stage = -1
        self.program_t0 = self.app.controller.elapsed()
        self._starts, acc = [], 0.0
        for s in prog.stages:
            self._starts.append(acc)
            acc += s.minutes * 60.0
        self._total = acc
        self.app.controller.session_seconds = self.program_t0 + acc
        self._update_program(self.program_t0)        # cue up stage 0

    def stage_info(self):
        """(title, index1, n, stage_remaining_s, total_remaining_s) or None."""
        if not self.program:
            return None
        local = self.app.controller.elapsed() - self.program_t0
        i = min(self.program_stage, len(self.program.stages) - 1)
        if i < 0:
            return None
        end = self._starts[i] + self.program.stages[i].minutes * 60.0
        return (self.program.stages[i].title, i + 1, len(self.program.stages),
                max(0.0, end - local), max(0.0, self._total - local))

    def start_sleep(self, duration, start_pattern, end_pattern):
        self.sleep = True
        self.wake = False
        self.mode = "Manual"
        self.program = None
        self.sleep_duration = max(60.0, float(duration))
        self.sleep_a = start_pattern
        self.sleep_b = end_pattern

    def stop_sleep(self):
        self.sleep = False

    def start_wake(self, duration, start_pattern, end_pattern):
        """Sunrise wake-up: the inverse of the wind-down. Over *duration* the
        breath quickens slow->normal and the volume rises quiet->full; the GUI
        brightens (warm dim -> clear) in :meth:`window._tick`."""
        self.wake = True
        self.sleep = False
        self.mode = "Manual"
        self.program = None
        self.wake_duration = max(60.0, float(duration))
        self.wake_a = start_pattern
        self.wake_b = end_pattern

    def stop_wake(self):
        self.wake = False

    def set_manual(self, value):
        self.manual = float(value)

    def set_period(self, seconds):
        self.period = max(3.0, float(seconds))

    # --- per-frame update --------------------------------------------------

    def update(self, t):
        if self.program is not None:
            self._update_program(t)
            return
        if self.sleep:
            self._update_sleep(t)
            return
        if self.wake:
            self._update_wake(t)
            return
        eng = self.app.engine
        if self.mode == "Auto drift":
            ph = (t % self.period) / self.period
            eng.set_morph(0.5 - 0.5 * math.cos(2 * math.pi * ph))
        elif self.mode == "Random":
            self._update_random(t)
        else:
            eng.set_morph(self.manual)

    def _update_program(self, t):
        local = t - self.program_t0
        idx = 0
        for i, start in enumerate(self._starts):
            if local >= start:
                idx = i
        if idx != self.program_stage:
            self.program_stage = idx
            stage = self.program.stages[idx]
            self.app.apply_stage(stage)
            if stage.say:
                self.app.speech.announce(stage.say)

    def _update_random(self, t):
        eng = self.app.engine
        if t >= self._next_t:
            self._from = self._cur
            self._to = float(self._rng.random())
            self._seg_t0, self._seg_t1 = t, t + self.period
            self._next_t = t + self.period
            if self._rng.random() < 0.5:
                eng.set_voice_b(str(self._rng.choice(self._morphable_names())))
        span = max(0.001, self._seg_t1 - self._seg_t0)
        frac = min(1.0, max(0.0, (t - self._seg_t0) / span))
        self._cur = self._from + (self._to - self._from) * (
            0.5 - 0.5 * math.cos(math.pi * frac))
        eng.set_morph(self._cur)

    def _update_sleep(self, t):
        d = self.sleep_duration
        frac = min(1.0, t / d) if d > 0 else 1.0
        a, b = self.sleep_a, self.sleep_b
        if a is not None and b is not None:
            def lerp(x, y):
                return x + (y - x) * frac
            self.app.controller.set_pattern(BreathPattern(
                "Sleep wind-down", lerp(a.inhale, b.inhale),
                lerp(a.hold_full, b.hold_full), lerp(a.exhale, b.exhale),
                lerp(a.hold_empty, b.hold_empty)))
        vol = self.app.user_volume
        if frac > 0.7:
            vol *= max(0.0, 1.0 - (frac - 0.7) / 0.3)
        if self.app.controller.running:
            self.app.engine.set_master_volume(vol)

    def _update_wake(self, t):
        d = self.wake_duration
        frac = min(1.0, t / d) if d > 0 else 1.0
        a, b = self.wake_a, self.wake_b
        if a is not None and b is not None:
            s = 0.5 - 0.5 * math.cos(math.pi * frac)        # smooth ease slow->normal
            def lerp(x, y):
                return x + (y - x) * s
            self.app.controller.set_pattern(BreathPattern(
                "Sunrise wake-up", lerp(a.inhale, b.inhale),
                lerp(a.hold_full, b.hold_full), lerp(a.exhale, b.exhale),
                lerp(a.hold_empty, b.hold_empty)))
        vol = self.app.user_volume
        rise = min(1.0, 0.15 + frac / 0.8 * 0.85)           # quiet -> full by ~80%
        if self.app.controller.running:
            self.app.engine.set_master_volume(vol * rise)

    def _morphable_names(self):
        return (voices.names(voices.GROUP_VOCAL) + voices.names(voices.GROUP_SING)
                + voices.names(voices.GROUP_SYNTH) + voices.names(voices.GROUP_BREATH))


def mode_options():
    return SessionDirector.MODES + programs.names()
