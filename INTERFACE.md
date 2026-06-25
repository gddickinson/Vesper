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
sleep wind-down / **ease-to-resonance "settle in"** pacing), transition chimes /
spoken cues, the mindfulness bell, the
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
  eyes), `Aurora` (drifting colour veils), `Nebula`, `Gradient`, `Underwater`,
  `Embers`, and the story themes **`Rain`** (soft streaks), **`Forest`** (green hush +
  motes) and **`City`** (twinkling windows) — all tinted by the breath-phase hue.
  `make(name)`/`names()`. The FaceWidget **crossfades** between backdrops
  (`set_background(name, fade)`) so story-driven changes never jump.
- **xtts_tts.py** + **xtts_worker.py** + **xtts_voices.py** — optional **XTTS-v2**
  narration engine (highest-fidelity offline voice; opt-in, non-commercial CPML, never
  bundled). The heavy torch+model stack runs in a *separate* interpreter via a
  persistent worker subprocess (`xtts_worker.py`), so it stays out of the app env;
  `xtts_tts` mirrors the `kokoro_tts` interface and reads `~/.vesper-xtts/config.json`.
  **`xtts_voices.py`** holds curated per-speaker metadata (gender + timbre + a quality
  star, derived by *measuring* each rendered voice). `narration.voice_groups()` feeds
  the **grouped** Sleep picker (Recommended · XTTS by gender · Kokoro by accent), and
  the storyteller routes per chosen voice (`xtts:` ids); absent → Kokoro/`say`.
  Characters carry an `xtts` voice (`char_voice`) used when installed, falling back to
  their Kokoro/say hints. Users add the engine themselves via `tools/setup_xtts.py`
  (Sound ▸ "High-quality voices (XTTS)…"). Setup + licence: `docs/XTTS.md`.
- **llm.py** + **llm_keys.py** — optional **LLM provider** (wired into the UI via
  `vesper/llm_settings.py`). Auto-selects **Claude** when an Anthropic key resolves
  (`llm_keys.resolve`: env → OS keychain → chmod-600 `~/.breathsim/llm.json` → session-only)
  else **Ollama** (local, **opt-in** via `enable_ollama` — no network unless asked) else a
  **null** provider (`available()` False). API: `available`/`backend_name`/`status`/`complete`/
  `chat` (Claude over urllib, no SDK dep). `llm_keys` also exposes `set_session`/`set_file`/
  `set_keychain`/`clear`/`source`/`keychain_available`. **Key-safe:** the key is fetched lazily
  and never stored on a provider, never logged (errors `_sanitize`d), never committed/shipped;
  `mask()` shows only the last 4. No network at import. Offline safety test: `tools/test_llm.py`.
- **llm_story.py** — optional **AI story generation** built on the provider. `generate(topic)`
  asks the model for a sleep story in the lecture **7x12** schema, treats the reply as
  *untrusted* (`validate` + a re-prompt **repair** loop), and registers valid stories into
  `lectures.LECTURES` under the **"AI Stories"** category with an **"AI: "** prefix (labelled,
  framed atmospheric -- no accuracy claims), so they narrate like any lecture; `save`/`saved`/
  `delete`/`register_saved` persist them to `store` (`ai_stories`, loaded from
  `store.register_all`). Gated on `llm.available()`; absent with no LLM. Offline test:
  `tools/test_llm_story.py`.
- **llm_content.py** — optional **structured-content** generation (no code execution): a plain
  request → a validated `BreathPattern` (`pattern`), a safe whitelisted `VoiceConfig` that is
  constructed **and rendered** finite/non-clipping (`voice`), or a simple letters-only `mantra`.
  Model JSON is untrusted → coerced/clamped/range-checked → constructed → repaired → else
  rejected; saved via `store.save_pattern`/`save_voice`/`save_ai_mantra` with an **"AI: "**
  prefix. Gated on `llm.available()`. Offline test: `tools/test_llm_content.py`.
- **llm_assist.py** — optional **quiet helper**: plain language → a **whitelist** of 9 bounded
  app actions (`set_mode`/`set_pattern`/`set_ambience`/`set_voice`/`play`/`pause`/`set_volume`/
  `start_story`/`set_sleep_timer`) via `llm.chat(tools=...)`. `ask()` returns
  `{reply, actions, refused}`: a calm reply + **validated** `{action, args}` intents (names
  checked against the real registries, numbers clamped) for the Qt layer to apply; anything
  unknown/out-of-range/off-whitelist is refused, never executed. GUI-free, stateless, no
  free-form code; gated on `llm.available()`. Offline test: `tools/test_llm_assist.py`.
