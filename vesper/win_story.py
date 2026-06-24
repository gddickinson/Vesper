"""Storyteller, speech pacing, mood check-ins, ambience-follow, settle-in
lead-in, practice log and mood-easing for MainWindow (a mixin), split from
window.py. State lives on the engine / controller / narrator; these translate
story + session flow into core calls."""
from __future__ import annotations

from breathsim import sound_cues, stories, store

from .face_motion import emotion_for_text


class _StoryMixin:
    def set_story(self, scene):
        self._story_scene = None if scene in (None, "Off") else scene
        if self._story_scene:
            self._set_base_ambience(stories.ambience_for(self._story_scene))
            from . import story_bg
            self._story_bg_base = story_bg.base_for_scene(self._story_scene)
            self._story_bg_target = self._story_bg_base    # picture follows the tale
            self._bg_idle = 0
        else:
            self._restore_user_character()                 # story cleared
        if self.controller.running:
            self._start_story()

    def set_story_char_follow(self, on):
        """Sound/Face toggle: the cartoon character matches the story scene
        (persisted, default off). Restores the user's own character when off."""
        self._story_char_follow = bool(on)
        from breathsim import store
        store.save_settings({"story_char": self._story_char_follow})
        if not self._story_char_follow:
            self._restore_user_character()
        elif self._story_scene and self.controller.running:
            self._apply_story_character()

    def _apply_story_character(self):
        """When enabled and the cartoon face is shown, set the character to fit the
        scene (without overwriting the user's saved pick)."""
        if not getattr(self, "_story_char_follow", False) or not self._story_scene:
            return
        if not self.face.uses_cat():                       # only the 2D face shows it
            return
        from . import story_char
        target = story_char.char_for_scene(self._story_scene)
        if target and target != self.face.character():
            self.set_character(target, persist=False)
            self._story_char_active = True

    def _restore_user_character(self):
        """Put the user's chosen character back after a story-driven swap."""
        if getattr(self, "_story_char_active", False):
            self.set_character(getattr(self, "_character", "Cat"), persist=False)
            self._story_char_active = False

    def set_story_voice(self, v):
        self.narrator.set_voice(v)
        if self._story_scene and self.controller.running:
            self._start_story()

    def set_speech_speed(self, v):
        """Base storyteller speed (1.0 = normal); it still slows over the session."""
        self._speech_speed = max(0.6, min(1.2, float(v)))

    def _apply_speech_pace(self):
        """Subtly slow the speech + lengthen the between-statement pauses as the
        session goes on (gentle wind-down over ~10 minutes)."""
        prog = min(1.0, self.controller.elapsed() / 600.0)
        rate = getattr(self, "_char_rate", 1.0)             # the character's own pace
        self.narrator.speed = self._speech_speed * rate * (1.0 - 0.18 * prog)
        self.narrator.pause_scale = self._pause_scale * (1.0 + 0.5 * prog)

    def set_mood_checkins(self, on):
        self._mood_on = bool(on)

    def _after_mood(self):
        """Offer the 'after' mood check-in once, if a real non-Sleep sit ended."""
        if self._mood_after_done or self.current_mode == "Sleep":
            return
        if self.controller.elapsed() < 60:
            return
        self._mood_after_done = True
        from . import mood
        mood.maybe_check_in(self, "after")

    def _note_if_silent(self):
        """If the audio device could not be opened, gently say so once, so a
        visual-only session doesn't seem broken. The breath/visuals carry on."""
        if getattr(self, "_silent_noted", False):
            return
        if not getattr(self.engine, "available", True):
            self._silent_noted = True
            self.status.showMessage("Audio unavailable - visual only", 6000)

    def _arm_intro(self, fresh):
        """A gentle settle-in lead-in over the first breath, so the first inhale
        isn't abrupt. Only on a fresh start, and not when a storyteller is about
        to speak (its narration is its own lead-in). Purely on-screen text."""
        self._intro_sched = []
        story_narrating = bool(self._story_scene and self.narrator.available)
        if fresh and self._intro_on and not story_narrating:
            from breathsim import intro
            self._intro_sched = intro.schedule(self.controller.pattern.cycle)

    def set_intro_lead_in(self, on):
        """Toggle the settle-in lead-in (persisted); clears any active one."""
        self._intro_on = bool(on)
        if not self._intro_on:
            self._intro_sched = []

    def _intro_text(self):
        """The gentle settle-in line to show now, or '' once the lead-in is over."""
        sched = getattr(self, "_intro_sched", None)
        if not sched or not self.controller.running:
            return ""
        from breathsim import intro
        line = intro.line_at(sched, self.controller.elapsed())
        if line is None:
            self._intro_sched = []                   # finished -> normal status resumes
            return ""
        return line

    def _log_practice(self):
        """Record a completed sit (≥30 s) to the practice history, once."""
        if not self._logged_session and self.controller.elapsed() >= 30:
            p = self.controller.pattern                # log the session's pace (bpm)
            cycle = p.inhale + p.hold_full + p.exhale + p.hold_empty
            bpm = 60.0 / cycle if cycle > 0 else None
            store.log_session(self.controller.elapsed() / 60.0, bpm)
            self._logged_session = True
            ac = getattr(self, "_active_course", None)
            if ac:                                  # a course day completed -> advance
                store.advance_course(ac[0], ac[1])
                self._active_course = None
            if self.current_mode != "Sleep":        # a gentle "well done" (not for sleepers)
                from breathsim import welldone
                cur, _best = store.streak()
                self._closing_msg = welldone.message(
                    self.controller.elapsed() / 60.0, cur)

    def _start_story(self):
        if not (self._story_scene and self.narrator.available
                and self.controller.running):
            return
        start = 0                                      # resume a long lecture, gently
        from breathsim import lectures, resume, store
        total = lectures.section_count(self._story_scene)
        if total:
            import datetime as _dt
            start = resume.start_section(
                store.get_lecture_progress(self._story_scene), total, _dt.date.today())
            if start:
                self.status.showMessage(
                    f"Resuming \"{self._story_scene}\" partway through", 4000)
        self._last_logged_section = start - 1          # so the first new section logs
        units = stories.story_units(self._story_scene, guidance=True,
                                    start_section=start)
        self.narrator.start(units, self._story_level, self._story_timing,
                            self._on_story_unit)
        self._apply_story_character()                   # the teller looks the part
        store.save_settings({"last_scene": self._story_scene})   # remember for next launch

    def _set_base_ambience(self, amb):
        """Set the story's signature ambience bed + reset the sound-cue tracker."""
        self._base_ambience = amb
        self._cur_ambience = amb
        self._sfx_target = amb
        self._sfx_idle = 0
        if amb:
            self.engine.set_voice(amb, "ambience")

    def _on_story_unit(self, unit):
        """Per narrated line: show it, steer the soundscape, set the face's mood."""
        text = unit.get("text", "")
        self._story_line = text
        sec = unit.get("section")                       # track lecture progress (throttled)
        if sec is not None and sec != getattr(self, "_last_logged_section", -1):
            self._last_logged_section = sec
            from breathsim import lectures, store
            total = lectures.section_count(self._story_scene)
            if total and sec >= total - 1:             # finished -> clear so it starts fresh
                store.clear_lecture_progress(self._story_scene)
            else:
                store.set_lecture_progress(self._story_scene, sec)
        if unit.get("kind") in ("shuffle", "hypnosis", "poem"):
            # Shuffle nouns / hypnosis / poems shouldn't steer the bed; hold it.
            self._mood_target = (0.0, 0.0, 0.0)
            return
        cue = sound_cues.cue_for_text(text)
        if cue:
            self._sfx_target = cue              # imagery → morph the bed toward it
            self._sfx_idle = 0
        else:
            self._sfx_idle += 1
            if self._sfx_idle >= 4 and self._base_ambience:
                self._sfx_target = self._base_ambience   # drift home over abstract lines
        from . import story_bg                  # the backdrop follows the words too
        bg = story_bg.bg_for_text(text)
        if bg:
            self._story_bg_target = bg
            self._bg_idle = 0
        else:
            self._bg_idle = getattr(self, "_bg_idle", 0) + 1
            if self._bg_idle >= 4:             # ease home to the scene base
                self._story_bg_target = getattr(self, "_story_bg_base", "Stars")
        self._mood_target = emotion_for_text(text)

    def set_ambience_rotate(self, on):
        """Toggle ambience auto-rotate (opt-in, persisted); slowly cycles beds."""
        self._amb_rotate = bool(on)

    def _apply_ambience_rotate(self):
        """Crossfade the ambience slot to the curated bed for the current elapsed
        time (every ~6 min), reusing the engine's gain-ramped crossfade."""
        from breathsim import ambrotate, voices
        beds = [b for b in ambrotate.BEDS if voices.get_voice(b)]
        target = ambrotate.next_ambience(beds, self.controller.elapsed())
        if target and target != self.engine.slot_voice.get("ambience"):
            self.engine.set_voice(target, "ambience", fade=3.0)

    def set_story_bg_follow(self, on):
        """Sound ▸ Backdrop follows the story toggle (persisted, default on). When
        off, the current backdrop is simply left as-is (the mode's own)."""
        self._story_bg_follow = bool(on)
        from breathsim import store
        store.save_settings({"story_bg": self._story_bg_follow})

    def _apply_story_bg(self):
        """Gently crossfade the face backdrop toward the story's current theme (a
        slow ~4 s fade so it never startles); eases home to the scene's base over
        abstract passages. Off, or outside a story, leaves the backdrop alone."""
        if not getattr(self, "_story_bg_follow", True) or not self._story_scene:
            return
        target = getattr(self, "_story_bg_target", None)
        if target and target != getattr(self, "_cur_story_bg", None):
            self.face.set_background(target, fade=4.0)
            self._cur_story_bg = target

    def set_soundscape_follow(self, on):
        """Sound ▸ Soundscape follows story toggle. Off → hold the base ambience."""
        self._soundscape_follow = bool(on)

    def _apply_soundscape(self):
        """Drive the single ambience-level writer each frame: crossfade toward the
        text-matched target and DUCK on a swap (a cue blooms in rather than jumps),
        and — when enabled — a gentle **breath swell** (the bed rises with the inhale
        and softens on the exhale, a soft auditory pacer). Duck * swell combine so
        the two can never fight over the level. Follow off -> ease home to the base."""
        amb = self.engine.slot_levels.get("ambience", 0.8)   # user's base level
        target = (self._sfx_target if self._soundscape_follow
                  else self._base_ambience)
        if target and target != self._cur_ambience:
            self.engine.set_voice(target, "ambience", fade=2.5)
            self._cur_ambience = target
            self._duck_t0 = self._anim_t                     # start the duck
        duck = 1.0                                           # 0.5 just after a cue swap
        if self._duck_t0 is not None:
            u = (self._anim_t - self._duck_t0) / 1.8
            if u >= 1.0:
                self._duck_t0 = None
            else:
                e = u * u * (3.0 - 2.0 * u)                  # smoothstep recovery
                duck = 0.5 + 0.5 * e
        self.engine.set_layer_level("ambience", amb * duck * self._breath_swell_factor())

    def _breath_swell_factor(self):
        """1.0 normally; when the breath swell is on, dip toward 1-depth on the
        exhale and back to 1.0 at the top of the inhale (follows lung fullness)."""
        if not getattr(self, "_breath_swell", False):
            return 1.0
        vol = max(0.0, min(1.0, self.controller.current_state().volume))
        return 1.0 - 0.22 * (1.0 - vol)                      # depth 0.22 (subtle)

    def _ease_mood(self, running):
        """Ease the expression toward the line's emotion (decaying to calm)."""
        ds, db, do = self._mood_target if running else (0.0, 0.0, 0.0)
        self._smile += (0.12 + ds - self._smile) * 0.06
        self._brow += (db - self._brow) * 0.06
        self._eyeb += (do - self._eyeb) * 0.06
        self._mood_target = tuple(v * 0.992 for v in self._mood_target)

    # --- reactive face (optional): style follows mode / chant / story mood, and
    # the eyes/rim breathe with the live breath. Off by default; never changes the
    # saved static style (restored when the toggle is turned off).
    def set_face_reactive(self, on):
        self._face_reactive = bool(on)
        if not self._face_reactive:
            self.face.set_style(getattr(self, "_face_style", "Default"))
            self.face.set_pulse(1.0)
            self._react_on = False

    def _react_face(self, state, running):
        if not getattr(self, "_face_reactive", False):
            return
        from . import face_react
        if not running:                              # idle: hold saved style, no pulse
            if getattr(self, "_react_on", False):
                self.face.set_style(getattr(self, "_face_style", "Default"))
                self.face.set_pulse(1.0)
                self._react_on = False
            return
        self._react_on = True
        self.face.set_pulse(face_react.pulse_for(getattr(state, "volume", 0.5)))
        target = face_react.style_for(
            self.current_mode, chanting=self.current_mode == "Chant",
            singing=self.current_mode == "Sing",
            story_active=bool(self._story_scene),
            mood=face_react.mood_key(getattr(self, "_mood_target", (0.0, 0.0, 0.0))))
        if target == getattr(self, "_react_pending", None):    # dwell, so it never flickers
            self._react_dwell = getattr(self, "_react_dwell", 0) + 1
        else:
            self._react_pending, self._react_dwell = target, 0
        if self._react_dwell >= 18 and target != self.face.style():
            self.face.set_style(target)

    def _story_level(self):
        dur = self._story_minutes * 60.0
        frac = self.controller.elapsed() / dur if dur > 0 else 1.0
        if frac < 0.55:
            return 1.0
        return 0.0 if frac >= 0.85 else 1.0 - (frac - 0.55) / 0.30

    def _story_timing(self):
        p = self.controller.pattern
        return (max(0.5, p.inhale), max(0.5, p.exhale))
