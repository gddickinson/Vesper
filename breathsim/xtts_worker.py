"""Persistent XTTS-v2 synthesis worker -- run by a *separate* Python interpreter
that has `coqui-tts` installed (see `xtts_tts.py`). It loads the heavy model once,
then serves one synth request per stdin line and replies one JSON line on stdout:

    <- {"text": "...", "voice": "Daisy Studious", "speed": 0.9}
    -> {"wav": "/tmp/....wav", "sr": 24000}        (or {"error": "..."})

The first line it ever emits is a readiness handshake with the device + the real
built-in speaker list: {"ready": true, "device": "mps", "speakers": [...]}.

stdout carries ONLY these JSON lines; the model's own chatty logging is redirected
to stderr so the protocol channel stays clean. Kept dependency-light + offline
(COQUI_TOS_AGREED + a cached model). This file imports nothing from breathsim.
"""
import json
import os
import sys
import tempfile

os.environ.setdefault("COQUI_TOS_AGREED", "1")            # accept CPML (non-commercial)
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")  # CPU-fallback unsupported ops

# A clean response channel: keep the real stdout, send everything else to stderr.
_out = os.fdopen(os.dup(1), "w")
os.dup2(2, 1)


def _respond(obj):
    _out.write(json.dumps(obj) + "\n")
    _out.flush()


def _load(device):
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    tts.to(device)
    return tts


def main():
    import numpy as np
    import soundfile as sf

    want = os.environ.get("VESPER_XTTS_DEVICE", "mps")
    tts = device = None
    for dev in (want, "cpu"):                              # fall back to CPU on failure
        try:
            tts = _load(dev)
            device = dev
            break
        except Exception as e:  # noqa: BLE001
            print(f"load on {dev} failed: {e}", file=sys.stderr)
    if tts is None:
        _respond({"ready": False, "error": "model load failed"})
        return 1

    sm = tts.synthesizer.tts_model.speaker_manager
    speakers = list(getattr(sm, "name_to_id", None) or getattr(sm, "speakers", []))
    default = speakers[0] if speakers else None
    _respond({"ready": True, "device": device, "speakers": speakers})

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if req.get("cmd") == "quit":
            break
        try:
            text = (req.get("text") or "").strip() or "."
            voice = req.get("voice") or default
            speed = float(req.get("speed", 1.0))
            try:
                wav = tts.tts(text=text, speaker=voice, language="en", speed=speed)
            except TypeError:                              # older API: no speed kwarg
                wav = tts.tts(text=text, speaker=voice, language="en")
            wav = np.asarray(wav, dtype="float32").reshape(-1)
            fd, path = tempfile.mkstemp(suffix=".wav", prefix="vesper_xtts_")
            os.close(fd)
            sf.write(path, wav, 24000)
            _respond({"wav": path, "sr": 24000})
        except Exception as e:  # noqa: BLE001
            _respond({"error": str(e)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
