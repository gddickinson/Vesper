"""MainWindow — the PySide6 app. Reuses the breathsim core; the face is central.

Phase 1 of the rebuild: a working session runner with the faceView face
breathing + lip-syncing the bedtime story, a mode bar, transport, volume, a
render-mode picker and Sleep story controls. The audio/logic (engine, controller,
voices, patterns, modes, narration, stories, Kokoro) is the unchanged core.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                               QStackedWidget, QWidget)

from breathsim import choir, modes, narration, personas, sound_cues, stories
from breathsim import story_db
from breathsim import controller as ctrl_mod
from breathsim import engine as eng_mod
from breathsim import session as sess_mod
from breathsim import speech as sp_mod
from breathsim import store
from breathsim.patterns import DEFAULT_PATTERN, preset_by_name

from . import menus, shortcuts, theme
from .app_actions import _ActionsMixin
from .controls import ControlPanel
from .face import FaceWidget
from .face_motion import breath_routing, emotion_for_text, sample_inhale_open
from .pitch import _PitchMixin
from .viz import VizWidget
from .win_hourglass import _HourglassMixin

FPS = 40

# Talking takes precedence over breathing. A voiced frame means the storyteller
# is exhaling words; a gap means a breath before the next sentence.
_AMP_TH = 0.06          # narration amp above this counts as "voicing now"
_SPEAK_HOLD = 0.35      # s: short word/syllable gaps still count as speaking
_TALK_WINDOW = 9.0      # s of silence after which we revert to plain breathing
_BREATH_EASE = 0.08     # per-frame easing of the speech-driven visible breath

# Each window gets a fitting backdrop behind the face (kept to its theme).
_MODE_BG = {"Meditate": "Gradient", "Breathwork": "Aurora", "Chant": "Nebula",
            "Sing": "Aurora", "Relax": "Underwater", "Sleep": "Stars"}


class MainWindow(_ActionsMixin, _PitchMixin, _HourglassMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vesper")
        self.resize(1060, 720)
        self.setStyleSheet(theme.STYLESHEET)

        store.register_all()                       # merge saved patterns/voices
        try:
            story_db.build()                       # refresh the stories database
        except Exception:
            pass
        self.controller = ctrl_mod.BreathController(DEFAULT_PATTERN)
        self.engine = eng_mod.AudioEngine(self.controller)
        self.speech = sp_mod.SpeechCue()
        self.narrator = narration.Narrator(self.speech)
        self.director = sess_mod.SessionDirector(self)
        self.user_volume = 0.6
        self._is_muted = False
        self._zen = False
        self._scene_hint = "orb"
        self._view = "face"                 # central view: "face" or "scene"
        self._face_bg = "Stars"            # animated background behind the face
        self.tuner = None                   # lazy mic pitch monitor (Sing/Chant)
        self._pitch_spec = None
        self._bell_interval = 0.0           # mindfulness bell interval (minutes)
        self._next_bell = 0.0
        self._hold_t0 = None                # breath-hold (retention) timer
        self._hold_last = 0.0
        self._logged_session = False
        self._anim_t = 0.0
        self._last_phase = None
        self._last_speak_t = -1e9          # anim time of the last voiced frame
        self._face_breath = 0.5            # speech-driven visible breath (eased)
        self._inhale_open = 0.3            # per-breath mouth-parting scale (0..1)
        self._was_speaking = False         # for detecting between-sentence breaths
        self._speech_speed = 1.0           # user speech-speed setting (slider)
        self._pause_scale = 1.4            # base between-statement pause multiplier
        self._story_scene = None
        self._story_line = ""
        self._story_minutes = 20.0
        self._base_ambience = None         # the story's signature ambience bed
        self._cur_ambience = None          # what's playing now (cues morph it)
        self._sfx_target = None            # ambience the text currently calls for
        self._sfx_idle = 0                 # lines since the last imagery cue
        self._soundscape_follow = True     # ambience follows the story's words?
        self._duck_t0 = None               # in-progress ambience-duck start time
        self._mood_target = (0.0, 0.0, 0.0)   # emotion deltas from the current line
        self._smile, self._brow, self._eyeb = 0.12, 0.0, 0.0   # eased expression
        self._sing_in = 0                  # pitch-trainer: frames sung in tune
        self._sing_tot = 0                 # frames voiced (for the % score)
        self._med_style = "Off"            # Meditate guidance style
        self._hg_show = False              # hourglass session timer visible?
        self._hg_spin = 0.0                # current displayed glass rotation (deg)
        self._hg_spin_from = 0.0           # flip animation endpoints + start time
        self._hg_spin_to = 0.0
        self._hg_spin_t0 = None
        self.current_mode = None
        self._font_scale = 1.0             # accessibility: global UI text size
        self._base_pt = 0.0                # app font point size before any scaling
        self._active_course = None         # (course name, total) while a course day runs
        self._sleep_timer_min = 0.0        # sleep auto-stop: 0 = off (default each launch)
        self._sleep_timer_t0 = 0.0         # elapsed when the timer was armed
        self._sleep_timer_done = False
        self._mood_on = False              # optional mood check-ins (opt-in; off by default)
        self._mood_after_done = False

        accents = self.speech.accent_voices()
        if accents:                                  # default cues to a UK female
            uk_fem = ("Serena", "Stephanie", "Kate", "Martha", "Jamie")
            pick = next((vid for _d, vid in accents
                         if vid.split(" (")[0] in uk_fem), accents[0][1])
            self.speech.set_voice(pick)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        self.face = FaceWidget()
        self.viz = VizWidget()
        self.face._hg_click_cb = self._flip_hourglass    # tap the timer to flip it
        self.viz._hg_click_cb = self._flip_hourglass
        self.stack = QStackedWidget()
        self.stack.addWidget(self.face)            # index 0
        self.stack.addWidget(self.viz)             # index 1
        self.panel = ControlPanel(self)
        lay.addWidget(self.stack, 1)
        lay.addWidget(self.panel, 0)
        self.setCentralWidget(central)
        self.status = self.statusBar()
        menus.build(self)
        shortcuts.bind(self)

        self.engine.start()
        self.engine.set_master_volume(0.0)
        self._restore_settings()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(int(1000 / FPS))

        from . import onboarding              # gentle first-launch welcome (once)
        onboarding.maybe_show(self)

        from . import clocktheme, suggest             # a gentle, non-modal launch hint
        self._started_once = False
        try:
            self._launch_suggestion = suggest.suggest(
                clocktheme.now_hour(), store.history(), store.course_state()).text
        except Exception:
            self._launch_suggestion = None

    def rebuild_menu(self):
        menus.build(self)

    def set_text_scale(self, scale):
        """Accessibility: scale all UI text (app font + the stylesheet font sizes,
        which dialogs and menus inherit). Persisted; a readability setting only."""
        from . import fontscale
        scale = float(scale)
        self._font_scale = scale
        app = QApplication.instance()
        if app is not None:
            f = app.font()
            if self._base_pt <= 0:                       # capture the unscaled size once
                self._base_pt = f.pointSizeF() if f.pointSizeF() > 0 else 13.0
            f.setPointSizeF(max(6.0, self._base_pt * scale))
            app.setFont(f)
        self.setStyleSheet(fontscale.scaled_css(theme.STYLESHEET, scale))

    def _restore_settings(self):
        """Reopen in the last-used mode, volume, speed and view (store)."""
        s = store.load_settings()
        self._speech_speed = float(s.get("speech_speed", self._speech_speed))
        self.toggle_hourglass(bool(s.get("hourglass", False)))
        self.set_face_cat(bool(s.get("face_cat", False)))
        self._clock_light = bool(s.get("clock_light", True))   # time-of-day warmth
        self._mood_on = bool(s.get("mood_checkins", False))    # opt-in mood check-ins
        self._onboarded = bool(s.get("onboarded", False))      # first-run welcome shown?
        self._spatial = bool(s.get("spatial", True))           # ambience stereo width
        self.engine.set_spatial(self._spatial)
        self.set_text_scale(float(s.get("font_scale", 1.0)))   # accessibility text size
        mode = s.get("mode")                          # no saved mode -> suit the clock
        if mode not in modes.names():
            from . import clocktheme
            mode = clocktheme.suggested_mode_for_hour(clocktheme.now_hour())
        self.apply_mode(mode if mode in modes.names() else "Sleep")
        if "volume" in s:
            self.set_volume(float(s["volume"]))
            self.panel.sync()
        self.set_view(s.get("view", "face"))   # bg is themed per-mode in apply_mode

    # --- visualization view (face ↔ scene) --------------------------------
    def set_view(self, name):
        """Switch the central area between the 3D face and the 2D scene."""
        self._view = "scene" if name == "scene" else "face"
        self.stack.setCurrentWidget(
            self.viz if self._view == "scene" else self.face)
        self.face.set_active(self._view == "face")
        self.panel.reflect_view(self._view)
        menus.reflect_view(self)

    def toggle_view(self):
        self.set_view("face" if self._view == "scene" else "scene")

    def set_face_background(self, name):
        """Pick the animated background painted behind the 3D face."""
        self._face_bg = name
        self.face.set_background(name)

    def set_face_cat(self, on):
        """Use the cartoon cat instead of the 3D head (View menu / persisted)."""
        self.face.set_use_cat(on)
        act = getattr(self, "_act_cat", None)
        if act is not None and act.isChecked() != self.face.uses_cat():
            act.setChecked(self.face.uses_cat())

    def set_scene(self, name):
        """Pick which 2D scene shows, and switch to the scene view."""
        self._scene_hint = name
        self.viz.set_scene(name)
        self.set_view("scene")

    def set_weather(self, kind):
        """Optional particle weather overlay (off / snow / leaves / bubbles / fireflies)."""
        self.viz.set_weather(kind)

    def set_clock_light(self, on):
        self._clock_light = bool(on)

    def _clock_warm(self):
        """A gentle time-of-day warmth (0 by day, warmer at night), or 0 if off."""
        if not getattr(self, "_clock_light", True):
            return 0.0
        from . import clocktheme
        return clocktheme.clock_warm_for_hour(clocktheme.now_hour())

    def _scene_ctx(self, state, running, prog):
        m, s = divmod(int(self.controller.elapsed()), 60)
        if running:
            status = f"{m:02d}:{s:02d}"
        else:
            status = "Press Start" if self.controller.elapsed() == 0 else "Paused"
        sub = (self._story_line[:42] if (self.current_mode == "Sleep"
                                         and self._story_line) else "")
        hint = ""                                  # Meditate: gentle rotating guidance
        if running and self.current_mode == "Meditate" and self._med_style != "Off":
            hint = self._med_phrase(self.controller.elapsed())
        ctx = {"running": running,
               "volume": state.volume if running else 0.5,
               "airflow": state.airflow if running else 0.0,
               "phase": state.phase, "cycle_frac": getattr(state, "cycle_frac", 0.0),
               "progress": getattr(state, "progress", 0.0),   # 0..1 through this phase
               "remaining": state.remaining, "label": state.label,
               "t": self._anim_t, "prog": prog, "subtitle": sub,
               "status": status, "hint": hint,
               "bpm": (60.0 / self.controller.pattern.cycle
                       if self.controller.pattern.cycle > 0 else 0.0)}
        if self.viz.scene_name() == "pitch":
            pc = self.pitch_context(self.controller.elapsed()) or {}
            sung, clar = (self.tuner.latest() if (self.tuner and self.tuner.available)
                          else (0.0, 0.0))
            tgt = pc.get("target")
            intune = False
            if running and tgt and sung > 0 and clar > 0.5:
                intune = abs(1200.0 * math.log2(sung / tgt)) < 30.0
                self._sing_tot += 1
                self._sing_in += 1 if intune else 0
            score = (100.0 * self._sing_in / self._sing_tot) if self._sing_tot else 0.0
            ctx["pitch"] = {**pc, "sung": sung, "clarity": clar, "tol": 30,
                            "intune": intune, "score": score,
                            "samples": self._sing_tot}
        return ctx

    # Meditate guidance — two evidence-based styles, slow rotating cues.
    _MED_CUES = {
        "Focused attention": [
            "Rest your attention on the breath.",
            "Feel the air — cool in, warm out.",
            "When the mind wanders, gently come back.",
            "No need to judge it; just return.",
            "Let the breath be your anchor.",
            "Soften the body around each breath.",
        ],
        "Open monitoring": [
            "Let awareness rest open and wide.",
            "Notice whatever arises, then let it pass.",
            "Sounds, feelings, thoughts — hold none.",
            "Be the sky; let it all drift like clouds.",
            "Nothing to fix, nothing to chase.",
            "Rest as the awareness that notices.",
        ],
    }

    def set_meditation_guidance(self, style):
        self._med_style = style if style in self._MED_CUES else "Off"

    def _med_phrase(self, elapsed):
        cues = self._MED_CUES.get(self._med_style)
        if not cues:
            return ""
        return cues[int(elapsed / 22.0) % len(cues)]   # a new cue ~every 22 s

    def save_screenshot(self, path=None, face_only=False):
        """Save a PNG of the window (or just the face). Ctrl+S / Ctrl+Shift+S."""
        pm = (self.face if face_only else self.centralWidget()).grab()
        if path is None:
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Screenshot", "breathsim.png", "PNG (*.png)")
        if path:
            pm.save(path)
            self.status.showMessage(f"Saved {path}", 3000)
        return path

    # --- modes / settings --------------------------------------------------
    def apply_mode(self, name):
        m = modes.get(name)
        if not m:
            return
        self.controller.change_pattern(preset_by_name(m.pattern) or DEFAULT_PATTERN)
        self.engine.set_persona(personas.get(m.persona))
        self.engine.set_voice_b(None)
        self.engine.set_morph(0.0)
        self.engine.set_voice_a(m.voice)
        self.engine.set_voice_out(getattr(m, "voice_out", None))
        self._set_base_ambience(m.ambience)
        self.engine.set_layer("effects", m.effect,
                              level=self.engine.slot_levels.get("effects", 0.85))
        choir.apply(self.engine, *m.choir) if m.choir else choir.clear(self.engine)
        self.speech.set_style(m.cue_style)
        self.set_volume(m.volume)
        self.controller.session_seconds = m.session
        self.director.set_mode("Manual")           # cancel any program/wind-down
        self.director.set_manual(0.0)
        self._scene_hint = m.scene
        self._pitch_spec = None                     # leave any pitch trainer
        self.set_tuner(False)
        self.viz.set_scene(m.scene)
        self.narrator.stop()
        self._story_scene = stories.scene_names()[0] if name == "Sleep" else None
        if self._story_scene:
            self._set_base_ambience(stories.ambience_for(self._story_scene))
            self._story_minutes = (m.session or 1200) / 60.0
        self.set_face_background(_MODE_BG.get(name, "Stars"))   # themed backdrop
        self.current_mode = name
        self.panel.reflect_mode(name)
        self.status.showMessage(m.description, 4000)

    def set_pattern(self, name):
        p = preset_by_name(name)
        if p:
            self.controller.change_pattern(p)

    def set_volume(self, vol):
        self.user_volume = float(vol)
        if self.controller.running and not self._is_muted:
            self.engine.set_master_volume(self.user_volume)

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

    # --- mood check-ins ----------------------------------------------------
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

    # --- transport ---------------------------------------------------------
    def toggle_transport(self):
        if self.controller.running:
            self._log_practice()
            self.controller.pause()
            self.engine.set_master_volume(0.0)
            self.narrator.stop()
            self.panel.reflect_running(False)
            self._after_mood()                       # offer it after we've paused
            return
        fresh = self.controller.elapsed() < 1.0
        self._started_once = True                     # retire the launch hint
        if fresh:
            self._sleep_timer_t0 = 0.0                # restart the sleep-timer countdown
            self._sleep_timer_done = False
            self._mood_after_done = False
            from . import mood
            mood.maybe_check_in(self, "before")      # only on a fresh start
        self.controller.start()
        self.engine.set_master_volume(0.0 if self._is_muted else self.user_volume)
        self._start_story()
        self.panel.reflect_running(self.controller.running)

    def reset(self):
        self._log_practice()
        self._after_mood()
        self.narrator.stop()
        self.controller.reset()
        self.engine.set_master_volume(0.0)
        self._last_phase = None
        self._logged_session = False
        self._next_bell = self._bell_interval * 60.0
        self._sleep_timer_t0 = 0.0             # the countdown restarts with the session
        self._sleep_timer_done = False
        self._sfx_idle = 0                     # restore the base ambience bed
        self._sfx_target = self._base_ambience
        self._mood_target = (0.0, 0.0, 0.0)
        if self._base_ambience:
            self.engine.set_voice(self._base_ambience, "ambience", fade=1.5)
            self._cur_ambience = self._base_ambience
        self.setWindowOpacity(1.0)
        self.panel.reflect_running(False)

    def _log_practice(self):
        """Record a completed sit (≥30 s) to the practice history, once."""
        if not self._logged_session and self.controller.elapsed() >= 30:
            store.log_session(self.controller.elapsed() / 60.0)
            self._logged_session = True
            ac = getattr(self, "_active_course", None)
            if ac:                                  # a course day completed -> advance
                store.advance_course(ac[0], ac[1])
                self._active_course = None

    # --- bedtime story -----------------------------------------------------
    def _start_story(self):
        if not (self._story_scene and self.narrator.available
                and self.controller.running):
            return
        units = stories.story_units(self._story_scene, guidance=True)
        self.narrator.start(units, self._story_level, self._story_timing,
                            self._on_story_unit)

    # --- text-matched soundscape + emotion ---------------------------------
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

    # --- loop --------------------------------------------------------------
    def _tick(self):
        self._anim_t += 1.0 / FPS
        if self.controller.running:
            self.director.update(self.controller.elapsed())   # morph / program / sleep
        state = self.controller.current_state()
        running = self.controller.running
        if running and self.controller.session_finished():
            self._log_practice()
            self.controller.pause()
            self.engine.set_master_volume(0.0)
            self.narrator.stop()
            running = False
            self.panel.reflect_running(False)
            QTimer.singleShot(400, self._after_mood)   # offer mood, after the tick
        if running and self._sleep_timer_min > 0 and not self._sleep_timer_done:
            from . import sleeptimer                    # gentle fade-out, then pause
            local = self.controller.elapsed() - self._sleep_timer_t0
            gain, done = sleeptimer.fade_gain(self._sleep_timer_min, local)
            if done:
                self._log_practice()
                self.controller.pause()
                self.engine.set_master_volume(0.0)
                self.narrator.stop()
                self._sleep_timer_done = True
                running = False
                self.panel.reflect_running(False)
                QTimer.singleShot(400, self._after_mood)
            elif gain < 1.0:                            # ease the volume down
                base = 0.0 if self._is_muted else self.user_volume
                self.engine.set_master_volume(base * gain)
        if running and state.phase != self._last_phase:
            if state.phase in ("inhale", "exhale"):
                self.engine.trigger_chime(
                    "in" if state.phase == "inhale" else "out")
            if state.phase == "inhale":
                self._inhale_open = sample_inhale_open()    # vary the new breath
            self.speech.cue(state.phase)
            self._last_phase = state.phase
        if running and self._bell_interval > 0 and \
                self.controller.elapsed() >= self._next_bell:
            self.engine.trigger_chime("in")                 # mindfulness bell
            self._next_bell += self._bell_interval * 60.0
        elif not running:
            self._last_phase = state.phase

        rem = self.controller.session_remaining()
        total = self.controller.session_seconds
        prog = None if (total <= 0 or rem == float("inf")) else 1.0 - rem / total
        if running:
            self._apply_speech_pace()
        amp = self.narrator.amp if running else 0.0
        if running:
            self._apply_soundscape()           # ambience follows the words
        self._ease_mood(running)               # expression eases toward the mood
        if self._view == "scene":
            self.viz.update_state(self._scene_ctx(state, running, prog))
        else:
            breath, mo = self._face_inputs(state, running, amp)
            self.face.set_state(breath, self._anim_t, prog or 0.0,
                                mouth=mo["jaw"], nose=mo["nose"],
                                pucker=mo["pucker"], stretch=mo["stretch"],
                                phase=state.phase, smile=self._smile,
                                brow=self._brow, eye_bias=self._eyeb)
        # Sleep wind-down dims + warms toward sleep; the Sunrise wake-up does the
        # inverse, brightening from a warm pre-dawn dimness to a clear, full view.
        wake = getattr(self.director, "wake", False) and running and total > 0
        sleep = self.current_mode == "Sleep" and running and total > 0 and not wake
        if wake:
            wf = prog or 0.0                              # 0 = pre-dawn, 1 = full day
            warm = 0.4 * (1.0 - wf)                       # dawn warmth fades to clear
            self.face.set_warm(warm)
            self.viz.set_warm(warm)
            self.setWindowOpacity(0.55 + 0.45 * wf)       # dim -> bright
        else:
            cw = self._clock_warm()                       # gentle time-of-day warmth
            sw = 0.5 * (prog or 0.0) if sleep else 0.0
            warm = max(sw, cw)                            # Sleep dominates when active
            self.face.set_warm(warm)
            self.viz.set_warm(warm)
            if sleep:
                self.setWindowOpacity(1.0 - 0.3 * (prog or 0.0))
            else:
                self.setWindowOpacity(1.0 - 0.2 * cw)    # a touch dimmer at night
        self._tick_hourglass(running, total, prog)
        self.panel.tick()
        self._update_status(state, running)

    def _face_inputs(self, state, running, amp):
        """Resolve the face's visible breath + mouth, talking taking precedence.

        While the storyteller voices a sentence the mouth lip-syncs and the
        visible breath eases *down* (an exhale); in the gap before the next
        sentence the mouth closes and the breath eases *up* (a breath in). With
        no recent speech, the ordinary phase/voice breathing mouth applies."""
        now = self._anim_t
        if amp > _AMP_TH:
            self._last_speak_t = now
        silence = now - self._last_speak_t
        if running and silence < _TALK_WINDOW:               # storyteller active
            if silence < _SPEAK_HOLD:                        # speaking → exhaling
                mo = {"jaw": min(0.5, amp * 1.3), "pucker": 0.0,
                      "stretch": 0.0, "nose": 0.0}
                target = 0.28
                self._was_speaking = True
            else:                                            # between sentences
                if self._was_speaking:                       # new breath → vary it
                    self._inhale_open = sample_inhale_open()
                    self._was_speaking = False
                mo = {"jaw": 0.14 * self._inhale_open, "pucker": 0.0,
                      "stretch": 0.0, "nose": 0.12}          # slight, varied parting
                target = 0.92                                # breathe in
            self._face_breath += (target - self._face_breath) * _BREATH_EASE
            return self._face_breath, mo
        # Not talking: ordinary breath-driven mouth (nose-in / shaped mouth-out).
        af = state.airflow if running else 0.0
        r = breath_routing(state.phase, self.engine.voice_a, self.engine.voice_out)
        self._face_breath = state.volume if running else 0.5
        jaw = af * r["jaw"]
        if state.phase == "inhale":
            jaw *= self._inhale_open                          # vary the in-breath
        return self._face_breath, {"jaw": jaw, "pucker": af * r["pucker"],
                                   "stretch": af * r["stretch"], "nose": af * r["nose"]}

    def _update_status(self, state, running):
        if not running:
            sug = getattr(self, "_launch_suggestion", None)
            if (self.controller.elapsed() == 0 and sug
                    and not getattr(self, "_started_once", False)):
                self.status.showMessage(sug)         # gentle launch hint, until first start
                return
            self.status.showMessage("Press Start" if self.controller.elapsed()
                                    == 0 else "Paused — press Start")
            return
        m, s = divmod(int(self.controller.elapsed()), 60)
        label = state.label
        line = (self._story_line[:60] if self._story_line else "")
        self.status.showMessage(f"{label}    {m:02d}:{s:02d}    {line}")

    def closeEvent(self, ev):
        try:
            store.save_settings({"mode": self.current_mode,
                                 "volume": self.user_volume,
                                 "speech_speed": self._speech_speed,
                                 "view": self._view, "face_bg": self._face_bg,
                                 "hourglass": self._hg_show,
                                 "face_cat": self.face.uses_cat(),
                                 "clock_light": self._clock_light,
                                 "mood_checkins": self._mood_on,
                                 "onboarded": getattr(self, "_onboarded", False),
                                 "spatial": getattr(self, "_spatial", True),
                                 "font_scale": getattr(self, "_font_scale", 1.0)})
        except Exception:
            pass
        try:
            self.set_tuner(False)
            self.face.stop()
            self.narrator.stop()
            self.engine.stop()
            self.speech.shutdown()
        except Exception:
            pass
        super().closeEvent(ev)


def launch():
    app = QApplication.instance() or QApplication([])
    win = MainWindow()
    win.show()
    app.exec()
