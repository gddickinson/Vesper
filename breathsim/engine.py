"""Real-time audio engine.

Runs a sounddevice output stream whose callback renders and mixes a small set
of :class:`Layer` objects (a primary voice plus optional ambience), each
fading in/out for click-free voice changes, and one-shot transition chimes.
All synthesis is driven by breath state pulled from the
:class:`~breathsim.controller.BreathController`.
"""
from __future__ import annotations

import queue
import threading

import numpy as np
import sounddevice as sd

from . import dsp, personas, timestretch, tracks, voices
from .controller import BreathController

WORD_FILL = 0.95          # a stretched word fills this fraction of the exhale
WORD_RATIO_MAX = 12.0     # cap the stretch so very short words stay intelligible


def _default_samplerate() -> int:
    try:
        return int(sd.query_devices(kind="output")["default_samplerate"])
    except Exception:
        return 44100


class Layer:
    """A track plus a gain that ramps toward a target for smooth fades."""

    def __init__(self, track, slot: str, sr: int, fade: float = 0.35,
                 target: float = 1.0):
        self.track = track
        self.slot = slot
        self.gain = 0.0
        self.target = target
        self.step = (1.0 / max(fade, 0.001)) / sr     # gain change per sample
        self.dead = False

    def render(self, frames, s0, s1):
        start = self.gain
        max_delta = self.step * frames
        diff = self.target - self.gain
        delta = max(-max_delta, min(max_delta, diff))
        self.gain = start + delta
        if self.target <= 0.0 and self.gain <= 1e-4:
            self.dead = True
        ramp = np.linspace(start, self.gain, frames)[:, None]
        return self.track.render(frames, s0, s1) * ramp


class Chime:
    """A short inharmonic bell rendered as a one-shot."""

    RATIOS = (1.0, 2.01, 3.01, 4.18)
    AMPS = (1.0, 0.5, 0.3, 0.17)

    def __init__(self, kind: str, sr: int):
        base = 660.0 if kind == "in" else 392.0
        self.sr = sr
        self.freqs = [base * r for r in self.RATIOS]
        self.phase = [0.0] * len(self.RATIOS)
        self.age = 0
        self.tau = 0.85 * sr
        self.attack = max(1, int(0.004 * sr))
        self.gain = 0.3
        self.dead = False

    def render(self, frames: int) -> np.ndarray:
        idx = np.arange(frames)
        env = np.exp(-(self.age + idx) / self.tau)
        if self.age < self.attack:
            env = env * np.clip((self.age + idx) / self.attack, 0.0, 1.0)
        out = np.zeros(frames)
        steps = np.arange(1, frames + 1)
        for i, f in enumerate(self.freqs):
            inc = dsp.TWO_PI * f / self.sr
            ph = self.phase[i] + inc * steps
            out += self.AMPS[i] * np.sin(ph)
            self.phase[i] = float(ph[-1] % dsp.TWO_PI)
        out *= env * self.gain
        self.age += frames
        if np.exp(-self.age / self.tau) < 1e-3:
            self.dead = True
        return out


