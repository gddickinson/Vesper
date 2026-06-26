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

from . import captions, face_bg, hourglass, scene_particles, scenes, theme


class VizWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        # Name the central visual for screen readers (the breath is conveyed
        # audibly by the breath bed + optional spoken phase cues).
        self.setAccessibleName("Breathing visualization")
        self.setAccessibleDescription(
            "An ambient visual that breathes in and out with the guided pace.")
        self._scene = scenes.make("orb")
        self._weather = scene_particles.ParticleLayer()   # optional weather overlay
        self._warm = 0.0                          # warm low-blue Sleep dimming
        self._calm = False                        # 'reduce motion' (accessibility)
        self._vt = 0.0                            # virtual decorative clock (slows when calm)
        self._last_t = None
        self._hg = None                           # hourglass timer state (or None)
        self._hg_rect = None
        self._hg_click_cb = None
        self._caption = []                        # a11y: wrapped narration caption lines
        self._cap_scale = 1.0                     # a11y: UI text-size factor for captions
        self._warned = False                      # log a paint error only once
        self._ctx = {"running": False, "volume": 0.5, "airflow": 0.0,
                     "phase": "inhale", "cycle_frac": 0.0, "remaining": 0.0,
                     "label": "Ready", "t": 0.0, "prog": None}

    _CALM_RATE = 0.15                             # decorative motion runs at 15% when calm

    def set_warm(self, amount):
        self._warm = max(0.0, min(1.0, float(amount)))

    def set_calm(self, on):
        """'Reduce motion': slow the decorative drift/twinkle and drop the weather
        overlay, while the breath-driven orb + guide dot (informational) stay live."""
        self._calm = bool(on)

    def set_weather(self, kind):
        self._weather.set_kind(kind)
        self.update()

    def set_hourglass(self, state):
        """state = dict(frac, t, running, spin) to show the timer, or None to hide."""
        self._hg = state
        self.update()

    def set_caption(self, lines):
        """Accessibility: show the current spoken line as on-screen text (a list of
        wrapped caption rows), or [] to clear. Drawn as a calm overlay at the foot
        of whatever scene is showing, so it works the same for every scene."""
        self._caption = list(lines or [])

    def set_caption_scale(self, scale):
        """Accessibility: the global UI text-size factor, so captions enlarge with
        the rest of the interface (see fontscale)."""
        self._cap_scale = max(0.5, float(scale))

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
        # Feed the scenes a virtual clock that advances at the real rate normally,
        # or much more slowly when 'calm visuals' is on, so every time-driven
        # decorative motion (star drift, twinkle, motes, flicker) eases without
        # touching any scene. The breath-driven terms read volume/cycle_frac, not
        # this clock, so the breathing visualization stays fully responsive.
        rt = float(ctx.get("t", 0.0))
        if self._last_t is None:
            self._last_t = rt
        dt = rt - self._last_t
        self._last_t = rt
        if dt < 0.0:                              # guard a clock reset (new session)
            dt = 0.0
        self._vt += dt * (self._CALM_RATE if self._calm else 1.0)
        ctx = dict(ctx)
        ctx["t"] = self._vt
        ctx["calm"] = self._calm
        self._ctx = ctx
        self.update()

    def paintEvent(self, _ev):
        # paintEvent runs from the Qt event loop, NOT inside the _tick guard, so an
        # escape here would leave the QPainter active -> 'Cannot destroy paint device
        # that is being painted' -> hard crash. Always p.end() in a finally, and keep
        # every scene/overlay fault inside this method (degrade, never crash).
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            w, h = max(2, self.width()), max(2, self.height())
            try:
                self._scene.draw(p, w, h, self._ctx)
            except Exception as exc:
                p.fillRect(0, 0, w, h, theme.BG)
                self._warn("scene", exc)
            try:
                if not self._calm:                    # 'reduce motion' drops the busy layer
                    self._weather.draw(p, w, h, self._ctx.get("t", 0.0),
                                       self._ctx.get("volume", 0.5))   # weather layer
                face_bg.warm_overlay(p, w, h, self._warm)     # Sleep wind-down warmth
                captions.paint_caption(p, w, h, self._caption, self._cap_scale)  # a11y
                self._hg_rect = hourglass.draw_corner(p, w, h, self._hg)
            except Exception as exc:                  # an overlay must never escape paint
                self._warn("overlay", exc)
        finally:
            p.end()

    def _warn(self, where, exc):
        """Log the first paint error once (further ones suppressed) so a silently
        failing scene/overlay is at least diagnosable, without spamming ~40x/sec."""
        if not self._warned:
            self._warned = True
            print(f"[vesper] viz {where} draw error (further suppressed): {exc!r}")
