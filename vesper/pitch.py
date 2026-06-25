"""Pitch-trainer wiring for the MainWindow (a mixin).

Owns the live microphone ``Tuner`` (degrades to nothing without a mic), the
current target spec, the reference tone, and the ``pitch_context`` the PitchScene
consumes. Turning the guide on switches the central view to the pitch scene and
starts the mic; turning it off reverts to the mode's scene.
"""
from __future__ import annotations

REF_VOICE = "Pitch Reference"
_DRONE_BASE = 110.0          # base_freq of the steady tonal reference voice


class _PitchMixin:
    def set_tuner(self, on):
        if on:
            if self.tuner is None:
                from breathsim import pitchtrack
                self.tuner = pitchtrack.Tuner(self.engine.sr)
            self.tuner.start()
        elif self.tuner is not None:
            self.tuner.stop()

    def show_pitch_guide(self, spec):
        self._pitch_spec = spec
        # Anchor the exercise clock to *now* (the always-advancing animation time),
        # so a scale/arpeggio scrolls from its first note whether or not a breathing
        # session is playing -- the trainer is a standalone warm-up. (Previously it
        # read controller.elapsed(), which is frozen until you press play, so every
        # exercise sat on its base note and looked identical to "Hold note".)
        self._pitch_t0 = getattr(self, "_anim_t", 0.0)
        self._sing_in = self._sing_tot = 0       # reset the % in-tune score
        self.set_tuner(True)
        self.viz.set_scene("pitch")
        self.set_view("scene")

    def pitch_clock(self):
        """Seconds since the current exercise began (always advancing)."""
        return getattr(self, "_anim_t", 0.0) - getattr(self, "_pitch_t0", 0.0)

    def hide_pitch_guide(self):
        self._pitch_spec = None
        self.set_tuner(False)
        self.viz.set_scene(self._scene_hint)

    def pitch_context(self, t):
        spec = getattr(self, "_pitch_spec", None)
        if not spec:
            return None
        from breathsim import vocaltrainer
        tgt, nxt, label = vocaltrainer.target_at(spec, t)
        lo, hi = vocaltrainer.range_hz(spec)
        return {"target": tgt, "next": nxt, "label": label, "lo": lo, "hi": hi}

    def set_reference(self, on, note):
        if not on:
            self.engine.set_layer("reference", None)
            return
        from breathsim import music
        tr = music.semitones(_DRONE_BASE, music.note_to_hz(note))
        self.engine.set_layer("reference", REF_VOICE, level=0.45, transpose=tr)
