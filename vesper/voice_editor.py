"""Voice Editor (Qt): design custom voices across the full synthesis range.

A scrollable form exposes every meaningful ``VoiceConfig`` parameter with a live
wave + spectrum preview. A **Breath phase** selector chooses where the voice
sounds:

* **Both** -- one voice for the whole breath (in *and* out), or
* **In-breath** / **Out-breath** -- a voice for that phase only. Saving an
  In-breath voice makes it the inhale voice; an Out-breath voice the exhale
  voice -- so a distinct in and out can be paired, or either designed alone.

**Play** auditions, **Randomize** explores, **Save** stores a Custom voice. While
the dialog is open a transient ``(preview)`` voice is registered + applied; on
close (without saving) the prior voice(s) are restored. Mirrors the Tk editor.
"""
from __future__ import annotations

import random

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLineEdit, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from breathsim import formants, store, tracks, voices
from breathsim.patterns import BreathPattern, state_at

from . import theme
from .waveform import WaveformView
from .widgets import LabeledSlider, card, combo_row, muted

_SHAPES = [""] + formants.shape_names()
_KINDS = ["noise", "vocal", "tonal", "synth"]
_SRC = ["noise", "buzz", "mix"]
_NOISE = ["white", "pink", "brown"]
_FILT = ["lowpass", "highpass", "bandpass"]
_GLIDE = ["linear", "updown", "scale_up", "arp_up"]
_ATTACK = ["smooth", "explosive", "swell"]
_LOUD = [("Breath flow", "airflow"), ("Lung fullness", "volume"),
         ("Smooth pulses", "breath_both")]
_PHASES = [("Both", "both"), ("In-breath", "in"), ("Out-breath", "out")]
_PHASE_ENV = {"in": "inhale", "out": "exhale"}
_PHASE_NOTE = {
    "both": "One voice for the whole breath - sounds on the in and out breath.",
    "in": "A voice for the IN-breath only. Save makes it your inhale voice; pair "
          "with an Out-breath voice for a different exhale.",
    "out": "A voice for the OUT-breath only. Save makes it your exhale voice; "
           "pair with an In-breath voice for a different inhale.",
}
_PAT = BreathPattern("(preview)", 1.6, 0.3, 2.4, 0.3)
_SR = 44100


