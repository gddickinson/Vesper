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

from faceview.vision.personas import apply_persona, load_persona
from faceview.vision.sim_face import FaceParams, render_face

from . import face_bg, face_gpu, hourglass, theme

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
        self._params = _claude_face()
        self._breath = 0.5
        self._t = 0.0
        self._hue = theme.ACCENT
        self._req = (copy.copy(self._params), (480, 520))
        self._frame = None                       # (rgba ndarray, w, h)
        # GPU-ICT path (fast starfield eyes); BSQT_FACE=software forces the stable
        # CPU renderer if a machine's OpenGL driver is unhappy.
        self._gpu = (face_gpu.available()
                     and os.environ.get("BSQT_FACE", "").lower() != "software")
        self._bg = face_bg.make("Stars")         # animated background behind head
        self._active = True                      # throttle render thread when hidden
        self._gaze_ph = (random.random() * 6.283, random.random() * 6.283)
        self._head_ph = random.random() * 6.283
        self._next_blink = 2.5                   # randomized idle blink schedule
        self._blink_end = -1.0
        self._warm = 0.0                         # warm low-blue Sleep dimming (0..1)
        self._hg = None                          # hourglass timer state (or None)
        self._hg_rect = None                     # last-drawn hit rect
        self._hg_click_cb = None                 # flip-to-reset callback
        self._stop = False
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()                     # ONE render thread, started once

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
        p = self._params
        p._t = t                                             # GPU starfield time
        # Gentle wandering gaze — alive, never a dead forward stare.
        g0, g1 = self._gaze_ph
        p.pupil_x = 0.09 * math.sin(0.11 * t + g0) + 0.04 * math.sin(0.29 * t + g0)
        p.pupil_y = 0.06 * math.sin(0.15 * t + g1) + 0.03 * math.sin(0.33 * t + g1)
        # Mouth (resolved upstream).
        p.jaw_open = max(0.0, min(0.6, mouth))
        p.mouth_pucker = max(0.0, min(1.0, pucker))
        p.mouth_stretch = max(0.0, min(1.0, stretch))
        p.nose_wrinkle = max(0.0, min(0.16, nose))   # noseSneer lifts the lip; keep tiny
        # Emotion (eased upstream): a soft smile + a little brow.
        p.smile = max(0.0, min(1.0, smile))
        p.brow_raise = max(0.0, min(1.0, brow))
        # Head: the breath nod plus a tiny idle sway.
        p.pitch = (0.5 - vol) * 0.18 + 0.02 * math.sin(0.09 * t)
        p.yaw = 0.04 * math.sin(0.07 * t + self._head_ph)
        # Randomized blinks — varied gap, occasional double, heavier when drowsy.
        if t >= self._next_blink:
            self._blink_end = t + 0.16
            gap = (0.30 if random.random() < 0.15
                   else random.uniform(2.5, 6.0) * (1.0 - 0.45 * (prog or 0.0)))
            self._next_blink = t + max(0.22, gap)
        blink = 1.0 if t < self._blink_end else 0.0
        rest = 0.10 + 0.5 * (prog or 0.0)                    # lids grow heavy late
        p.eye_open = max(0.04, min(1.0, 1.0 - rest - blink + eye_bias))
        self._req = (copy.copy(p), (max(2, self.width()), max(2, self.height())))
        self.update()

    def stop(self):
        self._stop = True

    def _worker(self):
        while not self._stop:
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
        fr = self._frame
        if fr is not None:
            rgba, fw, fh = fr
            qimg = QImage(rgba.data, fw, fh, 4 * fw, QImage.Format.Format_RGBA8888)
            pm = QPixmap.fromImage(qimg)
            scale = 0.97 + 0.06 * self._breath               # breathing zoom
            sw, sh = int(fw * scale), int(fh * scale)
            painter.drawPixmap((w - sw) // 2, (h - sh) // 2, sw, sh, pm)
        face_bg.warm_overlay(painter, w, h, self._warm)      # Sleep wind-down warmth
        self._hg_rect = hourglass.draw_corner(painter, w, h, self._hg)
        painter.end()
