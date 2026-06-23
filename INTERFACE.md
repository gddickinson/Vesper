# INTERFACE.md — Vesper navigation map

Read this before opening source. This is a **self-contained project**: the Qt
front-end lives in `vesper/`, and the audio / breath / voice / story logic core is
**vendored** at `breathsim/` (no sibling dependency). External pip deps only — see
`requirements.txt` (PySide6, numpy, moderngl, sounddevice, soundfile, faceview, and
optionally kokoro-onnx). `python selftest.py` runs headless checks; `python run.py`
launches the app.

## Big picture

```
run.py ── launches ──> vesper.window.MainWindow (QMainWindow)
                          │ owns (from the shared breathsim core)
   ┌──────────┬──────────┼─────────┬────────────┬───────────┬──────────────┐
BreathController AudioEngine SpeechCue+ SessionDirector FaceWidget ControlPanel
(timing, the     (sounddevice) Narrator  (morph/program  (faceView  (workspace-
 single clock)               (Kokoro/say) /sleep)        render)     driven panel)
                          + menus.py (full menu bar) + shortcuts.py (keys/Zen)
```

A ~40 fps `QTimer` reads the controller's `BreathState` each frame and drives:
either the **face** (breath → head nod + breathing zoom; narration `amp` → jaw
lip-sync) **or** the current **scene** (whichever is shown in the central
`QStackedWidget`), the **SessionDirector** (morph automation / guided programs /
sleep wind-down), transition chimes / spoken cues, the mindfulness bell, the
bedtime story, Sleep dimming, the panel's live read-outs, and practice logging.

The central area is a **`QStackedWidget(FaceWidget, VizWidget)`**; the user toggles
**face ↔ scene** (pinned panel buttons · View menu · `V`). Each mode has a default
scene; Sing/Chant can switch to the **pitch trainer** scene.

## Files

### Entry
- **run.py** — adds this dir to `sys.path`, calls `vesper.window.launch()`.

### `vesper/` (the Qt package)
- **__init__.py** — puts the sibling `breathsim` core on `sys.path` on import.
- **theme.py** — colours + a Qt `STYLESHEET` mirroring the breathsim night theme.
- **face.py** — `FaceWidget(QWidget)`: faceView's **Claude avatar**
  (`_claude_face()` = the `ict_xray_young` persona — the ICT head, glowing-cyan
  *xray* style, "young" identity, which the faceView characters file names as the
  default Claude face). Renders on a **background thread** via the GPU path
  (`face_gpu`, ~11 ms) with software fallback; the GUI `paintEvent` blits the
  latest frame each tick: it paints the chosen **animated background**
  (`face_bg`) then composites the (transparent-background) head over it with the
  **breathing zoom**. `set_state(vol, t, prog, mouth, nose, pucker, stretch, phase,
  smile, brow, eye_bias)` applies the *already-resolved* mouth + head-nod/zoom, plus
  **naturalistic life**: a gently wandering **gaze**, a tiny idle **head sway**,
  **randomized blinks** (varied gap, occasional double, heavier as the session winds
  down), and the eased **emotion** (smile/brow/eye-openness) — so the face is alive
  while reading, breathing, or idle. `_t` drives the eye starfield + bg tint hue.
  `set_background(name)` picks the backdrop; `set_active(on)`
  throttles the render thread when the scene view is showing. NumPy→`QImage`
  RGBA8888; speaking-vs-breathing precedence is decided in `window._face_inputs`.
- **face_bg.py** — animated backgrounds painted **behind** the face (the head now
  renders on a transparent background): `None`, `Stars` (starfield, matches the
  eyes), `Aurora` (drifting colour veils), `Nebula`, `Gradient` — all tinted by the
  breath-phase hue. `make(name)`/`names()`.
- **cat.py** — `CatFace`: the **2D cartoon-cat face** drawn with QPainter. Breathes,
  blinks, twitches its ears, wanders its pupils, and opens its mouth to talk — driven by
  the same per-frame state (`vol`/`mouth`/`eye_open`/`t`) as the 3D head, over the same
  animated background. `face.py` imports faceView in a try/except (`_faceview_ok`);
  it's used automatically when faceView is missing, and is **switchable at runtime**
  (`FaceWidget.set_use_cat` ← `window.set_face_cat` ← **View ▸ Cartoon cat face**,
  persisted) when faceView *is* present. The render worker idles while the cat shows.
