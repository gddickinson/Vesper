"""Settings persistence for the MainWindow (a mixin).

Split out of ``window.py`` to keep it under the file-size limit: this holds the
two halves of round-tripping the user's preferences through
:mod:`breathsim.store` — ``_restore_settings`` (reopen in the last-used mode /
volume / view / toggles, suiting the clock when nothing is saved) and
``_persist_settings`` (gather the live state into the settings dict on close).
All state still lives on the engine / controller / window; these just (de)serialise.
"""
from __future__ import annotations

from breathsim import modes, store


class _SettingsMixin:
    def _restore_settings(self):
        """Reopen in the last-used mode, volume, speed and view (store)."""
        s = store.load_settings()
        self._speech_speed = float(s.get("speech_speed", self._speech_speed))
        self.toggle_hourglass(bool(s.get("hourglass", False)))
        self.set_face_cat(bool(s.get("face_cat", False)))
        self.set_face_style(s.get("face_style", "Default"))    # cyberpunk render style
        self.set_face_reactive(bool(s.get("face_reactive", False)))   # reactive face
        self._char_voices = bool(s.get("character_voices", True))   # before set_character
        self.set_character(s.get("character", "Cat"))         # 2D character + costume
        self.set_costume(s.get("costume", "None"))
        self._clock_light = bool(s.get("clock_light", True))   # time-of-day warmth
        self._mood_on = bool(s.get("mood_checkins", False))    # opt-in mood check-ins
        self._gratitude_on = bool(s.get("gratitude", False))   # opt-in bedtime gratitude
        from . import greeting                                  # optional spoken greeting
        self._listener_name = greeting.sanitize_name(s.get("listener_name", ""))
        self.set_calm_visuals(bool(s.get("calm_visuals", False)))   # reduce-motion (a11y)
        self._onboarded = bool(s.get("onboarded", False))      # first-run welcome shown?
        self._spatial = bool(s.get("spatial", True))           # ambience stereo width
        self.engine.set_spatial(self._spatial)
        self._space = s.get("space", "Off")                    # master reverb space
        self.engine.set_space(self._space)
        self._story_bg_follow = bool(s.get("story_bg", True))   # backdrop follows tale
        self._story_char_follow = bool(s.get("story_char", False))  # character per scene
        self.set_text_scale(float(s.get("font_scale", 1.0)))   # accessibility text size
        self._amb_rotate = bool(s.get("ambience_rotate", False))  # opt-in bed rotation
        self._quiet_hours = bool(s.get("quiet_hours", True))      # late-night soften
        self._apply_quiet_cap()
        self._coach = bool(s.get("breath_coach", False))         # opt-in count cue
        self._intro_on = bool(s.get("intro_lead_in", True))      # gentle settle-in lead-in
        self._settle = bool(s.get("settle_in", False))           # ease-to-resonance pacing
        self._breath_swell = bool(s.get("breath_swell", False))  # bed swells with breath
        self._llm_ollama = bool(s.get("llm_ollama", False))      # opt-in local Ollama
        if self._llm_ollama:                                     # honour the saved opt-in
            from breathsim import llm
            llm.enable_ollama(True)
        self._dramatize = bool(s.get("dramatize", False))        # cast book reading
        self._cast_expressive = bool(s.get("cast_expressive", False))
        mode = s.get("mode")                          # no saved mode -> suit the clock
        if mode not in modes.names():
            from . import clocktheme
            mode = clocktheme.suggested_mode_for_hour(clocktheme.now_hour())
        self.apply_mode(mode if mode in modes.names() else "Sleep")
        if "volume" in s:
            self.set_volume(float(s["volume"]))
            self.panel.sync()
        self.set_view(s.get("view", "face"))   # bg is themed per-mode in apply_mode

    def _persist_settings(self):
        """Gather the live preferences into the settings store (called on close)."""
        store.save_settings({"mode": self.current_mode,
                             "volume": self.user_volume,
                             "speech_speed": self._speech_speed,
                             "view": self._view, "face_bg": self._face_bg,
                             "face_style": getattr(self, "_face_style", "Default"),
                             "face_reactive": getattr(self, "_face_reactive", False),
                             "character": getattr(self, "_character", "Cat"),
                             "costume": getattr(self, "_costume", "None"),
                             "character_voices": getattr(self, "_char_voices", True),
                             "hourglass": self._hg_show,
                             "face_cat": self.face.uses_cat(),
                             "clock_light": self._clock_light,
                             "mood_checkins": self._mood_on,
                             "gratitude": getattr(self, "_gratitude_on", False),
                             "listener_name": getattr(self, "_listener_name", ""),
                             "calm_visuals": getattr(self, "_calm_visuals", False),
                             "onboarded": getattr(self, "_onboarded", False),
                             "spatial": getattr(self, "_spatial", True),
                             "font_scale": getattr(self, "_font_scale", 1.0),
                             "ambience_rotate": getattr(self, "_amb_rotate", False),
                             "quiet_hours": getattr(self, "_quiet_hours", True),
                             "breath_coach": getattr(self, "_coach", False),
                             "intro_lead_in": getattr(self, "_intro_on", True),
                             "settle_in": getattr(self, "_settle", False),
                             "breath_swell": getattr(self, "_breath_swell", False),
                             "llm_ollama": getattr(self, "_llm_ollama", False),
                             "dramatize": getattr(self, "_dramatize", False),
                             "cast_expressive": getattr(self, "_cast_expressive", False),
                             "last_scene": self._story_scene or ""})
