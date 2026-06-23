# CLAUDE.md — Breathing Sim (PySide6 rebuild)

Project guidance for Claude when working in this repository.

@INTERFACE.md

## What this is
The **PySide6/Qt rebuild** of Breathing Sim, with a **3D talking-head face** as
the centrepiece (faceView's renderer): a face that **breathes** with the breath
and **lip-syncs** the bedtime story. **Always read `INTERFACE.md` first.**

## Self-contained project (vendored core)
- This is an **independent project**. The audio/logic/story **core is vendored** at
  `breathsim/` (engine, controller, voices, patterns, modes, naturalness, dsp,
  formants, tracks, vocal, narration, `stories` + the **lecture library**,
  `sound_cues`, `story_db`, Kokoro TTS, personas, choir, speech). It is
  toolkit-agnostic (numpy/sounddevice); `bsqt/__init__.py` puts the project root on
  `sys.path` so `import breathsim` resolves the **local** copy. Do NOT reintroduce a
  dependency on `../breathing_sim` (now a legacy Tk fork). Edit the core HERE.
- External pip deps only (see `requirements.txt`): PySide6, numpy, moderngl,
  sounddevice, soundfile, **faceview** (the 3D renderer — `pip install -e` the
  faceView project; ~1.2 GB, so not vendored), optional kokoro-onnx.
  `faceview.vision.sim_face.render_face(FaceParams, size) -> BGR ndarray`.
- `python selftest.py` = headless voice + lecture checks. Stories live in
  `breathsim/lectures_*.py` + `breathsim/stories.py`, and are recorded to
  `data/stories.db` (`python -m breathsim.story_db`; browse via Help ▸ Story Library).

## Architecture rules
- Keep every file under 500 lines; one concept per file.
- This package (`bsqt/`) is **only the Qt front-end** + face integration. Any
  audio/breath/voice logic belongs in the shared `breathsim` core.
- The `BreathController` remains the single timing authority; the Qt loop and the
  audio engine both read breath state from it.
- Convert NumPy frames to `QImage` as **RGBA8888** (4*w stride) to avoid
  scanline skew.

## Dependencies
- `PySide6`, `numpy`, `sounddevice`, `scipy` (core); `faceview` (face);
  optional `kokoro-onnx soundfile` for neural narration (`moderngl` for GPU face
  modes). PySide6 + moderngl are already in the env.

## Running / verifying
- `python run.py` — launch the app.
- Headless check: `QT_QPA_PLATFORM=offscreen` + construct `MainWindow`, tick,
  `widget.grab().save(...)` to a PNG (see `SESSION_LOG.md`).

## Status
Phase 1: face (breathing + lip-sync), mode bar, pattern, transport, volume,
render-mode picker, Sleep bedtime story (Kokoro). Roadmap to Tk parity in
`SESSION_LOG.md`.