- **face_gpu.py** — **moderngl GPU renderer for the ICT head** (~11 ms/frame vs
  ~65 ms software). Reuses ICT's mesh + pose pipeline (`apply_blendshapes`, incl.
  the persona identity weights) + per-material palette (`_material_palette`),
  rasterised with a lambert + **rim-glow** shader + per-vertex **emissive**. The
  eyeballs render an animated **starry sky** (procedural twinkling + drifting
  starfield in the fragment shader, driven by a `u_time` uniform = the face's
  `_t`). `_color_emit` marks the eyeball verts emissive when open and **blends
  them to the eyelid skin (emissive→0) as the lids close**; the eye-occlusion ring
  is coloured to the lid so there's **no shadow** around the eye. Renders to an
  **RGBA FBO with a transparent clear** (so `face_bg` shows behind the head);
  `EYE_SCALE` enlarges the eyeballs a little. Lazy standalone context on the worker
  thread; returns **RGBA** or `None` (→ software fallback).
- **scenes.py** — Qt `QPainter` visualization scenes (ambient set): `OrbScene`
  (glow + guide ring + cycle dot + progress arc + drifting **motes**, soft **exhale
  rings**, and a mint **coherence halo** near ~6 breaths/min), `NightScene` (stars +
  moon, a deeper gradient, drifting **clouds**, a rare **shooting star**),
  `RippleScene` (resonance rings with **tone-reactive** colour/spacing + a pulsing
  central glow), `WaveScene` (moonlit sea: stars, moon + **reflection shimmer**, foam
  crests, layered swells), a shared text overlay, and `make(name)`/`names()`.
- **scene_fx.py** — small, deliberately slow/dim **visual-effect helpers** shared by
  the scenes: `Motes`, `Clouds`, `ShootingStar` (stateful, seeded RNG) and a
  `starfield` drawer. Keeps the enrichment calming and `scenes.py` lean.
- **scene_pitch.py** — `PitchScene`: the pitch-trainer scene (note grid + target
  line + live-pitch trail + plain-words guidance), fed a `pitch` dict.
- **viz.py** — `VizWidget(QWidget)`: hosts a persistent scene, `set_scene(name)`,
  `update_state(ctx)` each frame; paints via `scene.draw(p, w, h, ctx)`. Also draws
  the corner **hourglass timer** (`set_hourglass(state)`) and forwards taps on it to
  `_hg_click_cb` (flip-to-reset). `FaceWidget` does the same.
- **hourglass.py** — the session **countdown timer** painter: `draw(p, rect, frac, t,
  running, spin)` renders a glass hourglass whose top bulb empties / bottom heap fills
  as `frac` (elapsed fraction) goes 0→1, with a falling sand stream; `spin` rotates it
  for the flip gesture. `corner_rect`/`draw_corner`/`hit` place it in a corner + hit-test.
- **pitch.py** — `_PitchMixin` (MainWindow): the mic `Tuner`, `show/hide_pitch_guide`,
  `pitch_context(t)` (target spec → dict), and the `set_reference` tone.
- **face_motion.py** — pure mouth/nostril routing from the breath: `SHAPE_AUS`,
  `mouth_shape`, `breath_routing`, `sample_inhale_open`, and **`emotion_for_text`**
  (line text → small smile/brow/eye-openness deltas: wonder / awe / curiosity /
  deep calm). Split out of window.py.
- **widgets.py** — reusable themed building blocks: `card(title)` (hairline
  section container), `LabeledSlider` (slider + live numeric read-out over a float
  range), `combo`/`combo_row`/`muted` helpers.
- **workspaces.py** — `WORKSPACES` spec: each mode → ordered list of card keys
  (resolved to `ControlPanel._card_<key>`). `get`/`names`.
- **sections.py** — `_SectionsMixin` (inherited by `ControlPanel`): the card
  builders — `_card_pattern`, `_card_pace` (breaths/min + resonance hint),
  `_card_voice` (inhale/exhale/body), `_card_naturalness`, `_card_cues`,
  `_card_choir`, `_card_phrase` (tradition→mantra), `_card_soundscape`
  (ambience+effect+levels), `_card_story`, `_card_winddown`, `_card_programs`
  (guided session), **`_card_pitch`** (Sing/Chant pitch trainer + reference tone),
  **`_card_bell`** (Meditate interval bell), **`_card_retention`** (Breathwork
  breath-hold timer). Each registers its live widgets in `self._w`.