- **llm_plugin.py** — **EXPERIMENTAL**, opt-in, sandboxed LLM **code-plugin** generation. Off by
  default; `enable(accept_risk=True)` required. Writes to a gitignored `~/.breathsim/plugins`
  dir; the code is **never run in the app process**. Each candidate is statically pre-screened
  (`screen` -- a denylist of subprocess/socket/network/eval/exec/os.system/write-open …), then
  bug-tested in an **isolated subprocess** (`run_isolated`: `python -I`, minimal env, cwd =
  plugin dir, hard timeout, imports it + runs `selfcheck()`), with a generate→test→repair loop.
  Passing plugins are exposed via `loadable()` manifests only — the app never auto-loads them.
  Primary guarantees: opt-in + process isolation + no in-process exec. Offline test:
  `tools/test_llm_plugin.py`.
- **story_char.py** — maps a story scene / lecture to a fitting cartoon character
  (`char_for_scene`: sea→Penguin, night→Owl, forest→Bear, …, default Owl). Opt-in
  **Face ▸ "Character follows the story"** (persisted): when on and the cartoon face is
  shown, the storyteller swaps to the matching character via `set_character(persist=
  False)` and restores the user's saved pick afterwards (`win_story._apply_story_character`
  / `_restore_user_character`). Pure + testable.
