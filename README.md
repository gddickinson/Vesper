# Breathing Sim — PySide6

A meditation / breathing pacer whose centrepiece is a 3D talking-head **Claude
avatar** that breathes, lip-syncs and emotes a procedural **bedtime storyteller** —
including a library of 50+ soothing **sleep-lectures** across many branches.

This is a **self-contained project**: the audio / breath / voice / story logic core
is vendored at [`breathsim/`](breathsim/) (no dependency on any sibling folder), and
the PySide6 front-end lives in [`bsqt/`](bsqt/).

## Run

```bash
pip install -r requirements.txt      # + see the faceView note in requirements.txt
python run.py                        # launch the app
python selftest.py                   # headless checks (no display/audio needed)
```

## Layout

- `bsqt/` — the Qt app (window, control panel, the 3D face, scenes, menus…).
  See [`INTERFACE.md`](INTERFACE.md) for the module map.
- `breathsim/` — the **vendored core**: engine, controller, voices, patterns,
  modes, narration, `stories.py` + the whole **lecture library** (`lectures*.py`),
  `sound_cues.py` (text-matched ambience) and `story_db.py`.
- `data/stories.db` — a **SQLite record of every story** (rebuilt on startup;
  `python -m breathsim.story_db` rebuilds it). Browse it in the app via
  **Help ▸ Story Library**, or open it with any SQLite tool.
- `UPDATES.md` — the autonomous-improvement backlog the self-paced loop works through.

## Dependencies

Pure pip packages (see `requirements.txt`): PySide6, numpy, moderngl, sounddevice,
soundfile, **faceview** (the 3D renderer — install editable from the faceView
project), and optionally **kokoro-onnx** for neural narration (else macOS `say`).
Everything degrades gracefully: no GPU → software face; no audio device → visual
only; no Kokoro → `say`; no faceView → (face render unavailable).