- **controls.py** — `ControlPanel(_SectionsMixin, QWidget)`: a **workspace-driven**
  view. Pinned title + mode bar + **face/scene toggle** + master volume +
  transport; a `QScrollArea` body rebuilt per mode by **`build_workspace(name)`**.
  **`sync()`** pushes engine/controller state into the widgets; **`tick()`**
  refreshes live read-outs (guided-program stage, breath-hold timer).
  `reflect_mode`/`reflect_running`/`reflect_view`.
- **app_actions.py** — `_ActionsMixin` (inherited by `MainWindow`): the ported
  control actions the cards/menus call — `set_voice_a/b/out`, `set_persona`,
  `set_ambience`/`set_effect`/`set_slot_level`/`toggle_layer`, `set_morph_manual`,
  `set_naturalness`, `set_choir`, `set_phrase`, `set_cue_style`, `set_pace`
  (breaths/min → `pattern_for_bpm`), `start_session_mode` (automation or guided
  program), `set_winddown` (sleep), `set_muted`, `apply_stage`.
- **stage_apply.py** — `apply_stage(app, stage)`: applies one guided-program
  `Stage`'s settings dict (pattern/voice/phrase/persona/ambience/effect/cue/choir/
  volume), then `panel.sync()`. Driven by the `SessionDirector` at stage boundaries.
- **win_hourglass.py** — `_HourglassMixin` (inherited by `MainWindow`): the hourglass
  session-timer behaviour — `_tick_hourglass` (push frac to the visible view + ease
  the flip spin), `toggle_hourglass` (View-menu toggle, persisted) and
  `_flip_hourglass` (`controller.restart()` + spin). Painter is `hourglass.py`.
- **voice_editor.py** + **waveform.py** — the **Voice Editor** (`open_editor(win)`):
  a scrollable form over every `VoiceConfig` parameter with a live **wave + spectrum**
  preview (`WaveformView`), a Both/In/Out **breath-phase** selector, and Play
  (sounddevice) / Randomize / Save-as-custom-voice (`store.save_voice`). In Voice menu.
- **pattern_editor.py** — the **Pattern Editor** (`open_pattern_editor(win)`): sliders
  for the four phases + cycle/bpm read-out, saving custom breath patterns
  (`patterns.add_pattern` + `store.save_pattern`). In Pattern menu.
- **presets.py** — the **Presets Manager** (`open_presets(win)`): `capture(win,name)` /
  `apply(win,d)` round-trip the full audio+visual state; save/load/delete via
  `store.presets_list/save_preset/delete_preset`. In File menu.
- **app_io.py** — **Export Audio (WAV)** (`export_wav(win)` / `render_export`): offline
  render of primary+ambience+effects to a 16-bit WAV (no device needed). In File menu.
- **menus.py** — `build(win)`: the native **menu bar** (File / Modes / Sessions /
  Pattern / Voice / Sound / View / Help) — the global escape hatch for every
  control (all modes, automation + guided programs, every pattern, every voice +
  body + Morph A▸B, mute + background-sound toggles + chime + naturalness + Mixer,
  scene/face background, **Hourglass timer** toggle, Zen/Fullscreen, Stats/About).
  `win.rebuild_menu()` refreshes it.
- **shortcuts.py** — `bind(win)` global keys (Space play/pause · R reset ·
  F fullscreen · Z Zen · Esc exit) + `toggle_zen`/`toggle_fullscreen` (Zen hides
  the mode bar + panel + menus, leaving only the breathing face).
- **dialogs.py** — `open_stats` (practice history from `store`), `open_mixer`
  (per-slot levels), **`open_story_library`** (browse + search the stories DB via
  `story_db` — branch/lecture list, line view, full-text LIKE search) and
  `open_about`.