- **story_bg.py** — maps a narrated line to a fitting `face_bg` backdrop
  (`bg_for_text`) + a calm base per story scene (`base_for_scene`), mirroring
  `breathsim.sound_cues` so the picture and soundscape follow the words together. The
  storyteller drives it via `win_story._apply_story_bg` (Sound ▸ "Backdrop follows the
  story", persisted). Pure + testable.
- **2D character cast** — the QPainter face shown when faceView is missing or the
  user picks **Sound ▸ Cartoon cat face** (then **Character** / **Costume** submenus,
  persisted). A small framework, all driven by the same per-frame state as the 3D
  head:
  - **char_anim.py** — `AnimState.step(dt, state) -> Anim`: the shared animation
    engine turning breath/mouth/eye/smile/gaze (+ optional `excite`) into rich,
    character-agnostic signals — breathing bob + squash, idle sway, blinks (incl.
    spontaneous), a continuously **swishing tail**, **ear twitches**, and a **"hair
    on end" bristle** that spikes on excitement / a rare startle and eases off.
  - **char_base.py** — shared kit: colour helpers, breath `aura`, big **cute glossy
    eyes** (blink / gaze / pupil dilation / happy squint / catchlight), `blush`,
    `head_box` framing, and the `Character` base + `Head` anchor (so a costume fits
    any character).
  - **char_<name>.py** — one file per character (all subclass `Character`, return a
    `Head`): **Cat** (default) · Penguin · Dog · Owl · Fox · Chicken · Bunny · Bear ·
    Panda · Frog · Duckling · Hedgehog · **Robot** (brushed-metal head, glowing eyes,
    pulsing antenna, LED mouth, chest core) · Woman · Man (chibi humans). Each uses
    the shared kit (tail swish, ear twitch, body breathing, bristle, blush) with its
    own drawing + signature touches.
  - **char_costume.py** — costume overlays positioned from the `Head` anchor (None,
    Wizard/Party/Top Hat, Beanie, Crown, Halo, Headphones, Sunglasses, Flower, Scarf,
    Bow Tie), with a faint cyber glow.
  - **char_voice.py** — per-character **voice + personality** profiles (`CharVoice`:
    ordered TTS name/prefix `hints`, speaking `rate`, signature eye/aura `hue`,
    `greeting`, `persona`); `get(name)`, `pick_voice(hints, available)` (first
    case-insensitive match, works for Kokoro ids + macOS `say` names). Applied when
    **Sound ▸ Character voices** is on; sets the narrator voice + the eye hue + a
    short greeting. Pure + testable.
  - **characters.py** — the registry (`names`/`get`, costume names + `draw_costume`).
  `FaceWidget` advances one `AnimState` per frame and draws `character + costume`;
  `window.set_character`/`set_costume` (persisted `character`/`costume`) pick them.
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
  thread; returns **RGBA** or `None` (→ software fallback). Reads the chosen
  **cyberpunk style** off `params._style` each frame and sets the shader uniforms +
  GL state (wireframe / point-size / translucent blend) per the render mode.
- **face_styles.py** — the **cyberpunk face-style registry** (pure data, no GPU
  import). A `FaceStyle` = an **eye pattern** (starfield · nebula · plasma · HUD
  circuit · matrix · solar · void · iris · holo · sonar) + a **skin treatment**
  (smooth · chrome · neon-rim · circuit · holo-scan · iridescent · matte · grid) +
  a **render mode** (solid · wireframe · dot-matrix points · translucent ghost) +
  an accent colour. `STYLES` holds 15 presets; **"Default" reproduces the classic
  look pixel-for-pixel**. Selectable by the user (**Sound ▸ Face style**, persisted
  as `face_style`, via `window.set_face_style` → `FaceWidget.set_style`) and
  callable by the storyteller / breath / chant to animate the face's mood.
- **face_shaders.py** — the GLSL strings: a vertex shader (writes `gl_PointSize`
  for the dot-matrix mode) and a fragment shader whose `eye_pattern()` /
  `skin_shade()` switch on `u_eye` / `u_skin` (id 0 = the exact classic starfield /
  smooth skin), plus a fresnel `u_ghost` alpha for the translucent mode, a breath
  `u_pulse` glow, and the unchanged lash line shaders.
- **face_react.py** — the optional **reactive face** mapping (pure): `style_for`
  picks a style from the live context (mode + chant/song + storyteller mood),
  `pulse_for(volume)` turns the breath into a gentle glow pulse, `mood_key` buckets
  the storyteller's emotion. The window applies it each frame with a short dwell so
  the look shifts gently; **Sound ▸ Reactive face** toggles it (persisted
  `face_reactive`, off by default) and it never changes the saved static style.
- **scenes.py** — Qt `QPainter` visualization scenes (ambient set): `OrbScene`
  (glow + guide ring + cycle dot + progress arc + drifting **motes**, soft **exhale
  rings**, and a mint **coherence halo** near ~6 breaths/min), `NightScene` (stars +
  moon, a deeper gradient, drifting **clouds**, a rare **shooting star**),
  `RippleScene` (resonance rings with **tone-reactive** colour/spacing + a pulsing
  central glow), `WaveScene` (moonlit sea: stars, moon + **reflection shimmer**, foam
  crests, layered swells) and `FireplaceScene` (hearth glow + swaying flame tongues +
  rising embers), a shared text overlay, and `make(name)`/`names()`. Larger scenes
  live in their own modules and self-register at the foot of this file:
  `scene_rain` (rain-on-window), `scene_aurora`, `scene_mandala` and `scene_candle`.
- **scene_candle.py** — `CandleScene`: a single warm candle flame in the dark to rest
  the gaze on (*trataka* focused-attention practice) — a pale wax body, the pool of
  light it casts, an ambient glow that **breathes with you**, and a layered teardrop
  flame (cool blue base) that sways + flickers gently and grows on the inhale.
- **scene_fx.py** — small, deliberately slow/dim **visual-effect helpers** shared by
  the scenes: `Motes`, `Clouds`, `ShootingStar` (stateful, seeded RNG) and a
  `starfield` drawer. Keeps the enrichment calming and `scenes.py` lean.
- **scene_pitch.py** — `PitchScene`: the pitch-trainer scene (note grid + target
  line + live-pitch trail + plain-words guidance), fed a `pitch` dict.
- **viz.py** — `VizWidget(QWidget)`: hosts a persistent scene, `set_scene(name)`,
  `update_state(ctx)` each frame; paints via `scene.draw(p, w, h, ctx)`. Also draws
  the corner **hourglass timer** (`set_hourglass(state)`) and forwards taps on it to
  `_hg_click_cb` (flip-to-reset). `FaceWidget` does the same. **`set_calm(on)`** is the
  accessibility **"reduce motion"** chokepoint: it feeds the scenes a virtual decorative
  clock that advances at 15% when on (so star-drift / twinkle / motes / flicker ease,
  while the breath-driven orb + guide dot, which read volume/cycle_frac, stay live) and
  drops the busy weather overlay. Driven by `window.set_calm_visuals` (View menu toggle,
  persisted `calm_visuals`, off by default). Offline test: `tools/test_calm_visuals.py`.
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
  view. **Resizable** (min 360 / max 520; lives in a `QSplitter` beside the
  visualization in `window.py`, so the user can drag it wider). Pinned title + mode
  bar + **face/scene toggle** + master volume + transport; a `QScrollArea` body
  (right margin clears the scrollbar) rebuilt per mode by **`build_workspace(name)`**.
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
- **menus.py** — `build(win)`: the native **menu bar**, the global escape hatch for
  every control, organised by intent: **File** (screenshots · Export submenu ·
  presets · quit) / **Modes** / **Sessions** (guided programs · courses · Quick-start
  submenu) / **Pattern** / **Voice** (favourites · in/out/body · Morph A▸B incl.
  **Automation**) / **Sound** (mute · background sounds · reverb space · XTTS · the
  audio toggles · **Ambience & instruments** submenu · sleep timer · mixer) /
  **Face** (background · style · reactive · character · costume · character voices) /
  **View** (face↔scene · scene · weather · text size · reading aids · hourglass ·
  Zen/Blackout/Fullscreen) / **Help**. Helpers `_toggle`/`_sub_list`/`_list_menu`
  keep it declarative. `win.rebuild_menu()` refreshes it; an offscreen audit triggers
  all ~427 items to guarantee every action fires.
- **shortcuts.py** — `bind(win)` global keys (Space play/pause · R reset ·
  F fullscreen · Z Zen · Esc exit) + `toggle_zen`/`toggle_fullscreen` (Zen hides
  the mode bar + panel + menus, leaving only the breathing face).
- **dialogs.py** — `open_stats` (practice history from `store`), `open_mixer`
  (per-slot levels), **`open_story_library`** (browse + search the stories DB via
  `story_db` — branch/lecture list, line view, full-text LIKE search) and
  `open_about`.
- **gratitude.py** — the optional **bedtime "one good thing"** note (Sessions ▸ "One good
  thing…" + a "Bedtime gratitude" toggle; off by default). `should_offer(on, last_date,
  today)` (pure gate), `ask_gratitude(win)` (a soft Keep/Skip `QLineEdit` dialog →
  `store.log_gratitude`, returns the note or None) and `maybe_offer_bedtime(win)` (offered
  **once** at a fresh Sleep start, beside `mood.maybe_check_in`). Persisted via
  `win_settings` (`gratitude`); a "Good things noted: N" line shows in Stats. Backed by
  `store.log_gratitude` / `gratitude_entries` / `gratitude_count` / `gratitude_last_date`
  (cap 200, 280-char clamp, malformed-safe). Offline test: `tools/test_gratitude.py`.
- **greeting.py** — the optional **spoken greeting by name** (Sessions ▸ "Greet me by name…";
  off by default). Pure helpers: `sanitize_name` (NFKD ASCII-fold → letters/space/`-`/`'`, 24-char
  cap, `''` = off), `greeting_line(name, hour)` (one soft, time-aware line; `None` without a name),
  `prepend(line, units)` (lazy generator: a `kind:"greeting"` unit then the story stream) + the
  little `ask_name` Save/Clear dialog. `win_story._start_story` prepends the greeting **once** per
  fresh session (guarded by `_greeted_session`); `app_actions.set_listener_name`/`ask_listener_name`
  set it; persisted via `win_settings` (`listener_name`). Offline test: `tools/test_greeting.py`.