class AudioEngine:
    def __init__(self, controller: BreathController, sr: int | None = None,
                 blocksize: int = 2048):   # ~46ms: headroom against callback jitter
                                           # (Kokoro synth / GC) that caused crackle
        self.controller = controller
        self.sr = sr or _default_samplerate()
        self.block = blocksize
        self.lock = threading.RLock()
        self.layers: list[Layer] = []
        self.persona = personas.DEFAULT
        self.slot_voice: dict[str, str | None] = {}
        self.morph = 0.0                 # 0 = Voice A .. 1 = Voice B
        self.voice_a: str | None = None    # the inhale / main voice
        self.voice_b: str | None = None
        self.voice_out: str | None = None  # separate exhale voice (None = same)
        self.voice_word: str | None = None  # spoken word voiced on each exhale
        self.word_blend = 1.0              # 1 = word overrides exhale voice, <1 blends
        self.word_match = 0.0              # 0 = natural word .. 1 = time-warped to breath
        self._word_src = None              # original mono word clip
        self._word_buf = None              # prepared (possibly stretched) clip to play
        self._word_gain = 1.0
        self._word_exhale = 0.0            # exhale length the buffer was prepared for
        self._word_token = 0               # guards stale background stretches
        self.phrase = None                 # active chant/song phrase (overrides)
        self.chant_style = "per_breath"    # per_breath | per_phrase
        self.chant_recite = True           # mantras on a steady reciting tone
        # per-slot mix gain (default 1.0); effects sit a touch under unity
        self.slot_levels: dict[str, float] = {"effects": 0.85}
        self.master = 0.0
        self.master_target = 0.0
        self._req_vol = 0.0           # last requested master volume (pre-cap)
        self.vol_cap = 1.0            # upper bound on output (e.g. quiet-hours softening)
        self.chime_enabled = False
        self.spatial = True               # gentle stereo width + auto-pan on ambience
        self._chime_q: queue.Queue = queue.Queue()
        self._chimes: list[Chime] = []
        self.stream = None
        self.available = False

    # --- public control ----------------------------------------------------

    def _swap_layer(self, slot, track, fade, target=None):
        if target is None:
            target = self.slot_levels.get(slot, 1.0)
        with self.lock:
            for ly in self.layers:
                if ly.slot == slot:
                    ly.target = 0.0
            if track is not None:
                self.layers.append(
                    Layer(track, slot, self.sr, fade=fade, target=target))

    def _build_primary_track(self):
        if self.phrase is not None:                 # chant/song sequence voice
            from . import phrases as ph
            from .vocal import VocalTrack
            track = VocalTrack(ph.config(self.phrase), self.sr, self.persona)
            recite = (self.chant_recite
                      and self.phrase.category in ("Mantra", "Chant Sounds"))
            track.set_sequence(self.phrase.segments, self.phrase.base_pitch,
                               self.chant_style, self.phrase.groups,
                               monotone=recite)
            return track
        a_cfg = voices.get_voice(self.voice_a) if self.voice_a else None
        if a_cfg is None:
            return None
        a_track = tracks.build_track(a_cfg, self.sr, self.persona)
        b_cfg = voices.get_voice(self.voice_b) if self.voice_b else None
        if (b_cfg is not None and a_cfg.group in voices.MORPHABLE
                and b_cfg.group in voices.MORPHABLE):
            b_track = tracks.build_track(b_cfg, self.sr, self.persona)
            return tracks.MorphTrack(a_track, b_track, lambda: self.morph)
        return a_track

    def _word_level(self):
        """Live mix level for the spoken-word layer (0 when no word set)."""
        return self.word_blend if self.voice_word else 0.0

    def _exhale_duck(self):
        """Live multiplier for the exhale voice: 1 with no word, falling to 0 as
        the word blend rises to a full override."""
        return (1.0 - self.word_blend) if self.voice_word else 1.0

    def _rebuild_primary(self, fade: float = 0.35):
        self.slot_voice["primary"] = self.voice_a
        track = self._build_primary_track()
        if track is not None and self.phrase is None:
            if self.voice_out:
                track = tracks.PhaseGateTrack(track, "inhale")  # gate main to inhale
            elif self.voice_word:                  # no separate exhale voice:
                track = tracks.ExhaleDuckTrack(track, self._exhale_duck)  # duck its exhale
        self._swap_layer("primary", track, fade)

    def _rebuild_exhale(self, fade: float = 0.35):
        cfg = voices.get_voice(self.voice_out) if self.voice_out else None
        if cfg is not None:
            tr = tracks.PhaseGateTrack(
                tracks.build_track(cfg, self.sr, self.persona), "exhale")
            if self.voice_word:
                tr = tracks.GainTrack(tr, self._exhale_duck)
            self.slot_voice["exhale"] = self.voice_out
            self._swap_layer("exhale", tr, fade)
        else:
            self.slot_voice["exhale"] = None
            self._swap_layer("exhale", None, fade)

    def set_word(self, name: str | None, fade: float = 0.35):
        """Set a spoken word voiced once on each exhale (a ``Word: …`` voice).
        :meth:`set_word_blend` mixes it against the exhale voice; :meth:`set_word_match`
        time-warps and shapes it to the breath."""
        if name in (None, "", "None"):
            name = None
        self.voice_word = name
        self.slot_voice["word"] = name
        cfg = voices.get_voice(name) if name else None
        if cfg is not None:
            data = np.asarray(cfg.data, dtype=float)
            if data.ndim > 1:
                data = data.mean(axis=1)
            self._word_src = data
            self._word_gain = cfg.gain
            self._word_buf = None
            self._prepare_word()
            tr = tracks.BreathWordTrack(self.sr, lambda: self._word_buf,
                                        lambda: self.word_match)
            self._swap_layer("word", tracks.GainTrack(tr, self._word_level),
                             fade, target=1.0)
        else:
            self._word_src = self._word_buf = None
            self._swap_layer("word", None, fade)
        self._rebuild_primary(fade)    # (re)apply or drop the exhale duck
        self._rebuild_exhale(fade)

    def set_word_blend(self, amount: float):
        """0 = word silent (exhale voice full) .. 1 = word overrides the exhale
        voice. Read live by the word and exhale layers; no rebuild needed."""
        self.word_blend = float(min(max(amount, 0.0), 1.0))

    def set_word_match(self, amount: float):
        """0 = word plays at its natural length/shape .. 1 = time-stretched to
        fill the exhale and shaped by the breath. Re-stretches the clip."""
        self.word_match = float(min(max(amount, 0.0), 1.0))
        self._prepare_word()

    def _prepare_word(self):
        """(Re)build the word buffer for the current match + exhale length. The
        stretch (WSOLA) runs on a daemon thread so it never blocks audio/UI; the
        word keeps its current buffer until the new one is ready."""
        src = self._word_src
        if src is None:
            self._word_buf = None
            return
        exhale = max(0.0, float(self.controller.pattern.exhale))
        self._word_exhale = exhale
        natural = len(src) / self.sr
        ratio = 1.0
        if self.word_match > 0.001 and exhale >= 0.2 and natural > 0:
            target = natural + (exhale * WORD_FILL - natural) * self.word_match
            ratio = min(max(target / natural, 0.25), WORD_RATIO_MAX)
        if abs(ratio - 1.0) <= 1e-2:
            self._word_buf = src * self._word_gain
            return
        if self._word_buf is None:                 # play natural until ready
            self._word_buf = src * self._word_gain
        self._word_token += 1
        tok, gain = self._word_token, self._word_gain

        def work():
            buf = timestretch.time_stretch(src, ratio) * gain
            if tok == self._word_token:
                self._word_buf = buf

        threading.Thread(target=work, daemon=True).start()

    def maybe_reprepare_word(self):
        """Re-stretch the word if the exhale length has changed (called off the
        audio thread, e.g. from the GUI loop). Cheap no-op otherwise."""
        if self._word_src is not None and self.word_match > 0.001 and (
                abs(float(self.controller.pattern.exhale) - self._word_exhale)
                > 0.05):
            self._prepare_word()

    def set_voice(self, name: str | None, slot: str = "primary",
                  fade: float = 0.35):
        """Set the voice in *slot*. ``primary`` sets Voice A of the morph pair;
        any other slot (e.g. ``ambience``) holds a single voice."""
        if slot == "primary":
            self.set_voice_a(name, fade)
            return
        self.slot_voice[slot] = name
        cfg = voices.get_voice(name) if name else None
        track = tracks.build_track(cfg, self.sr, self.persona) if cfg else None
        if track is not None and slot == "ambience" and self.spatial:
            from .spatial import SpatialTrack, Spatializer    # widen the bed gently
            track = SpatialTrack(track, Spatializer(self.sr))
        self._swap_layer(slot, track, fade)

    def set_spatial(self, on: bool):
        """Toggle the gentle ambience stereo width/auto-pan; re-wrap live."""
        self.spatial = bool(on)
        amb = self.slot_voice.get("ambience")
        if amb:
            self.set_voice(amb, "ambience")

    def set_voice_a(self, name: str | None, fade: float = 0.35):
        self.voice_a = name
        self.phrase = None                  # a normal voice clears any phrase
        self._rebuild_primary(fade)

    def set_phrase(self, phrase, fade: float = 0.35):
        """Play a chant/song phrase as the primary voice (None to revert). Adopts
        the phrase's own preferred grouping (``per_phrase`` sings the whole phrase
        across one exhale; ``per_breath`` is one syllable per breath)."""
        self.phrase = phrase
        if phrase is not None:
            self.voice_out = None
            self.chant_style = getattr(phrase, "style", None) or self.chant_style
            self._rebuild_exhale(fade)
        self._rebuild_primary(fade)

    def set_chant_style(self, style: str):
        """'per_breath' (one syllable/breath) or 'per_phrase' (whole phrase)."""
        self.chant_style = style
        if self.phrase is not None:
            self._rebuild_primary()

    def set_chant_recite(self, on: bool):
        """Reciting tone: chant mantras on a steady tonic (vs. melodic)."""
        self.chant_recite = bool(on)
        if self.phrase is not None:
            self._rebuild_primary()

    def set_voice_b(self, name: str | None, fade: float = 0.35):
        self.voice_b = name
        self._rebuild_primary(fade)

    def set_voice_out(self, name: str | None, fade: float = 0.35):
        """Set a separate exhale voice. None / 'Same as inhale' => one voice
        plays the whole breath (the default)."""
        if name in (None, "", "Same", "Same as inhale"):
            name = None
        self.voice_out = name
        self._rebuild_primary(fade)
        self._rebuild_exhale(fade)

    def set_morph(self, amount: float):
        """Live morph A->B (0..1); read by the audio thread each block."""
        self.morph = float(min(max(amount, 0.0), 1.0))

    def set_layer(self, slot: str, name: str | None, level: float = 1.0,
                  transpose: float = 0.0, persona=None, fade: float = 0.4):
        """Overlay an extra voice in *slot* at *level*, transposed *transpose*
        semitones. Used to stack chant/singing voices into a choir/chord."""
        self.slot_voice[slot] = name
        cfg = voices.get_voice(name) if name else None
        if cfg is None:
            self._swap_layer(slot, None, fade)
            return
        factor = 2.0 ** (transpose / 12.0)
        track = tracks.build_track(cfg, self.sr, persona or self.persona, factor)
        with self.lock:
            for ly in self.layers:
                if ly.slot == slot:
                    ly.target = 0.0
            self.layers.append(
                Layer(track, slot, self.sr, fade=fade, target=level))

    def set_layer_level(self, slot: str, level: float):
        with self.lock:
            for ly in self.layers:
                if ly.slot == slot and ly.target > 0.0:
                    ly.target = float(min(max(level, 0.0), 1.0))

    def set_slot_level(self, slot: str, level: float):
        """Set the mix level for a slot (primary/ambience/effects) and remember
        it so the level survives voice changes that rebuild the layer."""
        level = float(min(max(level, 0.0), 1.0))
        self.slot_levels[slot] = level
        self.set_layer_level(slot, level)

    def set_slot_muted(self, slot: str, muted: bool):
        """Toggle a whole slot on/off (mute to 0, or restore its mix level)
        without forgetting its level or its assigned voice."""
        target = 0.0 if muted else self.slot_levels.get(slot, 1.0)
        with self.lock:
            for ly in self.layers:
                if ly.slot == slot:
                    ly.target = target

    def set_persona(self, persona):
        """Set the voice body; rebuild persona-dependent voices in place."""
        self.persona = persona
        self._rebuild_primary()
        self._rebuild_exhale()
        amb = self.slot_voice.get("ambience")
        amb_cfg = voices.get_voice(amb) if amb else None
        if amb_cfg is not None and amb_cfg.kind == "vocal":
            self.set_voice(amb, "ambience")

    def set_master_volume(self, vol: float):
        self._req_vol = float(min(max(vol, 0.0), 1.0))
        self.master_target = min(self._req_vol, self.vol_cap)   # cap = upper bound only

    def set_volume_cap(self, cap: float):
        """An upper bound on the output (1.0 = no cap); re-clamps the live target.
        Used by quiet-hours softening -- it only ever lowers, never raises."""
        self.vol_cap = float(min(max(cap, 0.0), 1.0))
        self.master_target = min(self._req_vol, self.vol_cap)

    def set_chime(self, enabled: bool):
        self.chime_enabled = bool(enabled)

    def trigger_chime(self, kind: str):
        if self.chime_enabled:
            self._chime_q.put(kind)

    def start(self) -> bool:
        if self.stream is not None:
            return self.available
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sr, blocksize=self.block, channels=2,
                dtype="float32", callback=self._callback)
            self.stream.start()
            self.available = True
        except Exception as exc:  # no audio device, etc. -> visual-only mode
            print(f"[breathsim] audio unavailable: {exc}")
            self.stream = None
            self.available = False
        return self.available

    def stop(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        self.stream = None
        self.available = False

    # --- audio callback ----------------------------------------------------

    def _callback(self, outdata, frames, time_info, status):
        try:
            elapsed = self.controller.elapsed()
            dt = frames / self.sr
            s0 = self.controller.state_at(elapsed)
            s1 = self.controller.state_at(elapsed + dt)
            buf = np.zeros((frames, 2))
            with self.lock:
                while not self._chime_q.empty():
                    self._chimes.append(Chime(self._chime_q.get(), self.sr))
                alive = []
                for ly in self.layers:
                    buf += ly.render(frames, s0, s1)
                    if not ly.dead:
                        alive.append(ly)
                self.layers = alive
                if self._chimes:
                    mono = np.zeros(frames)
                    keep = []
                    for ch in self._chimes:
                        mono += ch.render(frames)
                        if not ch.dead:
                            keep.append(ch)
                    self._chimes = keep
                    buf[:, 0] += mono
                    buf[:, 1] += mono
                target = self.master_target
            gain = np.linspace(self.master, target, frames)[:, None]
            self.master = target
            outdata[:] = dsp.soft_clip(buf * gain).astype(np.float32)
        except Exception:
            outdata.fill(0)
