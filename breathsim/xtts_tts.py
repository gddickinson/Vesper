"""Optional **XTTS-v2** narration engine -- the highest-fidelity offline voice we
can drive on this machine (voice-cloning + emotion, real-time on Apple Silicon /
Metal). It is heavy (torch + a ~1.8 GB model) and **non-commercial** (Coqui Public
Model License), so it is never bundled and never the default: it runs only when a
separate Python interpreter with `coqui-tts` is configured, and the app degrades
straight back to Kokoro / `say` when it is not.

To keep that heavy stack out of the app's own environment, synthesis runs in a
**persistent subprocess** (``xtts_worker.py``) launched with the configured
interpreter -- the model loads once and then serves one sentence per request. This
module is import-safe and pulls in nothing heavy at import time (no torch).

Configure via ``~/.vesper-xtts/config.json``::

    {"python": "/path/to/venv/bin/python", "tts_home": "/path/to/model/cache",
     "device": "mps", "speakers": ["Daisy Studious", ...]}

or the env vars ``VESPER_XTTS_PYTHON`` / ``VESPER_XTTS_HOME`` / ``VESPER_XTTS_DEVICE``.
Mirrors the :mod:`breathsim.kokoro_tts` interface (``ready`` / ``voice_names`` /
``best_voice`` / ``synth``) so :mod:`breathsim.narration` can treat it as one engine.
"""
from __future__ import annotations

import atexit
import json
import os
import subprocess
import threading

from . import xtts_voices

CONFIG = os.path.expanduser("~/.vesper-xtts/config.json")
PREFIX = "xtts:"                                   # voice-id namespace in the picker

# Curated, female-first ordering for the picker; any other model speakers follow.
_PREFERRED = tuple(xtts_voices.curated())
RECOMMENDED = tuple(PREFIX + n for n in xtts_voices.curated()
                    if xtts_voices.is_recommended(n))

_lock = threading.Lock()
_proc = None
_info = None                                       # {"device":.., "speakers":[..]}


def _cfg() -> dict:
    try:
        with open(CONFIG) as f:
            return json.load(f)
    except Exception:
        return {}


def _python():
    return os.environ.get("VESPER_XTTS_PYTHON") or _cfg().get("python")


def ready() -> bool:
    """True if a usable XTTS interpreter is configured (cheap -- no subprocess)."""
    py = _python()
    return bool(py and os.path.exists(py))


def device() -> str | None:
    return _info.get("device") if _info else None


def _speaker_list():
    if _info and _info.get("speakers"):
        return _info["speakers"]
    return _cfg().get("speakers") or ["Daisy Studious"]


def _ordered(names):
    names = list(names)
    pref = [n for n in _PREFERRED if n in names]
    rest = [n for n in names if n not in pref]
    return pref + rest


def voice_names():
    """Picker ids for the built-in studio speakers, namespaced with ``xtts:``."""
    return [PREFIX + n for n in _ordered(_speaker_list())]


def best_voice():
    names = _ordered(_speaker_list())
    return PREFIX + (names[0] if names else "Daisy Studious")


# --- worker subprocess -----------------------------------------------------

def _log_path():
    return os.path.join(os.path.dirname(CONFIG), "worker.log")


def _ensure_worker():
    """Start (or reuse) the persistent synth worker. Blocks on first start while
    the model loads (~20-60 s); returns False if XTTS is unavailable."""
    global _proc, _info
    if _proc is not None and _proc.poll() is None:
        return True
    py = _python()
    if not (py and os.path.exists(py)):
        return False
    worker = os.path.join(os.path.dirname(__file__), "xtts_worker.py")
    env = dict(os.environ)
    cfg = _cfg()
    home = os.environ.get("VESPER_XTTS_HOME") or cfg.get("tts_home")
    if home:
        env["TTS_HOME"] = home
    dev = os.environ.get("VESPER_XTTS_DEVICE") or cfg.get("device")
    if dev:
        env["VESPER_XTTS_DEVICE"] = dev
    env.setdefault("COQUI_TOS_AGREED", "1")
    try:
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        errlog = open(_log_path(), "a")
        _proc = subprocess.Popen(
            [py, worker], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=errlog, text=True, bufsize=1, env=env)
    except Exception:
        _proc = None
        return False
    line = _proc.stdout.readline()                 # readiness handshake (model loaded)
    try:
        info = json.loads(line)
    except Exception:
        info = {}
    if not info.get("ready"):
        _shutdown()
        return False
    _info = info
    return True


def synth(text, voice=None, speed=1.0):
    """``(samples float32 mono, sample_rate)`` for *text*, or ``None`` on failure
    (so the narrator falls back gracefully). Serialised: one request at a time."""
    name = voice[len(PREFIX):] if voice and str(voice).startswith(PREFIX) else voice
    with _lock:
        if not _ensure_worker():
            return None
        try:
            req = json.dumps({"text": str(text), "voice": name, "speed": speed})
            _proc.stdin.write(req + "\n")
            _proc.stdin.flush()
            line = _proc.stdout.readline()
            if not line:
                _shutdown()
                return None
            resp = json.loads(line)
        except Exception:
            _shutdown()
            return None
    path = resp.get("wav")
    if not path:
        return None
    try:
        import soundfile as sf
        data, sr = sf.read(path, dtype="float32")
        return data, sr
    except Exception:
        return None
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _shutdown():
    global _proc
    p, _proc = _proc, None
    if p is None:
        return
    try:
        if p.poll() is None:
            try:
                p.stdin.write('{"cmd": "quit"}\n')
                p.stdin.flush()
            except Exception:
                pass
            p.terminate()
    except Exception:
        pass


atexit.register(_shutdown)
