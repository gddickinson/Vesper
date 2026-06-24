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
        if self.controller.running:
            self._start_story()

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
        self.narrator.speed = self._speech_speed * (1.0 - 0.18 * prog)
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

    def set_soundscape_follow(self, on):
        """Sound ▸ Soundscape follows story toggle. Off → hold the base ambience."""
        self._soundscape_follow = bool(on)

    def _apply_soundscape(self):
        """Crossfade the ambience toward the text-matched target and gently DUCK
        the bed as it swaps, so a cue blooms in rather than jumps. When the follow
        toggle is off, ease home to the story's base ambience and hold it."""
        amb = self.engine.slot_levels.get("ambience", 0.8)   # user's base level
        target = (self._sfx_target if self._soundscape_follow
                  else self._base_ambience)
        if target and target != self._cur_ambience:
            self.engine.set_voice(target, "ambience", fade=2.5)
            self._cur_ambience = target
            self._duck_t0 = self._anim_t                     # start the duck
            self.engine.set_layer_level("ambience", amb * 0.5)
        if self._duck_t0 is not None:                        # ease the bed back up
            u = (self._anim_t - self._duck_t0) / 1.8
            if u >= 1.0:
                self.engine.set_layer_level("ambience", amb)
                self._duck_t0 = None
            else:
                e = u * u * (3.0 - 2.0 * u)                  # smoothstep recovery
                self.engine.set_layer_level("ambience", amb * (0.5 + 0.5 * e))

    def _ease_mood(self, running):
        """Ease the expression toward the line's emotion (decaying to calm)."""
        ds, db, do = self._mood_target if running else (0.0, 0.0, 0.0)
        self._smile += (0.12 + ds - self._smile) * 0.06
        self._brow += (db - self._brow) * 0.06
        self._eyeb += (do - self._eyeb) * 0.06
        self._mood_target = tuple(v * 0.992 for v in self._mood_target)

    def _story_level(self):
        dur = self._story_minutes * 60.0
        frac = self.controller.elapsed() / dur if dur > 0 else 1.0
        if frac < 0.55:
            return 1.0
        return 0.0 if frac >= 0.85 else 1.0 - (frac - 0.55) / 0.30

    def _story_timing(self):
        p = self.controller.pattern
        return (max(0.5, p.inhale), max(0.5, p.exhale))
