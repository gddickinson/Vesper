"""Hourglass session-timer behaviour for the MainWindow (mixed in).

Keeps `window.py` lean: the per-tick state push, the View-menu toggle and the
flip-to-reset gesture live here. The painter itself is ``vesper.hourglass``; the
FaceWidget / VizWidget draw it in a corner and report taps back via
``_hg_click_cb`` (wired to ``_flip_hourglass``)."""
from __future__ import annotations

_SPIN_DUR = 0.6                                   # seconds for a flip rotation


class _HourglassMixin:
    def _tick_hourglass(self, running, total, prog):
        """Push the timer state to the visible view (or hide it). Advances any
        flip-spin animation; the hourglass only shows when a session length is set."""
        if self._hg_spin_t0 is not None:              # ease the flip rotation
            u = (self._anim_t - self._hg_spin_t0) / _SPIN_DUR
            if u >= 1.0:
                self._hg_spin, self._hg_spin_t0 = self._hg_spin_to, None
            else:
                e = u * u * (3.0 - 2.0 * u)           # smoothstep
                self._hg_spin = (self._hg_spin_from
                                 + (self._hg_spin_to - self._hg_spin_from) * e)
        state = None
        if self._hg_show and total > 0:
            state = {"frac": max(0.0, min(1.0, prog or 0.0)), "t": self._anim_t,
                     "running": running, "spin": self._hg_spin}
        live = self.viz if self._view == "scene" else self.face
        other = self.face if self._view == "scene" else self.viz
        live.set_hourglass(state)
        if other._hg is not None:
            other.set_hourglass(None)

    def toggle_hourglass(self, show=None):
        """Show/hide the hourglass session timer (View menu / persisted)."""
        self._hg_show = (not self._hg_show) if show is None else bool(show)
        act = getattr(self, "_act_hourglass", None)
        if act is not None and act.isChecked() != self._hg_show:
            act.setChecked(self._hg_show)

    def _flip_hourglass(self):
        """Turn the hourglass over: reset the session clock and spin the glass."""
        self.controller.restart()
        self._logged_session = False
        if self._bell_interval > 0:
            self._next_bell = self._bell_interval * 60.0
        self._hg_spin_from = self._hg_spin
        self._hg_spin_to = self._hg_spin + 180.0
        self._hg_spin_t0 = self._anim_t
