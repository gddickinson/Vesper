"""MainWindow — the PySide6 app. Reuses the breathsim core; the face is central.

Phase 1 of the rebuild: a working session runner with the faceView face
breathing + lip-syncing the bedtime story, a mode bar, transport, volume, a
render-mode picker and Sleep story controls. The audio/logic (engine, controller,
voices, patterns, modes, narration, stories, Kokoro) is the unchanged core.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QApplication, QMainWindow, QSplitter,
                               QStackedWidget)

from breathsim import choir, modes, narration, personas, sound_cues, stories
from breathsim import story_db
from breathsim import controller as ctrl_mod
from breathsim import engine as eng_mod
from breathsim import session as sess_mod
from breathsim import speech as sp_mod
from breathsim import store
from breathsim.patterns import DEFAULT_PATTERN, preset_by_name

from . import introfade, menus, shortcuts, sleepdim, theme
from .app_actions import _ActionsMixin
from .controls import ControlPanel
from .face import FaceWidget
from .face_motion import breath_routing, emotion_for_text, sample_inhale_open
from .pitch import _PitchMixin
from .viz import VizWidget
from .win_hourglass import _HourglassMixin
from .win_consts import FPS
from .cast import _CastMixin
from .win_dnd import _DnDMixin
from .win_frame import _FrameMixin
from .win_settings import _SettingsMixin
from .win_story import _StoryMixin


# Each window gets a fitting backdrop behind the face (kept to its theme).
_MODE_BG = {"Meditate": "Gradient", "Breathwork": "Aurora", "Chant": "Nebula",
            "Sing": "Aurora", "Relax": "Underwater", "Sleep": "Stars"}


class MainWindow(_ActionsMixin, _PitchMixin, _HourglassMixin, _CastMixin,
                 _StoryMixin, _FrameMixin, _DnDMixin, _SettingsMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vesper")
        self.resize(1200, 780)
        self.setStyleSheet(theme.STYLESHEET)
        self.setAcceptDrops(True)                   # drop a .txt/.epub to add a novel

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
        self._face_style = "Default"       # cyberpunk face render style (see face_styles)
        self._face_reactive = False        # reactive face: style follows mode/chant/breath
        self._character = "Cat"            # chosen 2D character (cat/penguin/dog)
        self._costume = "None"             # costume overlay for the 2D character
        self._char_voices = True           # give each character its own voice + rate
        self._char_rate = 1.0              # current character's speaking-rate multiplier
        self._dramatize = False            # cast reading (each speaker its own voice)
        self._cast_expressive = False      # wider variation (sound follow) for the Reader
        self._cast = None                  # the live cast script (or None)
        self._gratitude_on = False         # opt-in bedtime 'one good thing' (set in restore)
        self._listener_name = ""           # optional spoken-greeting name ('' = off)
        self._greeted_session = False      # greeted by name yet this session?
        self._calm_visuals = False         # 'reduce motion' (set in restore)
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
        self._applying_mode = False        # guard: don't record prefs while applying a mode
        self._win_op = 1.0                 # last applied window opacity (intro fade + dim)
        self._closing_msg = None           # gentle "well done" line after a finished sit
        self._amb_rotate = False           # ambience auto-rotate (opt-in; off by default)
        self._quiet_hours = True           # gently cap output volume in the small hours
        self._cur_cap = 1.0                # last applied output cap (see _tick)
        self._blackout = False             # near-dark sleep screen (audio keeps playing)
        self._coach = False                # breathing-coach on-screen count cue (opt-in)
        self._intro_on = True              # gentle "settle in" lead-in on a fresh start
        self._intro_sched = []             # active lead-in [(start, end, text), ...]
        self._last_logged_section = -1     # per-lecture resume: last recorded section
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

        self.face = FaceWidget()
        self.viz = VizWidget()
        self.face._hg_click_cb = self._flip_hourglass    # tap the timer to flip it
        self.viz._hg_click_cb = self._flip_hourglass
        self.stack = QStackedWidget()
        self.stack.addWidget(self.face)            # index 0
        self.stack.addWidget(self.viz)             # index 1
        self.panel = ControlPanel(self)
        split = QSplitter(Qt.Orientation.Horizontal)   # user-resizable panel width
        split.addWidget(self.stack)
        split.addWidget(self.panel)
        split.setStretchFactor(0, 1)               # the visualization takes the slack
        split.setStretchFactor(1, 0)
        split.setCollapsible(0, False)
        split.setCollapsible(1, False)
        split.setChildrenCollapsible(False)
        split.setSizes([800, 400])
        self.setCentralWidget(split)
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

        from . import clocktheme, resumehint, suggest  # a gentle, non-modal launch hint
        self._started_once = False
        try:
            sug = suggest.suggest(
                clocktheme.now_hour(), store.history(), store.course_state())
            self._launch_suggestion = sug.text
            # Prefer a "pick up where you left off" reminder, unless an in-progress
            # course (the kindest resume) already takes the line.
            rh = resumehint.resume_hint(store.load_settings())
            if rh and sug.kind != "course":
                self._launch_suggestion = rh
            from breathsim import books               # an in-progress book wins (kindest)
            book_rh = resumehint.book_continue_hint(books.in_progress())
            if book_rh and sug.kind != "course":
                self._launch_suggestion = book_rh
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

    def set_face_style(self, name):
        """Pick the cyberpunk face render style (eye pattern / skin / mode).
        Persisted, applies live, and also callable by the storyteller / breath /
        chant to animate the face's mood. The Default keeps the classic look."""
        self._face_style = name
        self.face.set_style(name)

    def set_character(self, name, persist=True):
        """Pick the 2D cartoon character (Cat / Penguin / Dog / ...). Adopts the
        character's signature look, and (when Character voices is on) its narrator
        voice + speaking rate, with a brief greeting. ``persist=False`` is used when
        the storyteller temporarily matches a character to the scene -- it changes
        the displayed character without overwriting the user's saved choice."""
        self.face.set_character(name)
        from . import char_voice
        cv = char_voice.get(name)
        if persist:
            self._character = name
        if getattr(self, "_char_voices", True):
            self._apply_character_voice(name)
        if persist and cv.greeting:
            self.status.showMessage(f"{name}: “{cv.greeting}”", 5000)

    def _apply_character_voice(self, name):
        """Set the narrator to the character's preferred voice + rate. Prefers the
        character's high-quality **XTTS** voice when that engine is installed, and
        falls back to its Kokoro / say hint-match otherwise; always graceful."""
        from breathsim import narration, xtts_tts
        from . import char_voice
        cv = char_voice.get(name)
        self._char_rate = cv.rate
        try:
            v = None
            if cv.xtts and xtts_tts.ready():
                v = xtts_tts.PREFIX + cv.xtts
            if not v:
                v = char_voice.pick_voice(
                    cv.hints, narration.available_voices(self.speech))
            if v:
                self.narrator.set_voice(v)
                if self._story_scene and self.controller.running:
                    self._start_story()
        except Exception:
            pass

    def set_character_voices(self, on):
        """Toggle whether each character speaks in its own voice (persisted)."""
        self._char_voices = bool(on)
        if self._char_voices:
            self._apply_character_voice(self._character)
        else:
            self._char_rate = 1.0

    def set_costume(self, name):
        """Pick a costume overlay for the 2D character (persisted)."""
        self._costume = name
        self.face.set_costume(name)

    def set_face_cat(self, on):
        """Use the cartoon cat instead of the 3D head (View menu / persisted)."""
        self.face.set_use_cat(on)
        act = getattr(self, "_act_cat", None)
        if act is not None and act.isChecked() != self.face.uses_cat():
            act.setChecked(self.face.uses_cat())

    def set_clock_light(self, on):
        self._clock_light = bool(on)

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
        self._applying_mode = True
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
        # restore the voice / ambience the user last chose in this mode (if any)
        from breathsim import store, voices
        pref = store.get_mode_pref(name)
        pv = pref.get("voice")
        if pv and voices.get_voice(pv):
            self.engine.set_voice_a(pv)
        pa = pref.get("ambience")
        if pa and not self._story_scene and voices.get_voice(pa):
            self._set_base_ambience(pa)               # not during the Sleep storyteller
        self.current_mode = name
        self._applying_mode = False
        self.panel.reflect_mode(name)
        self.status.showMessage(m.description, 4000)

    def set_pattern(self, name):
        p = preset_by_name(name)
        if p:
            self.controller.change_pattern(p)
            if getattr(self, "_settle", False) and self.controller.running:
                self.director.start_settle(p)      # re-aim the easing at the new target

    def set_volume(self, vol):
        self.user_volume = float(vol)
        if self.controller.running and not self._is_muted:
            self.engine.set_master_volume(self.user_volume)

    # --- transport ---------------------------------------------------------
    def toggle_transport(self):
        if self.controller.running:
            self._log_practice()
            self.controller.pause()
            self.engine.set_master_volume(0.0)
            self.narrator.stop()
            self._intro_sched = []                   # retire any settle-in lead-in
            self.panel.reflect_running(False)
            self._after_mood()                       # offer it after we've paused
            return
        fresh = self.controller.elapsed() < 1.0
        self._started_once = True                     # retire the launch hint
        if fresh:
            self._sleep_timer_t0 = 0.0                # restart the sleep-timer countdown
            self._sleep_timer_done = False
            self._closing_msg = None                  # retire the previous "well done" line
            self._mood_after_done = False
            self._greeted_session = False            # allow one greeting-by-name this session
            from . import gratitude, mood
            mood.maybe_check_in(self, "before")      # only on a fresh start
            gratitude.maybe_offer_bedtime(self)      # opt-in 'one good thing' (Sleep)
        self.controller.start()
        self.engine.set_master_volume(0.0 if self._is_muted else self.user_volume)
        self._start_story()
        self._arm_intro(fresh)
        if fresh and getattr(self, "_settle", False):  # ease the pace down from the start
            self.director.start_settle(self.controller.pattern)
        self._note_if_silent()                         # honest visual-only message
        self.panel.reflect_running(self.controller.running)

    def reset(self):
        self._log_practice()
        self._after_mood()
        self.narrator.stop()
        self.controller.reset()
        self.engine.set_master_volume(0.0)
        self._intro_sched = []                 # retire any settle-in lead-in
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

    def toggle_blackout(self, on=None):
        """Near-dark sleep screen: hide the chrome and dim the window right down
        while the sound keeps playing. Reversible by B, Esc, a click, or toggle."""
        self._blackout = (not self._blackout) if on is None else bool(on)
        if self._blackout:
            self.status.showMessage("Blackout - press B or Esc, or tap, to wake", 2500)
        hide = self._blackout or getattr(self, "_zen", False)
        self.panel.setVisible(not hide)
        self.menuBar().setVisible(not hide)
        self.statusBar().setVisible(not hide)

    def mousePressEvent(self, ev):
        if self._blackout:                            # tap to wake from blackout
            self.toggle_blackout(False)
            return
        if getattr(self, "_intro_sched", None):       # tap to skip the settle-in lead-in
            self._intro_sched = []
        super().mousePressEvent(ev)

    def set_quiet_hours(self, on):
        """Toggle the late-night output-volume cap (persisted); applies at once."""
        self._quiet_hours = bool(on)
        self._cur_cap = -1.0                          # force a recompute
        self._apply_quiet_cap()

    def _apply_quiet_cap(self):
        """Set the engine's output ceiling from the clock (1.0 when off/by day)."""
        from . import clocktheme
        cap = clocktheme.quiet_cap(clocktheme.now_hour()) if self._quiet_hours else 1.0
        if abs(cap - self._cur_cap) > 1e-3:
            self._cur_cap = cap
            self.engine.set_volume_cap(cap)

    def closeEvent(self, ev):
        try:
            self._persist_settings()
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
