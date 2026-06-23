"""Optional sampled-loop voices.

Any audio file (``*.wav``/``*.ogg``/``*.flac``/``*.opus``) placed in
``assets/sounds/`` is registered as an extra Nature voice: the loop plays
continuously while its level is modulated by the breath (lung-volume) envelope,
so even a recorded ocean, rain or breathing loop *paces* the breath. Purely
additive -- the app works fully without any samples present.

WAV is read with scipy; other formats need the optional ``soundfile`` package.
"""
from __future__ import annotations

import glob
import os
from math import gcd

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

from . import voices
from .voices import GROUP_NATURE, GROUP_WORDS, VoiceConfig

try:
    import soundfile as _sf
except Exception:
    _sf = None

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DIR = os.path.join(_HERE, "assets", "sounds")
WORD_DIR = os.path.join(_HERE, "assets", "words")
_EXTS = ("wav", "ogg", "flac", "opus", "oga")


def _read(path: str):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext != "wav" or _sf is not None:
        if _sf is None:
            raise RuntimeError("soundfile not installed (needed for non-WAV)")
        data, sr = _sf.read(path, always_2d=False)
        return np.asarray(data, dtype=np.float64), int(sr)
    sr, data = wavfile.read(path)
    data = data.astype(np.float64)
    if np.issubdtype(np.dtype(data.dtype), np.integer):
        data /= float(np.iinfo(data.dtype).max)
    return data, int(sr)


def _load(path: str, target_sr: int) -> np.ndarray:
    data, sr = _read(path)
    peak = float(np.max(np.abs(data))) or 1.0
    data = data / peak * 0.9
    if sr != target_sr:
        g = gcd(int(sr), int(target_sr))
        data = resample_poly(data, target_sr // g, sr // g, axis=0)
    return data


def _nice_name(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem.replace("_", " ").replace("-", " ").strip().title()


def load_sample_voices(target_sr: int, directory: str = SAMPLE_DIR):
    """Scan *directory* for audio files and register each as a Nature voice."""
    added = []
    if not os.path.isdir(directory):
        return added
    paths = []
    for ext in _EXTS:
        paths += glob.glob(os.path.join(directory, f"*.{ext}"))
    for path in sorted(set(paths)):
        try:
            data = _load(path, target_sr)
        except Exception as exc:
            print(f"[breathsim] could not load sample {path}: {exc}")
            continue
        if len(data) < target_sr // 4:      # ignore tiny/empty files
            continue
        name = f"Sample: {_nice_name(path)}"
        voices.register(VoiceConfig(
            name, GROUP_NATURE, kind="sample", env="volume",
            floor=0.18, gain=0.9, data=data,
            description="Recorded loop, level paced by your breath."))
        added.append(name)
    return added


def load_word_voices(target_sr: int, directory: str = WORD_DIR):
    """Register each clip in *directory* as a one-shot **spoken-word** voice.

    These are short words/affirmations (e.g. rendered by the macOS concatenative
    synthesiser via ``tools/synth_words.py``). Unlike ambience samples they fire
    *once* on each exhale (``trigger="exhale"``) so the word lands with the
    breath, like a guided mantra. Purely additive; absent => feature off."""
    added = []
    if not os.path.isdir(directory):
        return added
    paths = []
    for ext in _EXTS:
        paths += glob.glob(os.path.join(directory, f"*.{ext}"))
    for path in sorted(set(paths)):
        try:
            data = _load(path, target_sr)
        except Exception as exc:
            print(f"[breathsim] could not load word {path}: {exc}")
            continue
        if len(data) < target_sr // 100:        # ignore empty files
            continue
        name = f"Word: {_nice_name(path)}"
        voices.register(VoiceConfig(
            name, GROUP_WORDS, kind="sample", trigger="exhale",
            env="volume", floor=1.0, gain=0.95, data=data,
            description="Spoken word, voiced once on each exhale."))
        added.append(name)
    return added
