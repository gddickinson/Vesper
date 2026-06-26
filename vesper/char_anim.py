"""Shared animation engine for the 2D characters (cat, penguin, dog, ...).

`AnimState.step(dt, state)` turns the per-frame face state (vol / mouth / eye_open
/ smile / gaze / tilt / optional ``excite`` / optional ``calm``) into a rich set of
**character-agnostic signals** the characters interpret: a breathing body bob +
squash, slow idle sway, blinks (incl. spontaneous ones), a continuously swishing
tail, occasional ear twitches, and a "hair on end" bristle that spikes on excitement
/ a rare startle and eases away.  On top of those it weaves a handful of rarer,
drowsy **gestures** -- a slow contagious **yawn**, a luxurious **stretch**, a
sleepy **nod-off**, a curious **head-cock**, an idle **look-around**, a soft
contented **sigh** and a cosy **settle** (a nestle-down into the pillow) -- folded
back into the same mouth / blink / bob / squash / tilt / gaze fields so *every*
character performs them with no per-character drawing code.  Centralising this here
means every character moves with the same gentle, alive timing -- and new motions
only have to be added once.  ``calm`` (0..1, the "reduce motion" accessibility
setting) softens and spaces the gestures out.

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
        # rarer, drowsy gestures (each a scheduled one-shot, folded into the
        # existing output fields so every character performs them for free)
        self._yawn_t0 = None
        self._next_yawn = 20.0 + r() * 26.0
        self._stretch_t0 = None
        self._next_stretch = 24.0 + r() * 30.0
        self._nod_t0 = None
        self._next_nod = 30.0 + r() * 40.0
        self._cock_t0 = None
        self._next_cock = 14.0 + r() * 22.0
        self._cock_dir = 1.0
        self._look_t0 = None
        self._next_look = 11.0 + r() * 16.0
        self._look_dir = (0.0, 0.0)
        self._sigh_t0 = None
        self._next_sigh = 26.0 + r() * 30.0
        self._settle_t0 = None
        self._next_settle = 36.0 + r() * 40.0
        self._settle_dir = 1.0

    def _gesture(self, t0, dur):
        """0->1->0 bump over *dur* s since *t0*, or None when finished."""
        if t0 is None:
            return None
        u = (self.t - t0) / dur
        return None if u >= 1.0 else math.sin(math.pi * u)

    def _oneshot(self, t0_attr, next_attr, dur, lo, hi, slow=1.0, on_start=None):
        """Run a scheduled one-shot gesture timer. Starts when due (calling the
        optional *on_start* callback so direction can be randomised), returns its
        eased 0..1->0 bump, and reschedules *lo..hi* s out (stretched by *slow*
        for reduced motion). Centralises the start/run/reschedule bookkeeping the
        drowsy gestures all share."""
        t0 = getattr(self, t0_attr)
        if t0 is None and self.t >= getattr(self, next_attr):
            setattr(self, t0_attr, self.t)
            if on_start is not None:
                on_start()
            t0 = self.t
        g = self._gesture(t0, dur)
        if g is None and t0 is not None:
            setattr(self, t0_attr, None)
            gap = (lo + self._rng.random() * (hi - lo)) * slow
            setattr(self, next_attr, self.t + gap)
        return g or 0.0

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

        # --- rarer drowsy gestures (reduce-motion 'calm' softens + spaces them) --
        calm = _clamp(float(st.get("calm", 0.0)))
        amp = 1.0 - 0.7 * calm
        slow = 1.0 + 1.8 * calm

        # yawn: slow wide mouth that holds open while the eyes squeeze toward shut
        yg = self._oneshot("_yawn_t0", "_next_yawn", 2.3, 22.0, 48.0, slow)
        yawn = min(1.0, 1.5 * yg)                      # plateau across the middle

        # stretch: a luxurious lengthen of the body + a small upward lift
        stg = self._oneshot("_stretch_t0", "_next_stretch", 1.9, 24.0, 54.0, slow)
        stretch = stg * amp

        # head-cock: a curious tilt to one (random) side and back
        def _pick_cock():
            self._cock_dir = 1.0 if self._rng.random() < 0.5 else -1.0
        cg = self._oneshot("_cock_t0", "_next_cock", 1.4, 15.0, 37.0, slow,
                           on_start=_pick_cock)
        cock = cg * self._cock_dir * 0.22 * amp

        # look-around: a brief gaze peek to a fresh point, then ease back
        def _pick_look():
            a = 0.16 * amp
            self._look_dir = (self._rng.uniform(-a, a),
                              self._rng.uniform(-0.6 * a, 0.6 * a))
        lg = self._oneshot("_look_t0", "_next_look", 1.6, 12.0, 28.0, slow,
                           on_start=_pick_look)

        # nod-off: the head sinks slowly, then gently catches itself (dozing)
        nod = self._nod_off(t, slow) * amp

        # sigh: a soft, contented exhale -- a small mouth open + a brief body
        # settle, without the eye-squeeze of a yawn (a sleepy breath out)
        sigh = self._oneshot("_sigh_t0", "_next_sigh", 1.5, 26.0, 52.0, slow) * amp

        # settle: a slow nestle-down, like snuggling into the pillow and easing
        # back -- the head sinks and leans a touch, the body softens
        def _pick_settle():
            self._settle_dir = 1.0 if self._rng.random() < 0.5 else -1.0
        settle = self._oneshot("_settle_t0", "_next_settle", 2.4, 36.0, 64.0, slow,
                               on_start=_pick_settle) * amp

        mouth_in = max(0.0, min(0.6, float(st.get("mouth", 0.0))))
        gx, gy = st.get("gaze", (0.0, 0.0))
        gaze = (max(-0.30, min(0.30, gx + self._look_dir[0] * lg)),
                max(-0.22, min(0.22, gy + self._look_dir[1] * lg)))

        return Anim(
            t=t, breath=breath, excite=excite,
            bob=bob + nod * 0.055 - stretch * 0.020 - settle * 0.040,
            sway=sway, squash=squash + stretch * 0.06 + sigh * 0.045 + settle * 0.045,
            tilt=(float(st.get("tilt", 0.0)) + cock + nod * 0.05
                  + settle * self._settle_dir * 0.05),
            blink=_clamp(max(blink, 0.92 * yawn)), gaze=gaze,
            mouth=max(mouth_in, 0.55 * yawn, 0.30 * sigh),
            smile=_clamp(float(st.get("smile", 0.12))), tail=tail, ear=_clamp(ear),
            bristle=_clamp(self.bristle), hue=st.get("hue", "#86e6bf"))

    def _nod_off(self, t, slow):
        """Drowsy 'nodding off': head sinks slowly then catches back up (0..1)."""
        if self._nod_t0 is None and t >= self._next_nod:
            self._nod_t0 = t
        if self._nod_t0 is None:
            return 0.0
        u = (t - self._nod_t0) / 1.7
        if u >= 1.0:
            self._nod_t0 = None
            self._next_nod = t + (30.0 + self._rng.random() * 40.0) * slow
            return 0.0
        if u < 0.72:                                   # slow sink
            return math.sin(0.5 * math.pi * (u / 0.72))
        return math.cos(0.5 * math.pi * ((u - 0.72) / 0.28))   # quicker catch
