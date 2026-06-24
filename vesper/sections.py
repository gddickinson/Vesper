"""Control-panel card builders (a mixin inherited by ControlPanel).

Each ``_card_<key>`` returns a themed card widget for one concept and registers
its live widgets in ``self._w`` so ``ControlPanel.sync``/``tick`` can refresh
them. Builders are pure view code: they read current state from ``self.win`` and
call back into the MainWindow actions. Workspaces (``workspaces.py``) decide which
cards each mode shows.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from breathsim import choir, narration, personas, phrases, session, voices
from breathsim.patterns import PRESETS

from .widgets import LabeledSlider, card, combo, combo_row, muted

CUE_STYLES = ["Off", "Minimal", "Standard", "Guided"]


def _voice_choices():
    groups = (voices.GROUP_BREATH, voices.GROUP_CAT, voices.GROUP_VOCAL,
              voices.GROUP_TECHNIQUE, voices.GROUP_SING, voices.GROUP_EXERCISE,
              voices.GROUP_SYNTH, voices.GROUP_CUSTOM)
    out = []
    for g in groups:
        out += voices.names(g)
    return out


class _SectionsMixin:
    # --- breath -----------------------------------------------------------
    def _card_pattern(self):
        frame, body = card("Breath pattern")
        box = combo([p.name for p in PRESETS],
                    self.win.controller.pattern.name,
                    self._on_pattern)
        self._w["pattern"] = box
        body.addWidget(box)
        from .pattern_bar import PatternBar           # a small phase diagram
        bar = PatternBar()
        bar.set_pattern(self.win.controller.pattern)
        self._w["pattern_bar"] = bar
        body.addWidget(bar)
        return frame

    def _on_pattern(self, name):
        self.win.set_pattern(name)
        bar = self._w.get("pattern_bar")
        if bar is not None:
            bar.set_pattern(self.win.controller.pattern)

    def _card_pace(self, _b=None):
        frame, body = card("Pace — breaths per minute")
        s = LabeledSlider("Rate", 3.0, 12.0, 6.0, decimals=1, suffix=" bpm",
                          on_change=self._on_pace)
        self._w["pace"] = s
        body.addWidget(s)
        chk = QCheckBox("Longer exhale (calming)")
        chk.toggled.connect(lambda _v: self._on_pace(s.value()))
        self._w["pace_long"] = chk
        body.addWidget(chk)
        hint = muted("~5.5–6 bpm is the resonance / coherence sweet spot.")
        hint.setWordWrap(True)
        body.addWidget(hint)
        return frame

    def _on_pace(self, _v=None):
        s, chk = self._w.get("pace"), self._w.get("pace_long")
        if s:
            self.win.set_pace(s.value(), bool(chk and chk.isChecked()))

    # --- voice ------------------------------------------------------------
    def _card_voice(self):
        frame, body = card("Voice")
        choices = _voice_choices()
        va = combo(choices, self.win.engine.voice_a, self.win.set_voice_a)
        self._w["voice_a"] = va
        body.addWidget(muted("Breath / inhale voice"))
        body.addWidget(va)
        outs = ["Same as inhale"] + _voice_choices()
        vo = combo(outs, self.win.engine.voice_out or "Same as inhale",
                   self.win.set_voice_out)
        self._w["voice_out"] = vo
        body.addWidget(muted("Exhale voice"))
        body.addWidget(vo)
        bp = combo(personas.names(), self.win.engine.persona.name,
                   self.win.set_persona)
        self._w["persona"] = bp
        body.addWidget(muted("Voice body"))
        body.addWidget(bp)
        return frame

    def _card_naturalness(self):
        frame, body = card("Naturalness")
        nat = self.win.controller.naturalness
        chk = QCheckBox("Natural breath-to-breath variation")
        chk.setChecked(getattr(nat, "amount", 0.0) > 1e-3)
        chk.toggled.connect(lambda _v: self._on_nat())
        self._w["nat_on"] = chk
        body.addWidget(chk)
        s = LabeledSlider("Amount", 0.0, 1.0, getattr(nat, "amount", 0.0) or 0.5,
                          decimals=2, on_change=lambda _v: self._on_nat())
        self._w["nat_amt"] = s
        body.addWidget(s)
        return frame

    def _on_nat(self):
        chk, s = self._w.get("nat_on"), self._w.get("nat_amt")
        if chk and s:
            self.win.set_naturalness(s.value() if chk.isChecked() else 0.0,
                                     chk.isChecked())

    # --- cues -------------------------------------------------------------
    def _card_cues(self):
        frame, body = card("Spoken cues")
        cs = combo(CUE_STYLES, self.win.speech.style, self.win.set_cue_style)
        self._w["cue_style"] = cs
        body.addWidget(muted("Style"))
        body.addWidget(cs)
        accents = self.win.speech.accent_voices()
        if accents:
            labels = [a[0] for a in accents]
            self._cue_voice_ids = {a[0]: a[1] for a in accents}
            cv = combo(labels, None, self._on_cue_voice)
            self._w["cue_voice"] = cv
            body.addWidget(muted("Voice"))
            body.addWidget(cv)
        return frame

    def _on_cue_voice(self, label):
        vid = getattr(self, "_cue_voice_ids", {}).get(label)
        if vid:
            self.win.speech.set_voice(vid)

    # --- chant / sing -----------------------------------------------------
    def _card_choir(self):
        frame, body = card("Choir")
        h = combo(choir.names(), "Off", self._on_choir)
        self._w["choir_h"] = h
        body.addWidget(muted("Harmony"))
        body.addWidget(h)
        s = LabeledSlider("Level", 0.0, 1.0, 0.6, decimals=2,
                          on_change=lambda _v: self._on_choir())
        self._w["choir_lvl"] = s
        body.addWidget(s)
        return frame

    def _on_choir(self, _v=None):
        h, s = self._w.get("choir_h"), self._w.get("choir_lvl")
        if h and s:
            self.win.set_choir(h.currentText(), s.value())

    def _card_phrase(self):
        frame, body = card("Chant / mantra")
        cat = combo(phrases.CATEGORIES, phrases.CATEGORIES[0], self._on_phrase_cat)
        self._w["phrase_cat"] = cat
        body.addWidget(muted("Tradition"))
        body.addWidget(cat)
        ph = combo(["None"] + phrases.names(phrases.CATEGORIES[0]), "None",
                   self.win.set_phrase)
        self._w["phrase"] = ph
        body.addWidget(muted("Phrase"))
        body.addWidget(ph)
        return frame

    def _on_phrase_cat(self, cat):
        ph = self._w.get("phrase")
        if ph:
            ph.blockSignals(True)
            ph.clear()
            ph.addItems(["None"] + phrases.names(cat))
            ph.blockSignals(False)

    # --- relax / sleep ----------------------------------------------------
    def _card_soundscape(self):
        frame, body = card("Soundscape")
        ambs = (["None"] + voices.names(voices.GROUP_NATURE)
                + voices.names(voices.GROUP_MUSIC)
                + voices.names(voices.GROUP_BELLS)
                + voices.names(voices.GROUP_WIND)
                + voices.names(voices.GROUP_FX))
        a = combo(ambs, self.win.engine.slot_voice.get("ambience") or "None",
                  self.win.set_ambience)
        self._w["ambience"] = a
        body.addWidget(muted("Ambience"))
        body.addWidget(a)
        al = LabeledSlider("Ambience level", 0.0, 1.0,
                           self.win.engine.slot_levels.get("ambience", 0.8),
                           decimals=2,
                           on_change=lambda v: self.win.set_slot_level("ambience", v))
        self._w["amb_lvl"] = al
        body.addWidget(al)
        effs = (["None"] + voices.names(voices.GROUP_EFFECTS)
                + voices.names(voices.GROUP_DRUMS))
        e = combo(effs, self.win.engine.slot_voice.get("effects") or "None",
                  self.win.set_effect)
        self._w["effect"] = e
        body.addWidget(muted("Heartbeat / effects"))
        body.addWidget(e)
        el = LabeledSlider("Effect level", 0.0, 1.0,
                           self.win.engine.slot_levels.get("effects", 0.85),
                           decimals=2,
                           on_change=lambda v: self.win.set_slot_level("effects", v))
        self._w["eff_lvl"] = el
        body.addWidget(el)
        return frame

    def _card_story(self):
        from breathsim import stories
        frame, body = card("Bedtime story")
        items = ["Off", "Random"] + stories.extra_names() + stories.scene_names()
        sc = combo(items, self.win._story_scene or "Off", self.win.set_story)
        for cat in stories.lecture_categories():    # lectures grouped by branch
            sc.insertSeparator(sc.count())
            sc.addItem(f"— {cat} —")       # disabled branch header
            sc.model().item(sc.count() - 1).setEnabled(False)
            sc.addItems(stories.lecture_names(cat))
        if self.win._story_scene in stories.lecture_names():
            sc.setCurrentText(self.win._story_scene)
        self._w["story"] = sc
        body.addWidget(muted("Scene or lecture"))
        body.addWidget(sc)
        ids = narration.available_voices(self.win.speech)
        self._story_voice_id = {narration.voice_label(v): v for v in ids}
        labels = list(self._story_voice_id) or ["(no voice)"]
        cur = narration.voice_label(self.win.narrator.voice
                                    or narration.best_voice(self.win.speech))
        if cur not in self._story_voice_id:
            cur = labels[0]
        vc = combo(labels, cur, lambda lbl: self.win.set_story_voice(
            self._story_voice_id.get(lbl, lbl)))
        self._w["story_voice"] = vc
        body.addWidget(muted("Narration voice  (★ = most realistic)"))
        body.addWidget(vc)
        s = LabeledSlider("Speech speed", 0.6, 1.2, self.win._speech_speed,
                          decimals=2, suffix="x",
                          on_change=self.win.set_speech_speed)
        self._w["speech_speed"] = s
        body.addWidget(s)
        lbl = narration.engine_label(self.win.speech) or "no narration"
        body.addWidget(muted(f"Engine: {lbl}"))
        return frame

    def _card_winddown(self):
        frame, body = card("Sleep wind-down")
        chk = QCheckBox("Slow the breath and fade out over the session")
        chk.toggled.connect(lambda _v: self._on_winddown())
        self._w["wind_on"] = chk
        body.addWidget(chk)
        s = LabeledSlider("Duration", 5.0, 60.0, self.win._story_minutes,
                          decimals=0, suffix=" min",
                          on_change=lambda _v: self._on_winddown())
        self._w["wind_min"] = s
        body.addWidget(s)
        from . import sleeptimer
        body.addWidget(muted("Sleep timer: fade out and pause after a set time."))
        tmr = combo([lbl for lbl, _m in sleeptimer.OPTIONS],
                    sleeptimer.label_for(self.win._sleep_timer_min),
                    self._on_sleep_timer)
        self._w["sleep_timer"] = tmr
        body.addWidget(tmr)
        return frame

    def _on_sleep_timer(self, label):
        from . import sleeptimer
        for lbl, m in sleeptimer.OPTIONS:
            if lbl == label:
                self.win.set_sleep_timer(m)
                return

    def _on_winddown(self):
        chk, s = self._w.get("wind_on"), self._w.get("wind_min")
        if chk and s:
            self.win.set_winddown(chk.isChecked(), s.value())

    # --- sing / chant: pitch trainer --------------------------------------
    def _card_pitch(self):
        from breathsim import music, vocaltrainer
        frame, body = card("Pitch trainer")
        ex = combo(["Hold note"] + list(vocaltrainer.SCALES.keys()),
                   "Hold note", lambda _v: self._on_pitch())
        self._w["pitch_ex"] = ex
        body.addWidget(muted("Exercise"))
        body.addWidget(ex)
        nb = combo(music.note_range("C3", "C5"), "C4", lambda _v: self._on_pitch())
        self._w["pitch_note"] = nb
        body.addWidget(muted("Starting note"))
        body.addWidget(nb)
        g = QCheckBox("Show pitch guide (uses mic)")
        g.toggled.connect(lambda _v: self._on_pitch())
        self._w["pitch_on"] = g
        body.addWidget(g)
        ref = QCheckBox("Play reference tone")
        ref.toggled.connect(lambda _v: self._on_ref())
        self._w["pitch_ref"] = ref
        body.addWidget(ref)
        body.addWidget(muted("Sing the bright target line green."))
        return frame

    def _pitch_spec(self):
        from breathsim import vocaltrainer
        ex, nb = self._w.get("pitch_ex"), self._w.get("pitch_note")
        name = ex.currentText() if ex else "Hold note"
        base = nb.currentText() if nb else "C4"
        return (vocaltrainer.hold_spec(base) if name == "Hold note"
                else vocaltrainer.scale_spec(name, base))

    def _on_pitch(self):
        g = self._w.get("pitch_on")
        if g and g.isChecked():
            self.win.show_pitch_guide(self._pitch_spec())
        else:
            self.win.hide_pitch_guide()
        self._on_ref()

    def _on_ref(self):
        ref, nb = self._w.get("pitch_ref"), self._w.get("pitch_note")
        note = nb.currentText() if nb else "C4"
        self.win.set_reference(bool(ref and ref.isChecked()), note)

    # --- meditate: mindfulness bell ---------------------------------------
    def _card_bell(self):
        frame, body = card("Mindfulness bell")
        b = combo(["Off", "2 min", "5 min", "10 min", "15 min"], "Off",
                  self._on_bell)
        self._w["bell"] = b
        body.addWidget(muted("Gentle interval chime"))
        body.addWidget(b)
        return frame

    def _on_bell(self, txt):
        mins = 0.0 if txt == "Off" else float(txt.split()[0])
        self.win.set_bell_interval(mins)

    # --- meditate: focused-attention vs open-monitoring guidance -----------
    def _card_guidance(self):
        frame, body = card("Guidance")
        body.addWidget(muted("Style"))
        g = combo(["Off", "Focused attention", "Open monitoring"], "Off",
                  self.win.set_meditation_guidance)
        self._w["med_guidance"] = g
        body.addWidget(g)
        body.addWidget(muted("Gentle cues appear softly under the orb."))
        return frame

    # --- breathwork: breath-hold retention --------------------------------
    def _card_retention(self):
        frame, body = card("Breath-hold timer")
        btn = QPushButton("Start hold")
        btn.clicked.connect(self._on_hold)
        self._w["hold_btn"] = btn
        body.addWidget(btn)
        lbl = muted("Hold your breath; tap to log the time.")
        lbl.setWordWrap(True)
        self._w["hold_lbl"] = lbl
        body.addWidget(lbl)
        return frame

    def _on_hold(self):
        self.win.toggle_hold()
        self._refresh_hold()

    def _refresh_hold(self):
        btn, lbl = self._w.get("hold_btn"), self._w.get("hold_lbl")
        if not btn:
            return
        state, secs = self.win.hold_status()
        if state == "holding":
            btn.setText("Stop & log")
            lbl.setText(f"Holding…  {secs:0.0f}s")
        else:
            btn.setText("Start hold")
            lbl.setText(f"Last hold: {secs:0.0f}s" if secs > 0
                        else "Hold your breath; tap to log the time.")

    # --- breathwork: guided programs --------------------------------------
    def _card_programs(self):
        frame, body = card("Guided session")
        from breathsim import programs
        opts = ["Manual"] + session.SessionDirector.MODES[1:] + programs.names()
        pr = combo(opts, "Manual", None)
        self._w["program"] = pr
        body.addWidget(muted("Mode / program"))
        body.addWidget(pr)
        row = QHBoxLayout()
        start = QPushButton("Start session")
        start.clicked.connect(lambda: self.win.start_session_mode(pr.currentText()))
        row.addWidget(start)
        body.addLayout(row)
        stage = muted("")
        stage.setWordWrap(True)
        self._w["prog_stage"] = stage
        body.addWidget(stage)
        return frame
