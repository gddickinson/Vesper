"""Sequential, fading narration for the bedtime storyteller.

Two engines, chosen automatically:
* **Kokoro** neural TTS (``kokoro_tts``) when its model is installed -- natural,
  clearly-vocalised voices; we also expose the live audio **amplitude** (``amp``)
  so the talking-head face can lip-sync.
* macOS **``say``** as a fallback.

Speaks a *stream* of story units one at a time on a background thread, softly,
slowing + quietening as the session winds down. A **generation token** makes a
voice/scene change kill the old thread, so two narrators can never overlap.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time

from . import kokoro_tts, xtts_tts

# macOS ``say`` fallback voices, in preference order. A British female leads (to
# match the app's British-female default), then other soft, clear voices.
RELAXING = ["Serena", "Stephanie", "Kate", "Martha", "Jamie", "Zoe", "Ava",
            "Samantha", "Allison", "Susan", "Moira", "Daniel", "Oliver"]

# British-female say voices (the preferred fallback when Kokoro isn't installed).
_UK_FEMALE = {"Serena", "Stephanie", "Kate", "Martha", "Jamie", "Kathryn"}


def _say_voices(speech):
    if not speech.available:
        return []
    out, seen = [], set()
    for base in RELAXING:
        v = speech._resolve(base)
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    for n in sorted(speech._installed):
        if ("(Premium)" in n or "(Enhanced)" in n) and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _base(v):
    return str(v).split(" (")[0]


def _say_best(speech):
    vs = _say_voices(speech)
    # Prefer a British female, ideally a Premium/Enhanced one.
    for tag in ("(Premium)", "(Enhanced)"):
        for v in vs:
            if _base(v) in _UK_FEMALE and tag in v:
                return v
    for v in vs:
        if _base(v) in _UK_FEMALE:
            return v
    for tag in ("(Premium)", "(Enhanced)"):     # else the best non-UK voice
        for v in vs:
            if tag in v:
                return v
    return vs[0] if vs else speech.voice_id


def available_voices(speech):
    """Voices the user can pick. XTTS voices (opt-in, highest quality) lead when
    configured, then the default engine's voices (Kokoro if installed, else say)."""
    out = list(xtts_tts.voice_names()) if xtts_tts.ready() else []
    out += kokoro_tts.voice_names() if kokoro_tts.ready() else _say_voices(speech)
    return out


def best_voice(speech):
    """The default voice -- NOT XTTS (that stays opt-in). Kokoro if installed."""
    return kokoro_tts.best_voice() if kokoro_tts.ready() else _say_best(speech)


# --- friendly labels for the voice picker ----------------------------------
_LANG = {"a": "American", "b": "British", "e": "Spanish", "f": "French",
         "h": "Hindi", "i": "Italian", "j": "Japanese", "p": "Portuguese",
         "z": "Chinese"}
_GENDER = {"f": "female", "m": "male"}


def recommended(speech=None):
    """The set of 'best' voice ids/names across engines (shown starred)."""
    rec = set(xtts_tts.RECOMMENDED) if xtts_tts.ready() else set()
    rec |= set(kokoro_tts.RECOMMENDED) if kokoro_tts.ready() else set(_UK_FEMALE)
    return rec


def is_recommended(voice, speech=None):
    v = str(voice)
    rec = recommended(speech)
    return (v in rec or _base(v) in rec
            or "(Premium)" in v or "(Enhanced)" in v)


def voice_label(voice, speech=None):
    """A human label for *voice*: friendly name + accent/gender, a leading star if
    it is one of the most realistic. Works for Kokoro ids (e.g. ``bf_emma``) and
    macOS ``say`` names alike."""
    if not voice:
        return "(no voice)"
    v = str(voice)
    star = "★ " if is_recommended(v, speech) else ""
    if v.startswith(xtts_tts.PREFIX):                  # high-quality XTTS studio voice
        from . import xtts_voices
        return f"{star}{xtts_voices.label(v[len(xtts_tts.PREFIX):])}"
    if len(v) >= 4 and v[2] == "_" and v[0] in _LANG and v[1] in _GENDER:
        name = v[3:].replace("_", " ").title()
        return f"{star}{name} - {_LANG[v[0]]} {_GENDER[v[1]]}"
    base = _base(v)
    tag = (" - premium" if "(Premium)" in v
           else " - enhanced" if "(Enhanced)" in v else "")
    return f"{star}{base}{tag}"