- **llm_settings.py** — **`open_llm_settings`** (Help ▸ "AI Assistant (optional)…"): the
  opt-in, fail-closed gateway to the LLM stack. A **password-masked** key field with three
  honest storage choices (session-only / OS keychain / chmod-600 file), a **Forget** button,
  and a local-**Ollama** opt-in (persisted via `win_settings` `llm_ollama`, default off).
  Status shows backend + key **source**, never the key. Qt-free helpers `status_text`/
  `apply_key`/`forget` (the key is never returned in any message). Offline test:
  `tools/test_llm_settings.py`.
- **reader.py** — the non-sleep **Book Reader** (Books ▸ "Read a book…"): a modeless dialog with a
  book picker (empty-safe), a **read-along text ↔ audio-only** toggle, paragraph-pause + reading-speed
  presets; narrates a `books.Book` via `bookreader.units` through the shared Narrator at a steady pace
  (no breath-gating; `win._reading` guards `_apply_speech_pace`), persists the resume position per
  sentence, and (read-along) highlights + scrolls the current sentence via a GUI-thread QTimer.
- **llm_story_action.py** — the Sleep **"Generate a bedtime story (AI)"** action (a button on the
  story card). `can_generate` gates on `llm_story.available()` (disabled + hinted with no backend);
  `make_story(topic, complete=None)` generates + registers one AI story (Qt-free, off-thread safe);
  `generate_dialog(win)` asks a topic, runs generation on a **daemon thread**, returns via a
  **queued signal** (UI never blocks), arms the story for Sleep and offers Keep/Just-tonight. Offline
  test: `tools/test_llm_story_action.py`.
