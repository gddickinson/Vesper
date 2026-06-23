"""Ported control actions for the MainWindow (a mixin).

These are the setters the workspace cards + menus call into: voice / body /
ambience / effect / morph / naturalness / choir / phrase / cues / pace / guided
sessions / sleep wind-down / background-sound toggles / mute. Split out of
``window.py`` so the window stays lifecycle-focused. State still lives on the
engine / controller / director; these just translate UI intent into core calls.
"""
from __future__ import annotations

from breathsim import choir, phrases
from breathsim.patterns import pattern_for_bpm, preset_by_name

from .stage_apply import apply_stage as _apply_stage


def _norm(name):
    """Map the UI's 'None'/'Same as inhale' sentinels to a real None."""
    if name in (None, "None", "Same as inhale", "(no voice)"):
        return None
    return name


class _ActionsMixin:
    # --- voice / body -----------------------------------------------------
    def set_voice_a(self, name):
        self.engine.set_voice_a(_norm(name))

    def set_voice_b(self, name):
        self.engine.set_voice_b(_norm(name))

    def set_voice_out(self, name):
        self.engine.set_voice_out(_norm(name))

    def set_persona(self, name):
        from breathsim import personas
        self.engine.set_persona(personas.get(name))

    # --- ambience / effects / mix ----------------------------------------
    def set_ambience(self, name):
        self.engine.set_voice(_norm(name), "ambience")

    def set_effect(self, name):
        self.engine.set_layer("effects", _norm(name),
                              level=self.engine.slot_levels.get("effects", 0.85))

    def set_slot_level(self, slot, level):
        self.engine.set_slot_level(slot, float(level))

    def toggle_layer(self, slot, on):
        self.engine.set_slot_muted(slot, not on)

    # --- morph ------------------------------------------------------------
    def set_morph_manual(self, amount):
        self.director.set_mode("Manual")
        self.director.set_manual(float(amount))
        self.engine.set_morph(float(amount))

    # --- naturalness ------------------------------------------------------
    def set_naturalness(self, amount, on):
        nat = self.controller.naturalness
        nat.amount = float(amount) if on else 0.0
        self._sync_menu()

    # --- choir / phrase ---------------------------------------------------
    def set_choir(self, harmony, level):
        if not harmony or harmony == "Off":
            choir.clear(self.engine)
        else:
            choir.apply(self.engine, self.engine.voice_a, harmony,
                        float(level), True)

    def set_phrase(self, name):
        self.engine.set_phrase(phrases.get(name) if _norm(name) else None)

    # --- cues -------------------------------------------------------------
    def set_cue_style(self, style):
        self.speech.set_style(style)
        self._sync_menu()

    # --- pace -------------------------------------------------------------
    def set_pace(self, bpm, long_exhale=False):
        self.controller.change_pattern(pattern_for_bpm(float(bpm), long_exhale))

    # --- guided sessions / programs / sleep -------------------------------
    def start_session_mode(self, name):
        self.director.set_mode(name)
        from breathsim import programs
        if programs.get(name):
            self._ensure_running()
        self.panel.sync()

    def set_winddown(self, on, minutes):
        if on:
            a = self.controller.pattern
            b = preset_by_name("Extended 7-11") or a
            self.director.start_sleep(float(minutes) * 60.0, a, b)
            self.controller.session_seconds = float(minutes) * 60.0
            self._story_minutes = float(minutes)
        else:
            self.director.stop_sleep()

    def _ensure_running(self):
        if not self.controller.running:
            self.toggle_transport()

    # --- mindfulness bell / retention timer -------------------------------
    def set_bell_interval(self, minutes):
        self._bell_interval = float(minutes)
        self._next_bell = self.controller.elapsed() + self._bell_interval * 60.0

    def toggle_hold(self):
        """Start/stop the breath-hold (retention) timer; log it on stop."""
        if self._hold_t0 is None:
            self._hold_t0 = self._anim_t
        else:
            secs = max(0.0, self._anim_t - self._hold_t0)
            self._hold_last = secs
            if secs >= 1.0:
                from breathsim import store
                store.log_hold(secs, "retention")
            self._hold_t0 = None

    def hold_status(self):
        if self._hold_t0 is not None:
            return ("holding", self._anim_t - self._hold_t0)
        return ("idle", self._hold_last)

    # --- mute -------------------------------------------------------------
    def set_muted(self, muted):
        self._is_muted = bool(muted)
        if self.controller.running:
            self.engine.set_master_volume(0.0 if muted else self.user_volume)

    # --- guided-program stage application ---------------------------------
    def apply_stage(self, stage):
        _apply_stage(self, stage)

    # --- menu checkbox reflection ----------------------------------------
    def _sync_menu(self):
        act = getattr(self, "_act_mute", None)
        if act is not None:
            act.setChecked(getattr(self, "_is_muted", False))