def voice_groups(speech):
    """Ordered ``[(header, [voice_id, ...])]`` for a grouped picker: a cross-engine
    Recommended shortcut, then XTTS by gender, then Kokoro by accent (or system)."""
    from . import xtts_voices
    groups, rec = [], []
    if xtts_tts.ready():
        rec += [xtts_tts.PREFIX + n for n in xtts_voices.curated()
                if xtts_voices.is_recommended(n)]
    if kokoro_tts.ready():
        have = set(kokoro_tts.voice_names())
        rec += [v for v in kokoro_tts.RECOMMENDED if v in have]
    if rec:
        groups.append(("Recommended", rec))
    if xtts_tts.ready():
        bg = xtts_voices.by_gender()
        pre = xtts_tts.PREFIX
        if bg.get("f"):
            groups.append(("High quality · female (XTTS)",
                           [pre + n for n in bg["f"]]))
        if bg.get("m"):
            groups.append(("High quality · male (XTTS)",
                           [pre + n for n in bg["m"]]))
    if kokoro_tts.ready():
        ids = kokoro_tts.voice_names()
        brit = [v for v in ids if v[:1] == "b"]
        amer = [v for v in ids if v[:1] == "a"]
        other = [v for v in ids if v[:1] not in ("a", "b")]
        for head, lst in (("British (Kokoro)", brit), ("American (Kokoro)", amer),
                          ("Other languages (Kokoro)", other)):
            if lst:
                groups.append((head, lst))
    else:
        sv = _say_voices(speech)
        if sv:
            groups.append(("System voices (macOS)", sv))
    return groups


def engine_label(speech):
    base = ("Kokoro (neural)" if kokoro_tts.ready()
            else "macOS say" if speech and speech.available else None)
    if base and xtts_tts.ready():
        return base + " · XTTS available"
    return base


def _envelope(samples, sr, win_ms=40.0):
    import numpy as np
    arr = np.asarray(samples, dtype="float32").reshape(-1)
    if arr.size == 0 or sr <= 0:
        return []
    win = max(1, int(sr * win_ms / 1000.0))
    rmss, mx = [], 1e-6
    for i in range(0, arr.size, win):
        c = arr[i:i + win]
        r = float(np.sqrt(np.mean(c * c))) if c.size else 0.0
        mx = max(mx, r)
        rmss.append(r)
    return [(j * win / sr, min(1.0, r / mx)) for j, r in enumerate(rmss)]


def _write_wav(samples, sr):
    try:
        import soundfile as sf
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".wav", prefix="breathsim_tts_")
        os.close(fd)
        sf.write(path, samples, int(sr))
        return path
    except Exception:
        return None