- **window.py** — `_breath_routing(phase, voice_a, voice_out)` + `_mouth_shape`
  decide the face's mouth/nostril motion per breath: **nose in-breath** (mouth
  closed, nostrils flare) and **mouth out-breath** shaped by the active voice
  (`_SHAPE_AUS`: pursed-lip / open "haa" / fricative sss / round OM / nasal
  ujjayi). `_face_inputs(state, running, amp)` then layers **talking over
  breathing**: while the storyteller voices a sentence the mouth lip-syncs to
  `narrator.amp` and the visible breath eases *down* (exhaling words); in the gap
  before the next sentence the mouth closes and the breath eases *up* (a breath in);
  with no recent speech the `_breath_routing` mouth applies.
  `MainWindow(_ActionsMixin, _PitchMixin, _HourglassMixin, _StoryMixin,
  _FrameMixin, _SettingsMixin, QMainWindow)` — now **lifecycle-focused** (~490
  lines, under the 500 rule): builds the core (controller / engine / speech /
  narrator / **SessionDirector**), `apply_mode` (audio preset + `panel.reflect_mode`
  → workspace rebuild; resets the director), transport (`toggle_transport`/`reset`,
  arming **settle-in** at a fresh start), volume (mute-aware), `set_pattern`
  (re-aims settle), blackout + quiet-hours, `save_screenshot`. The per-frame loop,
  storyteller runtime and settings round-trip were split into the mixins below.
- **win_settings.py** — `_SettingsMixin`: the preferences round-trip via
  `breathsim.store` — `_restore_settings` (reopen in the last mode / volume / view /
  toggles; suit the clock when nothing is saved) and `_persist_settings` (gather the
  live state into the settings dict on close). Split from `window` for the size rule.
- **win_consts.py** — shared frame-loop constants (`FPS`, the talk-detection
  thresholds), in a neutral module so `window` and `win_frame` both import them
  with no circular dependency.
- **win_frame.py** — `_FrameMixin` (inherited by `MainWindow`): the **~40fps
  frame loop** (`_tick` — now guarded so one bad frame logs once and the loop
  survives — + `_tick_impl`), the scene context (`_scene_ctx`), the
  talking-over-breathing face mouth (`_face_inputs`, layering lip-sync to
  `narrator.amp` over the `breath_routing` mouth), the status line
  (`_update_status`), Meditate guidance cues (`_med_phrase` over `_MED_CUES`,
  which stays a `MainWindow` class attr) and `_clock_warm`.
- **win_story.py** — `_StoryMixin` (inherited by `MainWindow`): the **storyteller
  + session runtime** — `set_story` / `set_story_voice`, the bedtime story
  (`_start_story` + per-lecture resume + `_on_story_unit` + `_story_level` fade +
  `_story_timing`), **storyteller pacing** (`set_speech_speed` /
  `_apply_speech_pace`), the **settle-in lead-in** (`_arm_intro` /
  `set_intro_lead_in` / `_intro_text`), the **audio-unavailable note**
  (`_note_if_silent`), ambience-follow (`_apply_soundscape` / `set_soundscape_follow`
  / ambience auto-rotate) — the **single ambience-level writer**, combining the cue
  **duck** with an opt-in **breath swell** (`_breath_swell_factor` /
  `set_breath_swell`: the bed rises with the inhale, softens on the exhale), mood
  check-ins (`set_mood_checkins` / `_after_mood`),
  practice logging (`_log_practice`) and `_ease_mood`. `launch()`.

