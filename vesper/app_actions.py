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
    def _remember_mode_pref(self, key, name):
        """Record an explicit user voice/ambience choice for the current mode."""
        mode = getattr(self, "current_mode", None)
        if mode and not getattr(self, "_applying_mode", False):
            from breathsim import store
            store.set_mode_pref(mode, key, name)

    def set_voice_a(self, name):
        self.engine.set_voice_a(_norm(name))
        self._remember_mode_pref("voice", name)

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
        self._remember_mode_pref("ambience", name)

    def set_effect(self, name):
        self.engine.set_layer("effects", _norm(name),
                              level=self.engine.slot_levels.get("effects", 0.85))

    def set_slot_level(self, slot, level):
        self.engine.set_slot_level(slot, float(level))

    def set_spatial(self, on):
        """Toggle the gentle ambience stereo width / auto-pan (persisted)."""
        self._spatial = bool(on)
        self.engine.set_spatial(self._spatial)

    def set_settle(self, on):
        """Ease-to-resonance: gently lead the breath from a comfortable, faster
        rate down to the chosen (slower) pattern over the first couple of minutes,
        then hold — a kinder entry to slow / resonance breathing. Opt-in; persisted.
        Arms now if a session is already running, else at the next fresh start."""
        self._settle = bool(on)
        if on and self.controller.running:
            self.director.start_settle(self.controller.pattern)
        elif not on:
            self.director.stop_settle()

    def set_breath_swell(self, on):
        """Toggle the **breathing soundscape**: the ambience bed gently rises with
        the inhale and softens on the exhale — a soft auditory pacer (the read each
        frame happens in `_apply_soundscape`; turning off restores the flat bed).
        Opt-in; persisted."""
        self._breath_swell = bool(on)

    def show_xtts_setup(self):
        """Explain / point at the opt-in high-quality XTTS voice engine."""
        from PySide6.QtWidgets import QMessageBox
        from breathsim import xtts_tts
        if xtts_tts.ready():
            msg = ("High-quality XTTS voices are installed.\n\n"
                   "Choose one from the Sleep ▸ Narration voice list "
                   "(the “High quality (XTTS)” groups). Characters will also "
                   "speak in their XTTS voice.")
        else:
            msg = ("Optional high-quality neural voices (XTTS-v2) are not installed.\n\n"
                   "They are a large (~5 GB), non-commercial (Coqui CPML) add-on you "
                   "can install yourself:\n\n"
                   "    python tools/setup_xtts.py --accept-license\n\n"
                   "Needs Python 3.9–3.12 and FFmpeg (brew install ffmpeg). Then "
                   "restart Vesper and pick an ‘XTTS’ narration voice. "
                   "See docs/XTTS.md.")
        QMessageBox.information(self, "High-quality voices (XTTS)", msg)

    def set_space(self, name):
        """Select the master reverb 'space' (Off / Room / Hall / Cathedral) and
        persist it. A little hall makes chants and singing sound real."""
        self._space = name
        self.engine.set_space(name)
        from breathsim import store
        store.save_settings({"space": name})
        self.status.showMessage(f"Space: {name}", 2500)

    def toggle_layer(self, slot, on):
        self.engine.set_slot_muted(slot, not on)

    # --- saved soundscapes (a light sound-only mix) -----------------------
    def save_soundscape(self, name):
        from breathsim import store
        from . import soundscape_presets as sp
        if not name:
            return
        store.save_soundscape(name, sp.capture(self))
        self.status.showMessage(f"Saved soundscape: {name}", 3000)

    def recall_soundscape(self, name):
        from breathsim import store
        from . import soundscape_presets as sp
        mix = store.get_soundscape(name)
        if mix:
            sp.apply(self, mix)
            self.status.showMessage(f"Soundscape: {name}", 3000)
            self.panel.sync()

    def delete_soundscape(self, name):
        from breathsim import store
        if name:
            store.delete_soundscape(name)

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

    def set_chant_style(self, style):
        """'per_phrase' (whole phrase per breath) or 'per_breath' (one syllable)."""
        self.engine.set_chant_style(style)

    def set_chant_recite(self, on):
        """Reciting tone: chant on a steady tonic (vs. the melodic pitches)."""
        self.engine.set_chant_recite(bool(on))

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

    def start_course_day(self, name):
        """Begin the next (or current) day of a multi-night course, reusing the
        normal session machinery; the day advances only when the sit completes."""
        from breathsim import courses, store
        course = courses.get(name)
        if not course:
            return
        total = course.total
        day = store.course_day(name)
        idx = day if day < total else total - 1      # completed -> replay last day
        courses.apply_day(self, course, idx)
        self._active_course = (name, total)
        self.status.showMessage(
            f"{name} - {courses.day_label(course, idx)}", 6000)

    def restart_course(self, name):
        from breathsim import store
        store.reset_course(name)
        self.start_course_day(name)

    def tonights_pick(self):
        """One-tap: pick a random bedtime lecture (avoiding recent ones), arm it
        as the Sleep story and begin. Reuses the normal story-start plumbing."""
        from breathsim import stories, store, tonight
        name = tonight.pick(stories.lecture_names(), store.recent_picks())
        if not name:
            return
        store.push_recent_pick(name)
        if self.current_mode != "Sleep":
            self.apply_mode("Sleep")
        self.set_story(name)                          # arms _story_scene + ambience
        self._ensure_running()                        # start the Sleep session + story
        self.status.showMessage(f"Tonight's pick: {name}", 5000)
        self.panel.sync()

    def surprise_in_branch(self, category):
        """One-tap: pick a random lecture from one *category* (avoiding recent
        ones), arm it as the Sleep story and begin. Like tonights_pick, but
        themed. Returns the chosen name (or None if the branch is empty)."""
        from breathsim import branchpick, store
        name = branchpick.pick_in_branch(category, store.recent_picks())
        if not name:
            return None
        store.push_recent_pick(name)
        if self.current_mode != "Sleep":
            self.apply_mode("Sleep")
        self.set_story(name)
        self._ensure_running()
        self.status.showMessage(f"From {category}: {name}", 5000)
        self.panel.sync()
        return name

    def toggle_favourite_voice(self):
        """Star/unstar the current inhale voice for quick access (persisted)."""
        name = self.engine.voice_a
        if not name:
            return
        from breathsim import store
        favs = store.toggle_favourite(name)
        self.status.showMessage(
            f"{'Starred' if name in favs else 'Unstarred'} {name}", 3000)
        self.rebuild_menu()

    def set_sleep_timer(self, minutes):
        """Arm (or clear, minutes<=0) the sleep auto-stop: after the chosen time
        the sound gently fades out and transport pauses. Counts from now."""
        self._sleep_timer_min = float(minutes)
        self._sleep_timer_t0 = self.controller.elapsed()
        self._sleep_timer_done = False
        if self._sleep_timer_min > 0:
            self.status.showMessage(
                f"Sleep timer set for {int(self._sleep_timer_min)} min", 4000)
        else:
            self.status.showMessage("Sleep timer off", 3000)
        self.panel.sync()

    def start_fall_asleep(self, minutes=40.0):
        """One tap to drift off: Sleep mode + a slow long-exhale breath + the
        wind-down + a sleep-timer + (if available) the storyteller, then begin.
        Composes existing features; Reset or switching modes returns to normal."""
        self.apply_mode("Sleep")
        p = preset_by_name("Calming 4-6 (Long Exhale)")
        if p:
            self.controller.change_pattern(p)         # gentle long exhale to start
        self.set_winddown(True, minutes)              # slow the breath + fade over time
        self.set_sleep_timer(min(float(minutes), 45.0))   # gentle auto-stop
        self._ensure_running()                        # start (also starts the storyteller)
        self.status.showMessage(
            "Falling asleep - winding down gently. Rest well.", 5000)
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

    def start_sunrise(self, minutes=15.0):
        """A gentle dawn wake-up: over *minutes* the breath quickens (slow->normal),
        the volume rises (quiet->full), the view brightens (warm dim->clear) and a
        soft morning bed fades in - the inverse of the Sleep wind-down."""
        a = preset_by_name("Extended 7-11") or self.controller.pattern
        b = preset_by_name("Coherent 5.5 (Resonance)") or a
        self.controller.change_pattern(a)
        self.controller.session_seconds = float(minutes) * 60.0
        self.director.start_wake(float(minutes) * 60.0, a, b)
        self.engine.set_voice("Forest Wind", "ambience")     # a gentle dawn chorus bed
        self._ensure_running()
        self.controller.restart()                            # ramp from t=0
        self.engine.set_master_volume(self.user_volume * 0.15)
        self.engine.trigger_chime("in")                      # a soft waking chime
        self.panel.sync()

    def _ensure_running(self):
        if not self.controller.running:
            self.toggle_transport()

    def set_gratitude(self, on):
        """Toggle the opt-in bedtime 'one good thing' prompt (persisted)."""
        self._gratitude_on = bool(on)
        from breathsim import store
        store.save_settings({"gratitude": self._gratitude_on})

    def gratitude_now(self):
        """Offer the gratitude note on demand (any time, any mode)."""
        from . import gratitude
        gratitude.ask_gratitude(self)

    def set_listener_name(self, name):
        """Set (and persist) the optional spoken-greeting name. Sanitised to a
        short plain-ASCII first name; '' = off. Returns the stored value."""
        from . import greeting
        self._listener_name = greeting.sanitize_name(name)
        from breathsim import store
        store.save_settings({"listener_name": self._listener_name})
        return self._listener_name

    def ask_listener_name(self):
        """Open the little 'greet me by name' dialog (Sessions menu)."""
        from . import greeting
        greeting.ask_name(self)

    def set_weather(self, kind):
        """Optional particle weather overlay (off / snow / leaves / bubbles / fireflies)."""
        self.viz.set_weather(kind)

    def set_calm_visuals(self, on):
        """Accessibility 'reduce motion' (persisted, off by default): eases the
        decorative drift/twinkle and drops the weather overlay; the breathing orb
        + guide dot stay responsive."""
        self._calm_visuals = bool(on)
        self.viz.set_calm(self._calm_visuals)
        from breathsim import store
        store.save_settings({"calm_visuals": self._calm_visuals})

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
