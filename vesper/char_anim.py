"""Shared animation engine for the 2D characters (cat, penguin, dog, ...).

`AnimState.step(dt, state)` turns the per-frame face state (vol / mouth / eye_open
/ smile / gaze / tilt / optional ``excite``) into a rich set of **character-agnostic
signals** the characters interpret: a breathing body bob + squash, slow idle sway,
blinks (incl. spontaneous ones), a continuously swishing tail, occasional ear
twitches, and a "hair on end" bristle that spikes on excitement / a rare startle and
eases away. Centralising this here means every character moves with the same gentle,
alive timing -- and new motions only have to be added once.

Pure (no Qt). Uses ``random`` for the small spontaneous gestures, seeded by wall
phase passed in (so it's deterministic enough to unit-test the easing math).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Anim:
    t: float = 0.0
    breath: float = 0.5      # lung volume 0..1
    excite: float = 0.0      # liveliness 0..1 (chant / energetic / startle)
    bob: float = 0.0         # head vertical offset (fraction of head R)
    sway: float = 0.0        # head/body horizontal offset (fraction of R)
    squash: float = 0.0      # body squash (+) on exhale / stretch (-) on inhale
    tilt: float = 0.0        # head-cock (-1..1)
    blink: float = 0.0       # 0 = open, 1 = shut
    gaze: tuple = (0.0, 0.0)
    mouth: float = 0.0
    smile: float = 0.12
    tail: float = 0.0        # signed swish (radians)
    ear: float = 0.0         # ear/feather twitch-perk 0..1
    bristle: float = 0.0     # hair/feathers on end 0..1
    hue: str = "#86e6bf"


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


class AnimState:
    """Persistent per-character animation timers. One per face widget."""

    def __init__(self, rng=None):
        self._rng = rng or random.Random()
        r = self._rng.random
        self.t = 0.0
        self._tail = r() * 6.2831
        self._sway = r() * 6.2831
        self._bobph = r() * 6.2831
        self._ear_t0 = None
        self._next_ear = 2.0 + r() * 4.0
        self._blink_t0 = None
        self._next_blink = 3.0 + r() * 4.0
        self._startle_t0 = None
        self._next_startle = 18.0 + r() * 30.0
        self.bristle = 0.0

    def _gesture(self, t0, dur):
        """0->1->0 bump over *dur* s since *t0*, or None when finished."""
        if t0 is None:
            return None
        u = (self.t - t0) / dur
        return None if u >= 1.0 else math.sin(math.pi * u)

    def step(self, dt, st):
        dt = max(0.0, min(0.1, float(dt)))
        self.t += dt
        t = self.t
        breath = _clamp(float(st.get("vol", 0.5)))
        excite = _clamp(float(st.get("excite", 0.0)))

        # rare spontaneous startle -> a brief excite + bristle spike (amusing life)
        if self._startle_t0 is None and t >= self._next_startle:
            self._startle_t0 = t
        sg = self._gesture(self._startle_t0, 1.1)
        if sg is None and self._startle_t0 is not None:
            self._startle_t0 = None
            self._next_startle = t + 18.0 + self._rng.random() * 34.0
        startle = sg or 0.0
        excite = max(excite, 0.55 * startle)

        # hair/feathers on end: chase the target (excite), ease away slowly
        target = excite
        self.bristle += (target - self.bristle) * (0.25 if target > self.bristle
                                                   else 0.05)

        # tail swishes continually, faster + wider when livelier
        self._tail += dt * (1.1 + 3.0 * excite)
        tail = math.sin(self._tail) * (0.16 + 0.55 * excite)

        # gentle idle sway + breathing bob/squash
        sway = math.sin(t * 0.45 + self._sway) * (0.018 + 0.03 * excite)
        bob = (breath - 0.5) * 0.05 + math.sin(t * 0.8 + self._bobph) * 0.012
        squash = (0.5 - breath) * 0.07

        # ear/feather twitch one-shot, rescheduled
        if self._ear_t0 is None and t >= self._next_ear:
            self._ear_t0 = t
        eg = self._gesture(self._ear_t0, 0.5)
        if eg is None and self._ear_t0 is not None:
            self._ear_t0 = None
            self._next_ear = t + 2.5 + self._rng.random() * 5.0
        ear = max(eg or 0.0, 0.4 * excite)

        # blink: from eye_open, plus an occasional spontaneous extra blink
        eye_open = _clamp(float(st.get("eye_open", 1.0)), 0.04, 1.0)
        if self._blink_t0 is None and t >= self._next_blink:
            self._blink_t0 = t
        bg = self._gesture(self._blink_t0, 0.18)
        if bg is None and self._blink_t0 is not None:
            self._blink_t0 = None
            self._next_blink = t + 3.0 + self._rng.random() * 5.0
        blink = max(1.0 - eye_open, bg or 0.0)

        return Anim(
            t=t, breath=breath, excite=excite, bob=bob, sway=sway, squash=squash,
            tilt=float(st.get("tilt", 0.0)), blink=_clamp(blink), gaze=tuple(
                st.get("gaze", (0.0, 0.0))),
            mouth=max(0.0, min(0.6, float(st.get("mouth", 0.0)))),
            smile=_clamp(float(st.get("smile", 0.12))), tail=tail, ear=_clamp(ear),
            bristle=_clamp(self.bristle), hue=st.get("hue", "#86e6bf"))
