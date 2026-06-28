"""Optional Kokoro neural TTS -- far more natural than macOS ``say``.

A local ONNX model (cross-platform) with ~50 voices. Everything here degrades
gracefully: if ``kokoro-onnx`` isn't installed or the model files are missing,
``ready()`` is False and the narrator falls back to ``say``.

**Highest quality by design.** Of the three Kokoro v1.0 ONNX builds --
``kokoro-v1.0.onnx`` (full **fp32**, ~310 MB), ``kokoro-v1.0.fp16.onnx`` (~169 MB)
and ``kokoro-v1.0.int8.onnx`` (~88 MB) -- we deliberately use the **fp32** model,
the maximum-fidelity reference build (fp16/int8 trade audio quality for size).
This matches the iOS app's fp32 Kokoro. (For an even higher-fidelity offline
voice, the optional XTTS-v2 engine is available separately -- see docs/XTTS.md.)

Install:  ``pip install kokoro-onnx soundfile``
Download: ``python -m breathsim.kokoro_tts --download``  (or call ``download()``)
"""
from __future__ import annotations

import importlib.util
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path

# Kokoro phonemises text via `phonemizer`/espeak, which logs benign
# "words count mismatch on N% of the lines" warnings on short or punctuation-only
# lines. The phonemes (and so the speech) are fine, so quiet that noise.
logging.getLogger("phonemizer").setLevel(logging.ERROR)

_BASE = ("https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
         "model-files-v1.0/")
# fp32 full-precision model = the highest-quality Kokoro build (NOT the .fp16 /
# .int8 variants, which are smaller but lower-fidelity). Keep this the fp32 file.
MODEL_URL = _BASE + "kokoro-v1.0.onnx"          # ~310 MB, fp32 (max quality)
VOICES_URL = _BASE + "voices-v1.0.bin"          # ~27 MB, full voice pack

# Calm, clearly-vocalised voices for sleep narration, in preference order. A
# British female leads (the app default); these top voices are the highest grade
# Kokoro ships, all rated "A" for long-form narration.
RELAXING = ["bf_emma", "bf_isabella", "bf_alice", "bf_lily", "af_heart",
            "af_sarah", "af_nicole", "af_sky", "bm_george", "bm_lewis",
            "am_michael", "am_adam"]

# The most realistic / recommended voices (shown starred in the picker).
RECOMMENDED = ("bf_emma", "bf_isabella", "af_heart", "af_sarah", "bm_george")

_engine = None


def _dir() -> Path:
    d = (Path(os.environ.get("BREATHSIM_HOME") or os.path.expanduser("~/.breathsim"))
         / "tts")
    d.mkdir(parents=True, exist_ok=True)
    return d


def model_path() -> Path:
    return _dir() / "kokoro-v1.0.onnx"


def voices_path() -> Path:
    return _dir() / "voices-v1.0.bin"


def deps_present() -> bool:
    return bool(importlib.util.find_spec("kokoro_onnx")
                and importlib.util.find_spec("soundfile"))


def assets_present() -> bool:
    return model_path().exists() and voices_path().exists()


def ready() -> bool:
    return deps_present() and assets_present()


def download() -> tuple[bool, str]:
    """Fetch model (~310 MB) + voices (~27 MB). Returns (ok, message)."""
    try:
        if not model_path().exists():
            urllib.request.urlretrieve(MODEL_URL, model_path())
        if not voices_path().exists():
            urllib.request.urlretrieve(VOICES_URL, voices_path())
    except (urllib.error.URLError, OSError) as exc:
        return False, str(exc)
    return True, f"Kokoro assets ready in {_dir()}"


def _load():
    global _engine
    if _engine is None and ready():
        from kokoro_onnx import Kokoro
        _engine = Kokoro(str(model_path()), str(voices_path()))
    return _engine


def voice_names():
    """Curated relaxing voices that are actually present, else all available."""
    eng = _load()
    if eng is None:
        return []
    try:
        have = set(eng.get_voices())
    except Exception:
        return []
    ranked = [v for v in RELAXING if v in have]
    return ranked + sorted(v for v in have if v not in ranked)


def best_voice():
    vs = voice_names()
    return vs[0] if vs else None


def synth(text, voice=None, speed=1.0):
    """(samples float32 mono, sample_rate) for *text*, or None on failure."""
    eng = _load()
    if eng is None:
        return None
    try:
        samples, sr = eng.create(text, voice=voice or best_voice(),
                                 speed=float(speed), lang="en-us")
        return samples, sr
    except Exception:
        return None


def _main():
    import argparse
    p = argparse.ArgumentParser(description="Kokoro TTS assets")
    p.add_argument("--download", action="store_true")
    args = p.parse_args()
    if args.download:
        ok, msg = download()
        print(("ok: " if ok else "fail: ") + msg)
        return 0 if ok else 1
    print(f"deps: {deps_present()}  assets: {assets_present()}  dir: {_dir()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