def render_mix(cfg_list, sr, persona, seconds=3.5):
    """Render one or more voice-config dicts together over one breath cycle."""
    built = []
    for i, c in enumerate(cfg_list):
        d = {k: v for k, v in c.items() if k != "data"}
        d["name"], d["group"] = f"(prev{i})", voices.GROUP_CUSTOM
        try:
            built.append(tracks.build_track(voices.VoiceConfig(**d), sr, persona))
        except Exception:
            pass
    if not built:
        return np.zeros(int(sr * 0.2))
    blk, out, t = 1024, [], 0.0
    for _ in range(int(seconds * sr) // blk):
        s0 = state_at(_PAT, t % _PAT.cycle)
        s1 = state_at(_PAT, (t + blk / sr) % _PAT.cycle)
        mix = np.zeros((blk, 2))
        for tr in built:
            try:
                mix += tr.render(blk, s0, s1)
            except Exception:
                pass
        out.append(mix)
        t += blk / sr
    audio = np.concatenate(out)
    return audio.mean(axis=1) if audio.ndim == 2 else audio


def render_preview(cfg_dict, sr, persona, seconds=3.5):
    return render_mix([cfg_dict], sr, persona, seconds)


def open_editor(win):
    ed = _Editor(win)
    ed.show()
    return ed


class _Editor(QDialog):
    """The Voice Editor dialog. One concept: editing a single VoiceConfig."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.engine = win.engine
        self.sr = getattr(self.engine, "sr", _SR)
        self.persona = self.engine.persona
        self._prev_a = self.engine.voice_a
        self._prev_out = self.engine.voice_out
        self._key = "both"
        self._ready = False
        self._saved = False
        self._sliders = {}        # key -> (LabeledSlider, mul)
        self._combos = {}         # key -> QComboBox

        self.setWindowTitle("Voice Editor")
        self.setStyleSheet(win.styleSheet())
        self.resize(470, 720)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        title = muted("Voice Editor")
        title.setObjectName("title")
        outer.addWidget(title)

        self.wave = WaveformView(width=424, height=160)
        outer.addWidget(self.wave, 0, Qt.AlignmentFlag.AlignHCenter)

        outer.addWidget(muted("Breath phase"))
        prow = QHBoxLayout()
        self._phase_btns = {}
        for label, key in _PHASES:
            b = QPushButton(label)
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self._on_phase(k))
            prow.addWidget(b)
            self._phase_btns[key] = b
        outer.addLayout(prow)
        self._note = muted("")
        self._note.setWordWrap(True)
        outer.addWidget(self._note)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        holder = QWidget()
        self._body = QVBoxLayout(holder)
        self._body.setContentsMargins(0, 4, 6, 4)
        self._body.setSpacing(10)
        self.scroll.setWidget(holder)
        outer.addWidget(self.scroll, 1)

        bar = QHBoxLayout()
        for label, cmd, accent in (("Random", self._randomize, False),
                                   ("Play", self._play, False),
                                   ("Save", self._save, True),
                                   ("Close", self._close, False)):
            b = QPushButton(label)
            if accent:
                b.setObjectName("accent")
            b.clicked.connect(cmd)
            bar.addWidget(b)
        outer.addLayout(bar)

        # --- source config + form ----------------------------------------
        self._bases = (voices.names("Breath") + voices.names(voices.GROUP_VOCAL)
                       + voices.names(voices.GROUP_SYNTH)
                       + voices.names(voices.GROUP_TONAL))
        self._cfg = voices.to_dict(voices.get_voice(self._bases[0]))
        self._build_form()

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(130)
        self._debounce.timeout.connect(self._preview)

        self._load_widgets()
        self._on_phase("both")
        self._ready = True
        self._preview()

    # --- form construction -------------------------------------------------
    def _slider(self, body, label, key, lo, hi, mul=1.0, decimals=0, suffix=""):
        s = LabeledSlider(label, lo, hi, lo, decimals=decimals, suffix=suffix,
                          on_change=lambda _v: self._changed())
        body.addWidget(s)
        self._sliders[key] = (s, mul)

    def _combo(self, body, label, key, items):
        wrap, box = combo_row(label, items, items[0],
                              on_change=lambda _v: self._changed())
        body.addWidget(wrap)
        self._combos[key] = box

    def _build_form(self):
        # Source voice + name + kind + both-breath loudness.
        frame, body = card("Voice")
        wrap, self._base_box = combo_row("Start from", self._bases,
                                         self._bases[0], on_change=self._on_base)
        body.addWidget(wrap)
        body.addWidget(muted("Name"))
        self._name = QLineEdit("My Voice")
        body.addWidget(self._name)
        self._combo(body, "Kind (engine)", "kind", _KINDS)
        wrap, self._loud_box = combo_row(
            "Both-breath loudness", [n for n, _ in _LOUD], _LOUD[0][0],
            on_change=lambda _v: self._changed())
        body.addWidget(wrap)
        self._body.addWidget(frame)

        frame, body = card("Source & timbre")
        self._combo(body, "Source", "source", _SRC)
        self._combo(body, "Noise colour", "noise", _NOISE)
        self._slider(body, "Voicing %", "voicing", 0, 100, mul=100)
        self._combo(body, "Vowel / shape", "vowel", _SHAPES)
        self._combo(body, "Glide to shape", "vowel_to", _SHAPES)
        self._body.addWidget(frame)

        frame, body = card("Pitch & harmonics")
        self._slider(body, "Pitch (Hz)", "pitch", 40, 500)
        self._slider(body, "Harmonics", "n_harm", 4, 40)
        self._slider(body, "Drone base (Hz)", "base_freq", 40, 500)
        self._body.addWidget(frame)

        frame, body = card("Filter & brightness")
        self._combo(body, "Filter type", "_ftype", _FILT)
        self._slider(body, "Filter freq (Hz)", "_ffreq", 60, 9000)
        self._slider(body, "Filter Q x100", "_fq", 10, 1500, mul=100)
        self._slider(body, "Brightness (Hz)", "bright_base", 100, 9000)
        self._slider(body, "Bright mod (Hz)", "bright_mod", 0, 5000)
        self._slider(body, "Exhale bright x100", "exhale_mul", 0, 200, mul=100)
        self._body.addWidget(frame)

        frame, body = card("Modulation")
        self._slider(body, "Vibrato rate (Hz)", "vibrato_rate", 0, 12, decimals=1)
        self._slider(body, "Vibrato depth x1000", "vibrato_depth", 0, 40, mul=1000)
        self._slider(body, "Tremolo rate (Hz)", "am_rate", 0, 40, decimals=1)
        self._slider(body, "Tremolo depth %", "am_depth", 0, 100, mul=100)
        self._slider(body, "Pitch glide (semis)", "pitch_glide", 0, 24)
        self._combo(body, "Glide shape", "glide_shape", _GLIDE)
        self._body.addWidget(frame)

        frame, body = card("Shape & space")
        self._combo(body, "Attack", "attack", _ATTACK)
        self._slider(body, "Air %", "air", 0, 100, mul=100)
        self._slider(body, "Floor %", "floor", 0, 100, mul=100)
        self._slider(body, "Stereo width %", "width", 0, 100, mul=100)
        self._slider(body, "Pan rate (Hz)", "pan_rate", 0, 20, decimals=1)
        self._slider(body, "Pan depth %", "pan_depth", 0, 100, mul=100)
        self._body.addWidget(frame)

        frame, body = card("Output")
        self._slider(body, "Gain %", "gain", 0, 300, mul=100)
        self._body.addWidget(frame)
        self._body.addStretch(1)

    # --- config <-> widgets ------------------------------------------------
    def _loud_env(self):
        return dict(_LOUD).get(self._loud_box.currentText(), "airflow")

    def _env_now(self):
        return _PHASE_ENV.get(self._key, self._loud_env())

    def _collect_widgets(self):
        d = {}
        for k, (s, mul) in self._sliders.items():
            if not k.startswith("_"):
                d[k] = s.value() / mul
        for k, box in self._combos.items():
            if not k.startswith("_"):
                d[k] = box.currentText()
        d["filt"] = [self._combos["_ftype"].currentText(),
                     self._sliders["_ffreq"][0].value(),
                     self._sliders["_fq"][0].value() / self._sliders["_fq"][1]]
        d["n_harm"] = int(round(d.get("n_harm", 18)))
        return d

    def _load_widgets(self):
        f = self._cfg.get("filt") or ["bandpass", 600.0, 1.0]
        pseudo = {"_ffreq": f[1], "_fq": f[2]}
        for k, (s, mul) in self._sliders.items():
            v = float(pseudo.get(k, self._cfg.get(k, 0) or 0)) * mul
            s.set_value(v)
        for k, box in self._combos.items():
            if k == "_ftype":
                val = f[0]
            else:
                val = self._cfg.get(k, box.currentText()) or box.currentText()
            box.blockSignals(True)
            box.setCurrentText(str(val))
            box.blockSignals(False)
        env = self._cfg.get("env", "airflow")
        loud = next((n for n, e in _LOUD if e == env), _LOUD[0][0])
        self._loud_box.blockSignals(True)
        self._loud_box.setCurrentText(loud)
        self._loud_box.blockSignals(False)

    def _current(self, name):
        self._cfg.update(self._collect_widgets())
        d = dict(self._cfg)
        d["env"], d["name"] = self._env_now(), name
        d.pop("group", None)
        return d

    # --- behaviour ---------------------------------------------------------
    def _preview(self):
        d = self._current("(preview)")
        voices.register_from_dict(d)
        try:
            self.engine.set_voice_a("(preview)")
        except Exception:
            pass
        self.wave.set_data(render_mix([d], self.sr, self.persona), self.sr)

    def _changed(self):
        if not self._ready:
            return
        self._debounce.start()

    def _on_phase(self, key):
        self._key = key
        for k, b in self._phase_btns.items():
            b.setChecked(k == key)
        self._loud_box.setEnabled(key == "both")
        self._note.setText(_PHASE_NOTE[key])
        if self._ready:
            self._preview()

    def _on_base(self, _name=None):
        self._cfg = voices.to_dict(voices.get_voice(self._base_box.currentText()))
        self._load_widgets()
        if self._ready:
            self._preview()

    def _randomize(self):
        def set_combo(key, val):
            box = self._combos[key]
            box.blockSignals(True)
            box.setCurrentText(val)
            box.blockSignals(False)
        set_combo("kind", random.choice(["noise", "noise", "vocal", "tonal"]))
        set_combo("source", random.choice(_SRC))
        set_combo("noise", random.choice(_NOISE))
        set_combo("vowel", random.choice(_SHAPES))
        set_combo("_ftype", random.choice(_FILT))
        for k, lo, hi, mul in (("voicing", 0, 100, 100), ("pitch", 80, 300, 1),
                               ("_ffreq", 200, 6000, 1), ("_fq", 30, 600, 1),
                               ("bright_base", 400, 7000, 1),
                               ("bright_mod", 0, 3000, 1),
                               ("vibrato_rate", 0, 7, 1),
                               ("vibrato_depth", 0, 18, 1000),
                               ("am_rate", 0, 24, 1), ("am_depth", 0, 90, 100),
                               ("air", 0, 60, 100), ("width", 0, 80, 100),
                               ("gain", 30, 140, 100)):
            self._sliders[k][0].set_value(random.uniform(lo, hi))
        self._preview()

    def _save(self):
        name = self._name.text().strip() or "My Voice"
        d = self._current(name)
        store.save_voice(d)
        voices.register_from_dict(d)
        try:
            voices.unregister("(preview)")
        except Exception:
            pass
        self.win.rebuild_menu()
        if self._key == "out":
            self.engine.set_voice_a(self._prev_a)
            self.engine.set_voice_out(d["name"])
        else:
            self.engine.set_voice_a(d["name"])
            self.engine.set_voice_out(None if self._key == "both"
                                      else self._prev_out)
        self._saved = True
        self.win.panel.sync()
        self.accept()

    def _play(self):
        try:
            import sounddevice as sd

            from breathsim import dsp
            buf = render_mix([self._current("(preview)")], self.sr, self.persona,
                             seconds=4.0)
            sd.play(dsp.soft_clip(buf * 0.9), self.sr)
        except Exception:
            self._preview()

    def _close(self):
        self.reject()

    def reject(self):
        self._cleanup()
        super().reject()

    def _cleanup(self):
        if not self._saved:
            try:
                voices.unregister("(preview)")
            except Exception:
                pass
            try:
                self.engine.set_voice_a(self._prev_a)
                self.engine.set_voice_out(self._prev_out)
            except Exception:
                pass
            try:
                self.win.panel.sync()
            except Exception:
                pass

    def closeEvent(self, ev):
        self._cleanup()
        super().closeEvent(ev)
