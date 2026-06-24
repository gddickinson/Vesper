"""The face widget — a younger, feminine, blue ICT head that breathes + lip-syncs.

Only the ICT-FaceKit renderer is used (the one that renders well). It is coloured
blue (``skin_hue`` ~ 206 + a blue hair-cap) with soft light skin and rose lips for
a younger, feminine look. The ICT software render is ~65 ms, so it runs on a
**background thread**; the GUI paints the latest frame each tick with a smooth
breathing zoom (40 fps motion, ~15 fps face content) and never blocks.

Lip-sync: ``jaw_open`` follows the live narration amplitude. Breath drives a
gentle head pitch + the breathing zoom; eyes slow-blink and grow heavy as the
session winds down.
"""
from __future__ import annotations

import copy
import math
import os
import random
import threading
import time

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

try:                                              # the 3D head is optional
    from faceview.vision.personas import apply_persona, load_persona
    from faceview.vision.sim_face import FaceParams, render_face
    _HAVE_FACEVIEW = True
except Exception:                                 # no faceView -> 2D cartoon-cat fallback
    _HAVE_FACEVIEW = False

from . import cat, face_bg, face_gpu, hourglass, theme

# faceView's Claude avatar: the ICT head, xray (glowing cyan) style, "young"
# identity — exactly what the characters file names as default Claude.
CLAUDE_PERSONA = "ict_xray_young"


def _claude_face() -> FaceParams:
    p = FaceParams.neutral()
    apply_persona(p, load_persona(CLAUDE_PERSONA))
    p.smile = 0.12
    p.background = theme.BG
    return p


class FaceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        # VESPER_FACE=cat starts on the 2D cat; =software forces the CPU ICT render.
        force = os.environ.get("VESPER_FACE",
                               os.environ.get("BSQT_FACE", "")).lower()
        self._faceview_ok = _HAVE_FACEVIEW           # is the 3D head usable at all?
        self._show_cat = (not self._faceview_ok) or force == "cat"  # current choice
        self._gpu = (self._faceview_ok and face_gpu.available()
                     and force != "software")
        self._params = _claude_face() if self._faceview_ok else None
        self._breath = 0.5
        self._t = 0.0
        self._style = "Default"                  # cyberpunk face style (see face_styles)
        self._pulse = 1.0                        # breath glow (1.0 = none; reactive only)
        self._hue = theme.ACCENT
        self._req = ((copy.copy(self._params), (480, 520)) if self._faceview_ok
                     else (None, (480, 520)))
        self._frame = None                       # (rgba ndarray, w, h)
        self._cat = cat.CatFace()                # the 2D fallback face
        self._cat_state = dict(vol=0.5, t=0.0, mouth=0.0, eye_open=1.0,
                               smile=0.12, hue=theme.ACCENT)
        self._bg = face_bg.make("Stars")         # animated background behind head
        self._active = True                      # throttle render thread when hidden
        self._gaze_ph = (random.random() * 6.283, random.random() * 6.283)
        self._head_ph = random.random() * 6.283
        self._sacc = (0.0, 0.0)                  # micro-saccade gaze offset
        self._next_sacc = 1.5
        self._sigh_t0 = None                     # rare settling-sigh
        self._next_sigh = 9.0
        self._swallow_t0 = None                  # occasional swallow
        self._next_swallow = 16.0
        self._tilt = 0.0                         # eased head-tilt (curiosity)
        self._next_blink = 2.5                   # randomized idle blink schedule
        self._blink_end = -1.0
        self._warm = 0.0                         # warm low-blue Sleep dimming (0..1)
        self._hg = None                          # hourglass timer state (or None)
        self._hg_rect = None                     # last-drawn hit rect
        self._hg_click_cb = None                 # flip-to-reset callback
        self._stop = False
        self._thread = None
        if self._faceview_ok:                    # ONE render thread (idles on cat)
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def set_use_cat(self, on):
        """Switch the face between the cartoon cat and the 3D head at runtime.
        Always the cat when faceView isn't available."""
        self._show_cat = bool(on) or not self._faceview_ok
        self.update()

    def uses_cat(self):
        return self._show_cat

    def set_style(self, name):
        """Choose the cyberpunk render style (eye pattern / skin / mode). Unknown
        names fall back to Default. Affects the 3D head only; the cat ignores it."""
        from . import face_styles
        self._style = name if name in face_styles.STYLES else "Default"
        self.update()

    def style(self):
        return self._style

    def set_pulse(self, v):
        """Breath glow multiplier (1.0 = none). Driven by the reactive face so the
        eyes/rim gently brighten on the in-breath and soften on the out-breath."""
        self._pulse = max(0.6, min(1.4, float(v)))

    def faceview_available(self):
        return self._faceview_ok

    def set_warm(self, amount):
        self._warm = max(0.0, min(1.0, float(amount)))

    def set_hourglass(self, state):
        """state = dict(frac, t, running, spin) to show the timer, or None to hide."""
        self._hg = state
        self.update()

    def mousePressEvent(self, ev):
        pos = ev.position()
        if self._hg_click_cb and hourglass.hit(self._hg_rect, pos.x(), pos.y()):
            self._hg_click_cb()
            return
        super().mousePressEvent(ev)

    def set_background(self, name):
        self._bg = face_bg.make(name)
        self.update()

    def set_active(self, on):
        """When the scene view is showing, throttle the head render thread."""
        self._active = bool(on)

    def set_state(self, vol, t, prog, mouth=0.0, nose=0.0, pucker=0.0,
                  stretch=0.0, phase="inhale", smile=0.12, brow=0.0,
                  eye_bias=0.0):
        """vol 0..1 breath, t time, prog 0..1, the resolved mouth pose, and the
        eased emotion (``smile``/``brow``/``eye_bias``). Mouth precedence (speaking
        vs. breathing) is decided upstream; the widget adds the *naturalistic* life
        — a gently wandering gaze, head sway, randomized blinks — on top.
        """
        self._breath = vol
        self._t = t                                          # background anim time
        self._hue = theme.phase_hue(phase)                   # tint bg by breath phase
        prog = prog or 0.0
        calm = 1.0 - 0.6 * prog                              # wind-down: stiller late
        # Randomized blinks — varied gap, occasional double, heavier when drowsy.
        if t >= self._next_blink:
            self._blink_end = t + 0.16
            gap = (0.30 if random.random() < 0.15
                   else random.uniform(2.5, 6.0) * (1.0 - 0.45 * prog))
            self._next_blink = t + max(0.22, gap)
        blink = 1.0 if t < self._blink_end else 0.0
        rest = 0.10 + 0.5 * prog                             # lids grow heavy late
        eye_open = max(0.04, min(1.0, 1.0 - rest - blink + eye_bias))
        # Gaze: a slow drift plus rare micro-saccades (quick darts), both damped
        # as the session winds down so the face grows calm and still.
        g0, g1 = self._gaze_ph
        dx = 0.05 * math.sin(0.11 * t + g0) + 0.03 * math.sin(0.29 * t + g0)
        dy = 0.035 * math.sin(0.15 * t + g1) + 0.02 * math.sin(0.33 * t + g1)
        if t >= self._next_sacc:
            a = 0.11 * calm
            self._sacc = (random.uniform(-a, a), random.uniform(-0.7 * a, 0.7 * a))
            self._next_sacc = t + random.uniform(0.7, 1.8) * (1.0 + 1.6 * prog)
        gaze_x = max(-0.25, min(0.25, dx * calm + self._sacc[0]))
        gaze_y = max(-0.18, min(0.18, dy * calm + self._sacc[1]))
        sigh = self._gesture("_sigh_t0", "_next_sigh", t, 1.6, 24.0, 52.0)
        swal = self._gesture("_swallow_t0", "_next_swallow", t, 0.5, 16.0, 38.0)
        tilt_t = max(0.0, min(1.0, brow)) * 0.6              # curiosity head-cock
        self._tilt += (tilt_t - self._tilt) * 0.05
        smile_eff = 0.06 + (max(0.0, min(1.0, smile)) - 0.06) * (0.5 + 0.5 * calm)
        brow_eff = max(0.0, min(1.0, brow)) * calm           # flatter affect late
        mo = max(0.0, min(0.6, mouth + sigh * 0.1 + swal * 0.06))
        pitch = (0.5 - vol) * 0.18 + 0.02 * math.sin(0.09 * t) + sigh * 0.1 + swal * 0.05
        self._cat_state = dict(vol=vol, t=t, mouth=mo, eye_open=eye_open,
                               smile=smile_eff, hue=self._hue,
                               gaze=(gaze_x, gaze_y), tilt=self._tilt)
        if self._faceview_ok:                                # keep 3D params fresh
            p = self._params
            p._t = t                                         # GPU starfield time
            p.pupil_x, p.pupil_y = gaze_x, gaze_y
            p.jaw_open = mo                                  # mouth resolved upstream
            p.mouth_pucker = max(0.0, min(1.0, pucker))
            p.mouth_stretch = max(0.0, min(1.0, stretch))
            p.nose_wrinkle = max(0.0, min(0.16, nose))       # noseSneer lifts the lip
            p.smile = smile_eff
            p.brow_raise = brow_eff
            p.pitch = pitch                                  # breath nod + sigh/swallow
            p.yaw = (0.04 * math.sin(0.07 * t + self._head_ph) * calm
                     + self._tilt * 0.1)                     # idle sway + head-cock
            p.eye_open = eye_open
            p._style = self._style                       # cyberpunk render style
            p._pulse = self._pulse                       # breath glow (reactive)
            self._req = (copy.copy(p),
                         (max(2, self.width()), max(2, self.height())))
        self.update()

    def _gesture(self, t0_attr, next_attr, t, dur, lo, hi):
        """A rare one-shot bump (0->1->0 over *dur* s), rescheduled lo..hi s later.
        Used for the settling-sigh and the swallow."""
        t0 = getattr(self, t0_attr)
        if t0 is None:
            if t >= getattr(self, next_attr):
                setattr(self, t0_attr, t)
            return 0.0
        u = (t - t0) / dur
        if u >= 1.0:
            setattr(self, t0_attr, None)
            setattr(self, next_attr, t + random.uniform(lo, hi))
            return 0.0
        return math.sin(math.pi * u)

    def stop(self):
        self._stop = True

    def _worker(self):
        while not self._stop:
            if self._show_cat or not self._active:    # idle: cat shown or hidden
                time.sleep(0.12)
                continue
            params, (w, h) = self._req
            try:
                img = face_gpu.render(params, (w, h)) if self._gpu else None
                if img is None:                             # GPU off/failed
                    self._gpu = False
                    img = render_face(params, (w, h))       # software fallback (BGR)
                if img.shape[2] == 4:                       # GPU: RGBA, transparent bg
                    rgba = np.ascontiguousarray(img)
                else:                                       # software: opaque BGR
                    rgba = np.ascontiguousarray(np.dstack(
                        [img[:, :, ::-1], np.full((h, w), 255, np.uint8)]))
                self._frame = (rgba, w, h)
            except Exception:
                pass
            time.sleep(0.005 if self._active else 0.1)

    def paintEvent(self, _ev):
        w, h = max(2, self.width()), max(2, self.height())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(0, 0, w, h, QColor(theme.BG))
        try:                                                 # animated backdrop
            self._bg.draw(painter, w, h, self._t, self._breath, self._hue)
        except Exception:
            pass
        fr = None if self._show_cat else self._frame
        if fr is not None:                                   # 3D avatar frame
            rgba, fw, fh = fr
            qimg = QImage(rgba.data, fw, fh, 4 * fw, QImage.Format.Format_RGBA8888)
            pm = QPixmap.fromImage(qimg)
            scale = 0.97 + 0.06 * self._breath               # breathing zoom
            sw, sh = int(fw * scale), int(fh * scale)
            painter.drawPixmap((w - sw) // 2, (h - sh) // 2, sw, sh, pm)
        elif self._show_cat:                                 # 2D cartoon cat
            try:
                self._cat.draw(painter, w, h, self._cat_state)
            except Exception:
                pass
        face_bg.warm_overlay(painter, w, h, self._warm)      # Sleep wind-down warmth
        self._hg_rect = hourglass.draw_corner(painter, w, h, self._hg)
        painter.end()