class Narrator:
    def __init__(self, speech):
        self.speech = speech
        self.binary = speech.binary
        self.voice = None
        self.amp = 0.0                            # live speaking amplitude (lip-sync)
        self.speed = 1.0                          # speech-rate multiplier (<1 slower)
        self.pause_scale = 1.0                    # between-statement pause multiplier
        self._proc = None
        self._stop = True
        self._token = 0

    @property
    def engine(self):
        if kokoro_tts.ready():
            return "kokoro"
        return "say" if self.binary else None

    def _engine_for(self, voice):
        """Pick the engine from the chosen voice -- an ``xtts:`` voice routes to the
        opt-in XTTS engine, otherwise the default (Kokoro if installed, else say)."""
        if voice and str(voice).startswith(xtts_tts.PREFIX) and xtts_tts.ready():
            return "xtts"
        if kokoro_tts.ready():
            return "kokoro"
        return "say" if self.binary else None

    @property
    def available(self):
        return self.engine is not None

    def set_voice(self, voice):
        self.voice = voice or None

    # --- lifecycle ---------------------------------------------------------
    def start(self, units, level_fn, timing_fn=None, text_cb=None):
        voice = self.voice or best_voice(self.speech)
        engine = self._engine_for(voice)
        if engine is None:
            self.stop()
            return
        self._token += 1
        tok = self._token
        self._stop = False
        self._kill_proc()
        threading.Thread(
            target=self._loop,
            args=(tok, units, level_fn, timing_fn, text_cb, voice, engine),
            daemon=True).start()

    def stop(self):
        self._stop = True
        self._token += 1
        self.amp = 0.0
        self._kill_proc()

    def _active(self, tok):
        return not self._stop and tok == self._token

    def _loop(self, tok, units, level_fn, timing_fn, text_cb, voice, engine):
        for unit in units:
            if not self._active(tok):
                break
            try:
                lvl = level_fn()
            except Exception:
                lvl = 1.0
            if lvl < 0.04:
                break
            if text_cb:
                try:
                    text_cb(unit)
                except Exception:
                    pass
            uv = unit.get("voice") or voice            # per-line voice (cast reading)
            if engine == "kokoro":
                self._speak_neural(tok, unit, lvl, timing_fn, uv, kokoro_tts.synth)
            elif engine == "xtts":
                self._speak_neural(tok, unit, lvl, timing_fn, uv, xtts_tts.synth)
            else:
                self._speak_say(tok, unit, lvl, timing_fn, uv)
        self.amp = 0.0
        self._kill_proc()

    # --- pacing ------------------------------------------------------------
    def _pause_ms(self, unit, timing_fn):
        phase = unit.get("phase")
        if phase and timing_fn:                   # breath-cued: match the breath
            try:
                inh, exh = timing_fn()
                return max(200, min(20000,
                                    int((inh if phase == "in" else exh) * 1000)))
            except Exception:
                pass
        pause = int(int(unit.get("pause", 900)) * self.pause_scale)
        return max(200, min(20000, pause))

    def _wait(self, tok, ms):
        end = time.time() + ms / 1000.0
        while time.time() < end:
            if not self._active(tok):
                return
            time.sleep(0.05)

    def _rate(self, lvl):
        wpm = (140 - 28 * (1.0 - max(0.0, min(1.0, lvl)))) * self.speed
        return int(max(70, min(180, wpm)))

    def _speed(self, lvl):
        """Kokoro speed: the level relationship, scaled by the speed multiplier."""
        base = 0.82 + 0.12 * (max(0.0, min(1.0, lvl)) - 0.5)
        return max(0.6, min(1.1, base * self.speed))

    @staticmethod
    def _terminate(proc):
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def _kill_proc(self):
        self._terminate(self._proc)

    # --- backends ----------------------------------------------------------
    def _speak_say(self, tok, unit, lvl, timing_fn, voice):
        vol = max(0.05, min(0.8, 0.6 * lvl))
        pause = self._pause_ms(unit, timing_fn)
        txt = str(unit.get("text", "")).replace("[", "(").replace("]", ")")
        text = f"[[volm {vol:.2f}]] {txt} [[slnc {pause}]]"
        try:
            self._proc = subprocess.Popen(
                [self.binary, "-v", voice, "-r", str(self._rate(lvl)), text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return
        self.amp = 0.4                            # approximate mouth while speaking
        while self._proc and self._proc.poll() is None:
            if not self._active(tok):
                self._terminate(self._proc)
                break
            time.sleep(0.1)
        self.amp = 0.0

    def _speak_neural(self, tok, unit, lvl, timing_fn, voice, synth):
        """Shared playback for the neural engines (Kokoro / XTTS): synth -> short
        edge fades -> afplay, driving the lip-sync ``amp`` from the envelope."""
        import numpy as np
        speed = self._speed(lvl)
        r = synth(str(unit.get("text", "")), voice, speed)
        if not self._active(tok) or r is None:
            return self._wait(tok, self._pause_ms(unit, timing_fn))
        samples, sr = r
        vol = max(0.05, min(0.85, 0.62 * lvl))
        samples = np.asarray(samples, dtype="float32").reshape(-1) * vol
        # Short raised-cosine fades at both edges so the per-sentence afplay
        # process doesn't click/pop when CoreAudio starts and stops it.
        nf = min(int(sr * 0.010), samples.size // 2)
        if nf > 0:
            ramp = (0.5 - 0.5 * np.cos(
                np.linspace(0.0, np.pi, nf, dtype="float32")))
            samples[:nf] *= ramp
            samples[-nf:] *= ramp[::-1]
        env = _envelope(samples, sr)
        path = _write_wav(samples, sr)
        if not path:
            return self._wait(tok, self._pause_ms(unit, timing_fn))
        try:
            self._proc = subprocess.Popen(["afplay", path],
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
        except Exception:
            self._unlink(path)
            return self._wait(tok, self._pause_ms(unit, timing_fn))
        t0, i = time.time(), 0
        while self._proc and self._proc.poll() is None:
            if not self._active(tok):
                self._terminate(self._proc)
                break
            now = time.time() - t0
            while i < len(env) and env[i][0] <= now:
                i += 1
            self.amp = env[i - 1][1] if i > 0 else 0.0
            time.sleep(0.03)
        self.amp = 0.0
        self._unlink(path)
        self._wait(tok, self._pause_ms(unit, timing_fn))

    @staticmethod
    def _unlink(path):
        try:
            os.unlink(path)
        except OSError:
            pass
