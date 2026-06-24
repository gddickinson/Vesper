"""VizWidget — a QWidget that hosts and paints the current visualization scene.

Holds a persistent scene instance (so ripple rings / star drift / pitch history
carry across frames), switched by ``set_scene(name)``. ``update_state(ctx)``
stores the latest per-frame context and requests a repaint; ``paintEvent`` hands
an antialiased QPainter to the scene. The MainWindow drives whichever of the face
/ viz is currently shown in the central QStackedWidget.
"""
from __future__ import annotations

from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from . import face_bg, hourglass, scene_particles, scenes, theme


class VizWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        self._scene = scenes.make("orb")
        self._weather = scene_particles.ParticleLayer()   # optional weather overlay
        self._warm = 0.0                          # warm low-blue Sleep dimming
        self._hg = None                           # hourglass timer state (or None)
        self._hg_rect = None
        self._hg_click_cb = None
        self._ctx = {"running": False, "volume": 0.5, "airflow": 0.0,
                     "phase": "inhale", "cycle_frac": 0.0, "remaining": 0.0,
                     "label": "Ready", "t": 0.0, "prog": None}

    def set_warm(self, amount):
        self._warm = max(0.0, min(1.0, float(amount)))

    def set_weather(self, kind):
        self._weather.set_kind(kind)
        self.update()

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

    def scene_name(self) -> str:
        return self._scene.name

    def set_scene(self, name):
        if name and name != self._scene.name:
            self._scene = scenes.make(name)
            self.update()

    def update_state(self, ctx):
        self._ctx = ctx
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = max(2, self.width()), max(2, self.height())
        try:
            self._scene.draw(p, w, h, self._ctx)
        except Exception:
            p.fillRect(0, 0, w, h, theme.BG)
        self._weather.draw(p, w, h, self._ctx.get("t", 0.0),
                           self._ctx.get("volume", 0.5))   # optional weather layer
        face_bg.warm_overlay(p, w, h, self._warm)     # Sleep wind-down warmth
        self._hg_rect = hourglass.draw_corner(p, w, h, self._hg)
        p.end()