## Vendored core — `breathsim/` (in this project)
The whole audio/logic/story core lives here, gui-free (the Tk GUI is not vendored):
`controller`, `engine`, `speech`, `narration` (Kokoro/say + lip-sync `amp`),
`stories` + the **lecture library** (`lectures` + `lectures_*.py`, 220+ across
44 branches incl. The Inner Planets (Mercury · Venus · Mars · Earth from Space) + The Great
Voyages + The Microscopic World + Weathers of the World + The Polar Worlds; Cosmos incl. Comets ·
Nebulae · Saturn's Rings; The Moons of the Giants) + **`shuffle`** (the **Cognitive Shuffle** sleep-onset aid) + **`hypnosis`** (a **Sleep
Hypnosis** guided session: induction -> deepening countdown -> suggestions -> drift; exposes
reusable `induction`/`drift_tail`) + **`hypnosis_topics`** (6 **themed self-help** hypnosis
sessions reusing that arc with a different permissive suggestion block -- Letting Go of Stress
/ Quiet Confidence / Calm Focus / Letting Go of Worry / Deep Self-Acceptance / Peaceful
Gratitude, all winding down to sleep) +
**`poetry`** (original soothing **English Nocturnes** + a shared `recite()`; old "Poetry" name
kept as `ALIAS`) + **`poetry_world`** (3 more **"Pure Poetry: <tradition>"** sessions reusing
`poetry.recite` -- **Haiku & Tanka** (Japanese), **Tang Nature** (Chinese), **Persian**
ghazal/rubaiyat; all original verse written *in the spirit of* each tradition) + **`haiku`**
(**"Drifting Haiku"** -- a season-aware grammar that endlessly composes original haiku/tanka
from per-season image banks, drifting through the year; exposes `compose()`) + **`haibun`**
(**"A Wandering Haibun"** -- Basho-style wandering prose, reusing the `stories` scene vocab,
crystallised every few lines by a `haiku.compose` poem) + **`tales`** (**"Quiet Tales"** -- 6
conflict-free **kishotenketsu** 4-movement micro-tales, a gentle narrative class) - all Sleep
storyteller options via `stories.extra_names()`; the shuffle is a stream of random neutral nouns),
**`sound_cues`** (text→ambience), **`story_db`** (SQLite record of every
story; `build`/`connect`/`search`/`lectures_in`/`lines_of`/`stats`; CLI
`python -m breathsim.story_db`), `kokoro_tts`, `voices`, `patterns`, `modes`,
`personas`, `choir`, `session` (SessionDirector), `programs`, `phrases`, `store`,
`tracks` (+ `rhythm`, **`textures`** — the `kind="texture"` event generators for the
Campfire / Singing Bowl / Wind Chimes / Night Crickets / **Purr** ambiences;
`textures.register_generator` lets other modules add `kind="texture"` voices),
**`voices_cat`** — the **Cat** voice group (`GROUP_CAT`), and **`cosmic`** + **`reverb`**
— the **Cosmic Music** generative engine (`GROUP_MUSIC`: Music of the Spheres ·
Starlight Choir · Deep Space): endless, non-repeating, just-intonation pads scheduled on
near-coprime cycles over a drone with slow root drift, washed through a block-delay
feedback-comb `reverb.Reverb`; and **`synth_bell`** — a struck-resonator engine + 12-instrument
**Bells & Gongs** library (`GROUP_BELLS`: bells / bowls / gong / triangle / tingsha / tubular +
a sung bowl) tolling slowly as a meditation/ambience bed; and **`synth_drum`** — a
membrane/percussion synth + **Drums** library (`GROUP_DRUMS`: frame/taiko/tabla/djembe/log/
woodblock/bodhran) struck on a tempo (effects slot); and **`synth_wind`** — sustained additive
**Winds & Organs** (`GROUP_WIND`: Pipe Organ, Harmonium/Shruti, Reed Organ, Wooden Flute +
Train Whistle / Fog Horn / Ship Horn periodic blasts); and **`synth_fx`** — composite
**Environmental FX** (`GROUP_FX`: Train Steam/Diesel, Ship/Harbour, Thunderstorm, Ocean Buoy
Bell). Together these four `synth_*` modules add 31 synthesised instrument/effect voices. The
2D fallback face is the **character cast** (`vesper/characters.py` + `char_*`).

