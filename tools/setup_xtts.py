#!/usr/bin/env python3
"""One-command opt-in installer for the high-quality **XTTS-v2** narration engine.

XTTS-v2 is NOT bundled with Vesper: it is heavy (PyTorch + a ~1.8 GB model) and its
model is under the **Coqui Public Model License (CPML) -- non-commercial use only**.
This script lets a user add it *themselves*, accepting that licence, without touching
Vesper's own Python environment: it builds a dedicated venv, downloads the model, and
writes the config Vesper reads (`~/.vesper-xtts/config.json`). The app then offers the
XTTS voices and falls back to Kokoro / `say` if this was never run.

Usage:
    python tools/setup_xtts.py --accept-license          # install
    python tools/setup_xtts.py --status                  # show what's configured
    python tools/setup_xtts.py --accept-license --force  # rebuild the venv

Requirements: Python 3.9-3.12, ~5 GB disk, and system FFmpeg (`brew install ffmpeg`
on macOS) for torchcodec audio IO.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HOME = os.path.expanduser("~/.vesper-xtts")
VENV = os.path.join(HOME, "venv")
TTS_HOME = os.path.join(HOME, "tts_home")
CONFIG = os.path.join(HOME, "config.json")
PY = os.path.join(VENV, "bin", "python")

# coqui-tts pulls neither torch nor torchaudio/torchcodec, and its current release
# breaks on transformers 5.x -- so we pin the last 4.x line explicitly.
PIP_PKGS = ["coqui-tts", "soundfile", "torch", "torchaudio", "torchcodec",
            "transformers>=4.57,<5"]

LICENSE = """\
XTTS-v2 model licence: Coqui Public Model License (CPML) -- NON-COMMERCIAL use only.
By continuing you accept the CPML for the downloaded model. See
https://coqui.ai/cpml . Re-run with --accept-license to proceed."""


def _status():
    print(f"config:  {CONFIG}  {'present' if os.path.exists(CONFIG) else 'absent'}")
    print(f"venv:    {PY}  {'present' if os.path.exists(PY) else 'absent'}")
    print(f"model:   {TTS_HOME}  {'present' if os.path.isdir(TTS_HOME) else 'absent'}")
    if os.path.exists(CONFIG):
        cfg = json.load(open(CONFIG))
        print(f"device:  {cfg.get('device')}   speakers: {len(cfg.get('speakers', []))}")


def _have_ffmpeg():
    from shutil import which
    return bool(which("ffmpeg"))


def main():
    ap = argparse.ArgumentParser(description="Install the optional XTTS-v2 voice engine.")
    ap.add_argument("--accept-license", action="store_true",
                    help="accept the Coqui CPML (non-commercial) and install")
    ap.add_argument("--status", action="store_true", help="show current install state")
    ap.add_argument("--force", action="store_true", help="rebuild the venv from scratch")
    ap.add_argument("--device", default="mps", help="mps (Apple GPU) | cpu | cuda")
    args = ap.parse_args()

    if args.status:
        _status()
        return 0
    if not args.accept_license:
        print(LICENSE)
        return 2
    if not _have_ffmpeg():
        print("WARNING: FFmpeg not found on PATH (torchcodec needs it). "
              "On macOS: brew install ffmpeg")

    os.makedirs(HOME, exist_ok=True)
    if args.force and os.path.isdir(VENV):
        import shutil
        shutil.rmtree(VENV)
    if not os.path.exists(PY):
        print(f"Creating venv at {VENV} ...")
        subprocess.check_call([sys.executable, "-m", "venv", VENV])
        subprocess.check_call([PY, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    print("Installing XTTS dependencies (this downloads PyTorch + coqui-tts) ...")
    subprocess.check_call([PY, "-m", "pip", "install", "-q", *PIP_PKGS])

    print("Downloading the model + reading the speaker list (~1.8 GB, one time) ...")
    env = dict(os.environ, COQUI_TOS_AGREED="1", TTS_HOME=TTS_HOME,
               PYTORCH_ENABLE_MPS_FALLBACK="1")
    dump = (
        "import json,os\n"
        "from TTS.api import TTS\n"
        "t=TTS('tts_models/multilingual/multi-dataset/xtts_v2')\n"
        "sm=t.synthesizer.tts_model.speaker_manager\n"
        "names=list(getattr(sm,'name_to_id',None) or getattr(sm,'speakers',[]))\n"
        f"cfg=dict(python={PY!r},tts_home={TTS_HOME!r},device={args.device!r},speakers=names)\n"
        f"open({CONFIG!r},'w').write(json.dumps(cfg,indent=1))\n"
        "print('speakers',len(names))\n")
    subprocess.check_call([PY, "-c", dump], env=env)
    print(f"\nDone. Wrote {CONFIG}. Launch Vesper and pick an 'XTTS' narration voice "
          "in Sleep.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