- **window.py** — `_breath_routing(phase, voice_a, voice_out)` + `_mouth_shape`
  decide the face's mouth/nostril motion per breath: **nose in-breath** (mouth
  closed, nostrils flare) and **mouth out-breath** shaped by the active voice
  (`_SHAPE_AUS`: pursed-lip / open "haa" / fricative sss / round OM / nasal
  ujjayi). `_face_inputs(state, running, amp)` then layers **talking over
  breathing**: while the storyteller voices a sentence the mouth lip-syncs to
  `narrator.amp` and the visible breath eases *down* (exhaling words); in the gap
  before the next sentence the mouth closes and the breath eases *up* (a breath in);
  with no recent speech the `_breath_routing` mouth applies.
  `MainWindow(_ActionsMixin, QMainWindow)`: builds the core (controller / engine /
  speech / narrator / **SessionDirector**), the 40 fps loop (also ticks the
  director + panel + practice logging), `save_screenshot`, `apply_mode` (audio
  preset + `panel.reflect_mode` → workspace rebuild; resets the director),
  transport, volume (mute-aware), `set_pattern` / `set_story` / `set_story_voice`,
  the bedtime story (`_start_story` + `_story_level` fade + `_story_timing`),
  **storyteller pacing** (`set_speech_speed` + `_apply_speech_pace`), Sleep
  dimming, **last-settings persistence** (`_restore_settings` on boot +
  `save_settings` on close, via `store`), status bar. `launch()`.

## Vendored core — `breathsim/` (in this project)
The whole audio/logic/story core lives here, gui-free (the Tk GUI is not vendored):
`controller`, `engine`, `speech`, `narration` (Kokoro/say + lip-sync `amp`),
`stories` + the **lecture library** (`lectures` + `lectures_*.py`, 50+ across
8 branches; Cosmos now incl. Comets · Nebulae · Saturn's Rings) + **`shuffle`** (the
**Cognitive Shuffle** sleep-onset aid: a stream of
random neutral nouns, surfaced as a Sleep storyteller via `stories.extra_names()`),
**`sound_cues`** (text→ambience), **`story_db`** (SQLite record of every
story; `build`/`connect`/`search`/`lectures_in`/`lines_of`/`stats`; CLI
`python -m breathsim.story_db`), `kokoro_tts`, `voices`, `patterns`, `modes`,
`personas`, `choir`, `session` (SessionDirector), `programs`, `phrases`, `store`,
`tracks` (+ `rhythm`, **`textures`** — the `kind="texture"` event generators for the
Campfire / Singing Bowl / Wind Chimes / Night Crickets / **Purr** ambiences), and
**`voices_cat`** — the **Cat** voice group (`GROUP_CAT`: Cat Breath, Cat Sigh, Meow,
Cat Purr). The 2D fallback face lives in `vesper/cat.py`.

## Other project files
- **selftest.py** — headless voice + lecture checks against the vendored core.
- **requirements.txt** / **README.md** — external pip deps + run instructions.
- **data/stories.db** — generated SQLite story record (rebuilt on startup).
- **UPDATES.md** — the autonomous-improvement loop's backlog.

## Conventions
- All files < 500 lines; one concept per file. Core logic lives in the vendored
  `breathsim/`; `vesper/` is view/wiring. Face frames → `QImage` RGBA8888.

## GPU note
The **GPU-ICT renderer** (`face_gpu.py`) is built and is the default path
(~11 ms/frame, full 40 fps), with a software fallback. It reproduces the Claude
xray look approximately via a rim-glow shader; the eye-socket emissive glow of the
software xray isn't reproduced yet (a shader refinement: per-material emissive).

## Modes & workspaces
The mode bar is the primary navigation. Each mode supplies an **audio preset**
(`modes.py`) applied in a click, plus a **workspace** (`workspaces.py`) that
rebuilds the side panel into a distinct toolset: Meditate = pace/resonance +
naturalness; Breathwork = pattern + guided programs; Chant = mantra + choir; Sing =
voice + choir + naturalness; Relax = soundscape; Sleep = bedtime story + wind-down.

## Done — Tk feature parity
Workspaces / per-mode cards, full menu bar, keyboard shortcuts + Zen, the session
director (morph automation + **guided programs** + sleep wind-down), voice / body /
ambience / effect / morph / naturalness / choir / mantra / cue controls,
background-sound toggles + mute + Mixer, practice **Stats** + logging,
last-settings persistence, the **Qt scenes** (orb / night / ripple / wave) +
**face/scene toggle** + scene picker, the on-screen **pitch trainer** (Sing/Chant,
mic + reference tone), the **mindfulness bell** (Meditate) and breath-hold
**retention** timer (Breathwork), **animated backgrounds behind the face**
(Stars/Aurora/Nebula/Gradient) and the **no-shadow eyes** fix — all via the
shared core.

## Roadmap (remaining)
The **Voice** and **Pattern** editors + **Presets** manager (dialogs), a custom
breath-pattern designer, chant/song phrase sequencing UI; GPU shader refinements
(eye/teeth emissive to match the xray exactly).
