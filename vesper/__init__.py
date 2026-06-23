"""Vesper -- a breath-paced meditation & sleep companion (self-contained).

The audio/logic core — engine, controller, voices, patterns, modes, narration,
stories + the whole **lecture library**, sound cues, Kokoro TTS — is **vendored**
into this project at ``vesper/breathsim`` (no dependency on any sibling
folder). The PySide6 front-end (this ``vesper`` package) adds the 3D faceView head
that breathes and lip-syncs the bedtime stories.

External (pip) dependencies only: PySide6, numpy, moderngl, sounddevice,
soundfile, faceview (the 3D renderer) and optionally kokoro-onnx — see
``requirements.txt``. Importing this package puts the project root on ``sys.path``
so the vendored ``breathsim`` core resolves locally.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