**Audiobooks (the novels/reader feature, in progress):** **`booktext`** — pure text
processing (no I/O): `to_ascii` (fold smart quotes/dashes/accents), `strip_boilerplate`
(Project Gutenberg header/footer), `split_paragraphs`, `split_sentences` (abbreviation-aware),
`segment` → paragraphs-of-sentences, `chapter_marks`; and **`books`** — a `Book` model
(`paragraphs` + `sentences()`/`sentence_count()`/`paragraph_starts()`), `from_text`, and a **local
library** at `~/.breathsim/books` (`save`/`load`/`list_books`/`delete` + a self-contained
`_index.json`/`_progress.json`) with a per-book **resume** `position`/`set_position`/`clear_position`.
And **`bookreader`** — `units(book, start, line_pause, para_pause)` / `resume_units(book)` yield one
narrator unit per sentence (longer pause at paragraph ends; the `sentence` index drives resume).
Offline-tested (`tools/test_books.py`, `tools/test_bookreader.py`). The non-sleep Reader UI is
`vesper/reader.py` (Books menu). A library book is ALSO a **Sleep storyteller option** ("Book:
<title>"): `stories.book_names()`/`book_id_for()` + a `BOOK_PREFIX` dispatch in `story_units`/
`ambience_for` narrate it through the ordinary Sleep path (so it rides the wind-down + sleep-timer
fade-out) and resume by sentence (`tools/test_book_story.py`). **`booksource`** is the on-demand
public-domain **downloader** -- pure `parse_gutendex`/`text_to_book` + networked `search`/`download`
(Project Gutenberg via the open Gutendex API, NO key; network only on an explicit call, UA + timeout +
size cap + rate limit, fail-closed); `vesper/booklib.py` is its **Find & manage books** dialog (Books
menu: off-thread search/download + a delete-able library list). Offline-tested with an injected fetch
(`tools/test_booksource.py`, zero sockets). **`bookimport`** imports the user's OWN files (no network):
`import_txt`/`import_epub`/`import_file` -- defensive decode, stdlib zipfile+xml.etree EPUB parse (OPF
spine + tag-strip) with **zip-bomb guards** (per-entry/total/entry-count caps), fail-closed, saved
LOCAL; the GUI hook is `booklib.import_book_dialog` (Books ▸ "Import a book (file)..." + a button in
the dialog). Offline-tested (`tools/test_bookimport.py`, in-memory epub/txt). This also unlocks
Standard Ebooks (EPUB). Progress: `books.percent_read`/`books.in_progress` + `resumehint.
book_continue_hint` drive a **% read** read-out (Reader + library list) and a "Continue your book"
launch hint (`tools/test_bookprogress.py`). The audiobook feature is end-to-end (download / import /
read / sleep-narrate / resume), all opt-in + local-first. **`bookcast`** (pure, offline) turns a Book
into a **cast Script** -- `script(book)` heuristically assigns who speaks each sentence (dialogue +
attribution detection, deterministic character casting, emotion + ambience hints) for the dramatized
reader; no LLM, no `vesper` import (`tools/test_bookcast.py`). The **Dramatized** playback is
`vesper/cast.py` (`_CastMixin`, a Books-menu toggle, default off): `build_cast`/`cast_annotate`/
`apply_cast_tick` read the cast Script and per line switch the narrator **voice** (via `unit["voice"]`,
honoured by `narration.Narrator._loop`), swap the visible 2D **character** + set a gentle **mood**;
pure `segment_plan` offline-tested (`tools/test_cast_plan.py`). **`llm_cast`** is the opt-in LLM
**cast director** (validated + fail-closed): `direct(book, characters, costumes, complete=None)`
pre-reads a capped sample, clamps the model's cast to the registries, falls back to the heuristic, and
caches once per book (`~/.breathsim/casts.json`); `cast.build_cast` prefers the saved cast and runs the
director off-thread only when Dramatized is on AND a backend exists (`tools/test_llm_cast.py`, stubbed).
Dramatized playback also swaps the **costume** per speaker; `cast.cast_summary` + Books ▸ "Who's in this
book…" show the cast (speaker -> character + costume + source) with a **Re-cast** button
(`tools/test_cast_summary.py`). The cast/dramatized-books thread is complete (CAST-1..CAST-5).

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
