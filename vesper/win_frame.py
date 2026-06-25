"""The ~40fps frame loop, Meditate guidance cues and scene/face/status
presentation for MainWindow (a mixin), split from window.py. All state stays on
self; these render each frame and steer the visuals."""
from __future__ import annotations

import math

from PySide6.QtCore import QTimer

from . import introfade, sleepdim
from .face_motion import breath_routing, sample_inhale_open
from .win_consts import (FPS, _AMP_TH, _BREATH_EASE, _SPEAK_HOLD, _TALK_WINDOW)


class _FrameMixin:
    def set_meditation_guidance(self, style):
        self._med_style = style if style in self._MED_CUES else "Off"

    def set_breath_coach(self, on):
        """Toggle the on-screen breathing count cue (opt-in, persisted)."""
        self._coach = bool(on)

    def _phase_len(self, phase):
        p = self.controller.pattern
        return {"inhale": p.inhale, "hold_full": p.hold_full,
                "exhale": p.exhale, "hold_empty": p.hold_empty}.get(phase, 0.0)

    def _med_phrase(self, elapsed):
        cues = self._MED_CUES.get(self._med_style)
        if not cues:
            return ""
        return cues[int(elapsed / 22.0) % len(cues)]   # a new cue ~every 22 s

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
        intro_line = self._intro_text()            # settle-in lead-in takes precedence
        if intro_line:
            sub = intro_line
        if running and self._coach and not sub:    # gentle in/hold/out counting
            from breathsim import coach
            plen = self._phase_len(state.phase)
            sub = coach.cue(state.phase, getattr(state, "progress", 0.0) * plen, plen)
        hint = ""                                  # Meditate: gentle rotating guidance
        if running and self.current_mode == "Meditate" and self._med_style != "Off":
            hint = self._med_phrase(self.controller.elapsed())
        if running and not hint and self.director.settle_info() is not None:
            hint = "easing to your pace…"           # ease-to-resonance in progress
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
            if getattr(self, "_closing_msg", None):  # a gentle "well done" after a sit
                self.status.showMessage(self._closing_msg)
                return
            sug = getattr(self, "_launch_suggestion", None)
            if (self.controller.elapsed() == 0 and sug
                    and not getattr(self, "_started_once", False)):
                self.status.showMessage(sug)         # gentle launch hint, until first start
                return
            self.status.showMessage("Press Start" if self.controller.elapsed()
                                    == 0 else "Paused — press Start")
            return
        intro_line = self._intro_text()              # gentle settle-in over the first breath
        if intro_line:
            self.status.showMessage(intro_line)
            return
        m, s = divmod(int(self.controller.elapsed()), 60)
        label = state.label
        line = (self._story_line[:60] if self._story_line else "")
        self.status.showMessage(f"{label}    {m:02d}:{s:02d}    {line}")

    def _tick(self):
        """Per-frame slot (~40fps). Guarded so a single bad frame can't spam
        tracebacks every tick or stall the animation; the first error is logged
        once and the loop keeps running."""
        try:
            self._tick_impl()
        except Exception:
            if not getattr(self, "_tick_errored", False):
                self._tick_errored = True
                import traceback
                print("[vesper] tick error (suppressed after first):")
                traceback.print_exc()

    def _tick_impl(self):
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
            self._apply_story_bg()             # backdrop follows the words too
            if self._amb_rotate and not self._story_scene:
                self._apply_ambience_rotate()  # slowly cycle beds (when no storyteller)
        if running and getattr(self, "_cast", None):
            self.apply_cast_tick()             # dramatized: swap character + mood
        self._ease_mood(running)               # expression eases toward the mood
        self._react_face(state, running)       # reactive style/glow (when toggled on)
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
            op = 0.55 + 0.45 * wf                         # dim -> bright
        else:
            cw = self._clock_warm()                       # gentle time-of-day warmth
            sw = 0.5 * (prog or 0.0) if sleep else 0.0
            warm = max(sw, cw)                            # Sleep dominates when active
            self.face.set_warm(warm)
            self.viz.set_warm(warm)
            op = (sleepdim.sleep_dim(prog or 0.0) if sleep   # deepen toward 'lights out'
                  else (1.0 - 0.2 * cw))
        op *= introfade.intro_opacity(self._anim_t)       # gentle one-time launch fade-in
        if self._blackout:                                # near-dark sleep screen (never 0)
            op = min(op, 0.05)
        self._win_op = op                                 # recorded for tests
        self.setWindowOpacity(op)
        self._apply_quiet_cap()                # gentle late-night output ceiling
        self._tick_hourglass(running, total, prog)
        self.panel.tick()
        self._update_status(state, running)
