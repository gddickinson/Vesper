"""Spoken phase cues via the macOS ``say`` command (optional).

Speaks guidance at each breath phase in a chosen accent. Prefers the more
realistic *Premium/Enhanced* macOS voices when installed, and offers phrase
styles from terse ("In"/"Out") to fully guided ("Breathe in slowly...").
If ``say`` is unavailable the feature silently disables itself.
"""
from __future__ import annotations

import re
import shutil
import subprocess

_LOCALE = re.compile(r"\b[a-z]{2}_[A-Z]{2}\b")

# Curated accents: (display, base voice name, region). We use whichever
# matching voice is installed, preferring Premium/Enhanced variants.
_ACCENTS = [
    ("US", "Samantha"), ("US", "Ava"), ("US", "Alex"),
    ("UK", "Daniel"), ("UK", "Kate"), ("UK", "Serena"), ("UK", "Oliver"),
    ("Australian", "Karen"), ("Australian", "Lee"),
    ("Irish", "Moira"), ("Scottish", "Fiona"),
    ("South African", "Tessa"), ("Indian", "Rishi"), ("Indian", "Veena"),
]

STYLES = ["Off", "Minimal", "Standard", "Guided"]

_PHRASES = {
    "Minimal": {
        "inhale": ["In"], "hold_full": ["Hold"],
        "exhale": ["Out"], "hold_empty": [""],
    },
    "Standard": {
        "inhale": ["Breathe in"], "hold_full": ["Hold"],
        "exhale": ["Breathe out"], "hold_empty": ["Rest"],
    },
    "Guided": {
        "inhale": ["Breathe in slowly", "Gently breathe in",
                   "Inhale, filling your lungs", "Breathe in through your nose"],
        "hold_full": ["Hold", "Gently hold", "Hold, soft and still"],
        "exhale": ["Slowly breathe out", "Release the breath",
                   "Let everything go", "Exhale, and soften"],
        "hold_empty": ["Rest", "Relax", "", "Stay soft"],
    },
}


class SpeechCue:
    def __init__(self):
        self.binary = shutil.which("say")
        self.style = "Off"
        self.voice_id: str | None = None
        self.rate = 165
        self._proc: subprocess.Popen | None = None
        self._installed = self._detect()           # full name -> locale
        self._idx: dict[str, int] = {}

    def _detect(self):
        if not self.binary:
            return {}
        try:
            out = subprocess.run([self.binary, "-v", "?"], capture_output=True,
                                 text=True, timeout=5).stdout
        except Exception:
            return {}
        found = {}
        for line in out.splitlines():
            m = _LOCALE.search(line)
            if not m:
                continue
            name = line[:m.start()].strip()
            if name:
                found[name] = m.group(0)
        return found

    @property
    def available(self) -> bool:
        return bool(self.binary)

    def _resolve(self, base):
        """Best installed voice for *base* (prefer Premium/Enhanced)."""
        matches = [n for n in self._installed
                   if n == base or n.startswith(base + " ")]
        if not matches:
            return None
        for tag in ("(Premium)", "(Enhanced)"):
            for n in matches:
                if tag in n:
                    return n
        return matches[0]

    def accent_voices(self):
        """List of (display, voice_id) for installed accents + premium voices."""
        out, seen = [], set()
        for region, base in _ACCENTS:
            voice = self._resolve(base) if self._installed else base
            if voice and voice not in seen:
                seen.add(voice)
                label = voice.split(" (")[0]
                tag = " *" if "(" in voice else ""
                out.append((f"{label} ({region}){tag}", voice))
        for name in sorted(self._installed):
            if ("(Premium)" in name or "(Enhanced)" in name) and name not in seen:
                seen.add(name)
                out.append((f"{name}", name))
        return out or [(f"{b} ({r})", b) for r, b in _ACCENTS]

    def set_voice(self, voice_id):
        self.voice_id = voice_id

    def set_style(self, style):
        self.style = style if style in STYLES else "Off"

    @property
    def enabled(self):
        return self.style != "Off"

    def _next_phrase(self, phase):
        bank = _PHRASES.get(self.style, {}).get(phase, [])
        if not bank:
            return ""
        i = self._idx.get(phase, 0) % len(bank)
        self._idx[phase] = i + 1
        return bank[i]

    def _run(self, text, rate=None):
        if not (self.available and self.voice_id and text):
            return
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        try:
            self._proc = subprocess.Popen(
                [self.binary, "-v", self.voice_id, "-r", str(rate or self.rate),
                 text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _speak(self, text):
        if self.enabled:
            self._run(text)

    def announce(self, text):
        """Speak a one-shot guidance line (a session-stage instruction), even
        when per-phase cues are off."""
        self._run(text, rate=160)

    def cue(self, phase):
        self._speak(self._next_phrase(phase))

    def preview(self):
        prev, self.style = self.style, ("Guided" if self.style == "Off"
                                        else self.style)
        self._speak("Breathe in slowly, and gently breathe out.")
        self.style = prev

    def shutdown(self):
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
