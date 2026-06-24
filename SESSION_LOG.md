# SESSION_LOG — Breathing Sim (PySide6 rebuild)

## Session — Phase 1: new Qt project + 3D talking-head face

Started the PySide6 rebuild (chosen over a Tk-embedded face) as a **new project**
that reuses the existing `breathsim` audio/logic core unchanged and adds a Qt
front-end centred on faceView's face.

**Decisions / findings**
- PySide6 + moderngl already in the env; faceView `pip install -e ../faceView`.
- `render_face(FaceParams, size) -> BGR ndarray` is a clean pure entry point.
- All render modes work offscreen here. Software render speeds: stylised 3.3 ms,
  **makehuman_3d 10.5 ms** (smooth at 40 fps → default), head_decimated 56 ms,
  ict_face 65 ms (best-looking but software-slow; GPU modes are future work).
- Fixed scanline skew by packing frames as RGBA8888 (4*w aligned stride).

**Built** (`vesper/`): `__init__` (core path bootstrap), `theme`, `face`
(FaceWidget: breath→head nod + breathing zoom, narration amp→jaw lip-sync, slow
blinks), `controls` (mode bar / pattern / face mode / Sleep story / volume /
transport), `window` (MainWindow + 40 fps loop + modes + story + Sleep dimming),
`run.py`. Reuses controller/engine/speech/narration(Kokoro)/stories/voices/
patterns/modes/personas/choir.

**Verify**: boots offscreen, applies Sleep, runs, renders the face cleanly
(stylised + makehuman_3d + ict_face_3d grabbed to PNG — 3D head confirmed); story
arms with matching ambience + Kokoro voice; files < 500 (window 219).

## Session — ICT-only blue face + smoothness; GPU assessed

- **Removed the other face modes** (makehuman/stylised/decimated/anatomical) and
  the render-mode picker. The face is now **ICT only** (the one that rendered
  well), coloured **blue** (`skin_hue` 206 + blue hair-cap so the crown isn't
  brown), light smooth skin + rose lips → **younger, feminine**. Softened jaw gain
  so lip-sync looks natural.
- **Smoothness**: ICT is ~65 ms/frame software, so it now renders on a
  **background thread**; the GUI blits the latest frame each tick with the
  breathing zoom (40 fps motion, ~15 fps face). UI stays responsive.
- **GPU support — assessed, not shipped.** ICT has no GPU path in faceView; its
  GPU renderers (head_decimated/faceforge) target other meshes and rendered
  **broken + un-coloured** here (verified). moderngl *does* work offscreen
  (head_decimated_3d_gpu 5 ms, faceforge 27 ms), but a real GPU-ICT means porting
  ICT posing + per-material palette + its camera/shading to moderngl — a focused
  follow-up. The render thread delivers the smoothness meanwhile.

## Session — GPU-ICT renderer + the Claude avatar

- **Built `face_gpu.py`** — a moderngl GPU renderer for the ICT head: reuses ICT's
  mesh + `apply_blendshapes` (incl. persona identity weights) + `_material_palette`,
  lambert + **rim-glow** shader, orthographic aspect-correct fit, lazy standalone
  context on the worker thread, BGR out, `None`→software fallback. **~11 ms/frame**
  (vs ~65 ms software) → full 40 fps. Fixed orientation (base 180° yaw so the face,
  not the back of the head, faces the camera).
- **Switched the face to faceView's Claude avatar** = the `ict_xray_young` persona
  (glowing-cyan xray ICT head, "young" identity), applied via
  `personas.load_persona`/`apply_persona`. This is what the faceView characters
  file names as the default Claude face — and it's the calm blue look wanted.
- FaceWidget now renders the Claude avatar via GPU in the worker thread (software
  fallback), breathing + lip-syncing as before.

Verify: GPU renders the Claude avatar front-facing at 11.6 ms; full app runs with
`gpu=True`; PNGs captured (software target + GPU). Known gap: xray eye-emissive
glow not reproduced by the GPU shader (refinement noted).

## Session — eye fixes + screenshot feature

- **Screenshot feature**: File ▸ Save Screenshot (Ctrl+S) + Save Face Only
  (Ctrl+Shift+S) → `MainWindow.save_screenshot(path, face_only)`. Used it to
  inspect/iterate the face.
- **Eyes** (GPU `face_gpu._color_emit`): the lambert shader couldn't reproduce
  the xray eye look, so — sclera/iris use natural colours and a per-vertex
  **emissive** so they self-light when open; as the lids close they **blend to
  the eyelid skin colour and emissive fades to 0**, so a shut lid shows neither a
  black nor a bright eyeball (the original bug). The eye socket/lashes were a
  near-black hole → now a **soft skin-shadow**; the tear-duct catch-light is
  dimmed. Diagnosed the layering by colour-coding the eye materials and rendering.
- Verified open (alive eyes + catch-lights) and closed (gentle lids, no eyeball)
  via screenshots; full app runs `gpu=True`. Teeth left as-is (look fine).

## Session — starry-sky eyes + breathing nostrils/mouth

- **Starry-sky eyeballs**: procedural twinkling + drifting **starfield** in the
  GPU fragment shader (deep-space sky + hashed stars), animated by a `u_time`
  uniform (= the face's `_t`). Gated to the eyeball verts via `v_emit`, so it still
  fades into the eyelid when the lids close. Tuned star size/density/brightness so
  it reads at eye scale; verified the pattern changes over time.
- **Forward gaze**: `pupil_x/pupil_y = 0` so the eyes look forward.
- **Breathing nostrils + mouth**: `set_state` now takes `airflow`+`phase`; nostrils
  flare (`nose_wrinkle`) and the mouth opens gently on the in-breath, combined with
  the narration amplitude for speaking (`jaw_open = max(speaking, breath)`).
- Verified live (gpu=True): stars animate, mouth breathes/speaks, files < 500.

## Session — mouth matches the breath type (nose-in / mouth-out + shapes)

Breathing mouth was backwards (opened on inhale). Now `window._breath_routing` +
`_mouth_shape` route it by phase + the active voice:
- **In-breath = nose** (mouth closed, nostrils flare); out-breath = mouth.
- **Out-breath mouth shape** from the exhale voice (`_SHAPE_AUS`): pursed-lip
  (`mouth_pucker`), open "haa"/sigh (`jaw_open`), fricative sss/shh/fff
  (`mouth_stretch`), round OM, or **nasal** (ujjayi/hum/nose → mouth stays shut,
  nose breathes). Verified: Breathwork = nose-in + pursed-out; Ujjayi = nasal both.
- `face.set_state` now takes `mouth/nose/pucker/stretch`; **speaking** (narration
  amp) opens the mouth and relaxes the shape.
Confirmed the ICT renderer shows distinct mouths (pursed vs open vs fricative);
live app gpu=True.

## Session — mouth stays shut during the nasal in-breath

The mouth was still cracking open as the nostrils flared on a nose in-breath.
Root cause: the only nose AU (`noseSneer`, AU9) **also lifts the upper lip**, so a
big flare value opened the mouth. Confirmed by render sweep — jaw=0 + nose 0.0
closed, 0.15 just-closed (lip highlight), 0.4/0.8 gaping.
- `window._breath_routing`: nasal inhale now `jaw=0.0, nose=0.12` (was 0.03/0.8);
  exhale nasal flare 0.12 (was 0.6), non-nasal 0.05, holds 0.03.
- `face.set_state`: `nose_wrinkle` hard-capped at 0.16 so it can never lift the lip.
Nostril flare is therefore only a faint hint (the AU can't truly widen nostrils);
the closed mouth wins. Verified via routing crops (nasal-in closed, pursed-out
puckered, open-out open) and a live gpu=True smoke run.

## Session — talking takes precedence; speak on the out-breath

Reworked the face's mouth so **speech overrides breathing** and the rhythm reads
naturally: breathe in, then speak on the exhale, with a breath between sentences.
- Precedence resolution moved to `window._face_inputs(state, running, amp)`;
  `face.set_state` is now a dumb state-holder (dropped its internal amp mixing — new
  signature `set_state(vol, t, prog, mouth, nose, pucker, stretch)`).
- A voiced frame (`narrator.amp > _AMP_TH`) ⇒ **speaking**: jaw lip-syncs to amp,
  breath shapes (pucker/stretch/nose) suppressed, and the **visible breath eases
  *down*** (an exhale, target 0.28). Short word gaps (< `_SPEAK_HOLD` 0.35 s) still
  count as speaking so the mouth doesn't snap shut between words.
- A longer gap (storyteller's inter-unit pause) ⇒ **between sentences**: mouth
  closes, faint nostril flare, and the **visible breath eases *up*** (a breath in,
  target 0.92). After `_TALK_WINDOW` (9 s) of silence it reverts to plain breathing.
- The eased breath now also drives the breathing zoom + head-nod, so the head
  visibly takes a breath in during the gap then settles while speaking.
Verified by simulating a sentence→gap→sentence amp script: jaw 0.5→0 at speech end,
breath 0.50→0.28 while speaking then →0.92 in the gap, back to lip-sync next
sentence; live gpu=True boot with injected amp runs clean.

## Session — natural variability in the in-breath mouth opening

The in-breath opened the mouth by a fixed amount every cycle (mechanical). Added a
per-breath random scale `_sample_inhale_open()` = `random()**2` (skewed low), stored
on `self._inhale_open` and **resampled at each inhale onset** (and at each
between-sentence breath in the talking path).
- `_breath_routing` inhale jaw is now a *maximum* parting (nose 0.12, oral 0.40);
  `_face_inputs` multiplies it by `_inhale_open` only on the inhale phase.
- Result over 400 nose breaths: median jaw 0.03, ~56% nearly closed, ~14% a slight
  parting, capped ~0.12 — variable and usually small. Oral in-breaths went from a
  constant 0.40 to median ~0.09 (occasional up to 0.40). Satisfies "more
  variability, most of the time less than before." Live gpu=True boot clean.

## Session — storyteller pacing: longer pauses + speech speed (slows over time)

- **Core (`breathsim/narration.py`)**, backward-compatible (defaults 1.0 ⇒ old
  behaviour, Tk app unaffected — verified): added `Narrator.speed` (rate
  multiplier, folded into the Kokoro `_speed(lvl)` + `say` `_rate(lvl)`) and
  `Narrator.pause_scale` (scales the **between-statement** pauses only; breath-cued
  `phase` pauses stay matched to the breath). Pause clamp raised 12 s → 20 s.
- **Window**: `_pause_scale = 1.4` base (longer gaps between statements) and
  `_apply_speech_pace()` (called each running tick) **subtly slows over ~10 min** —
  speed ×1.0→×0.82, pause_scale ×1.4→×2.1. `set_speech_speed(v)` is the user base.
- **Controls**: a **Speech speed** slider (0.60×–1.20×) in the Sleep story panel.
- Verified: kokoro speed 0.88→0.72 and say 140→114 wpm across the session;
  between-statement pauses scale (900→1260→1890 ms) while breath cues stay at the
  breath length; defaults reproduce the original numbers exactly; Qt boots clean.
- Note: `run.py --selftest` flags a **pre-existing** "Brown Noise peak 1.04 > 1.0"
  calibration drift (unrelated to narration — left for a separate recalibration).

## Session — ported the Tk app's features (workspaces, menus, sessions, more)

A large feature-parity pass, all reusing the shared core, all files < 500 lines
(window 396, sections 252). New `vesper/` modules:
- **widgets.py** — `card`, `LabeledSlider` (slider + live read-out), combo helpers.
- **workspaces.py** + **sections.py** — a **workspace-driven panel**: each mode
  rebuilds the scroll body into a distinct card set (Meditate = pace/resonance +
  naturalness; Breathwork = pattern + guided programs; Chant = mantra + choir;
  Sing = voice + choir; Relax = soundscape; Sleep = story + wind-down).
- **controls.py** rewritten as `ControlPanel(_SectionsMixin, …)`: pinned mode bar +
  volume + transport, `build_workspace`/`sync`/`tick`. (Fixed a rebuild bug —
  `setParent(None)` before `deleteLater` so old cards don't bleed through.)
- **app_actions.py** — `_ActionsMixin` on MainWindow: voice/body/ambience/effect/
  morph/naturalness/choir/phrase/cue/pace/program/wind-down/mute/slot actions.
- **menus.py** — full menu bar (File/Modes/Sessions/Pattern/Voice/Sound/View/Help)
  as the global escape hatch (every voice by group, Morph A▸B, background-sound
  toggles, chime, naturalness, Mixer, Zen/Fullscreen, Stats/About).
- **shortcuts.py** — Space/R/F/Z/Esc + **Zen** (hide panel/menus/bar).
- **dialogs.py** — practice **Stats**, per-slot **Mixer**, About.
- **stage_apply.py** — applies a guided-program `Stage` to the Qt app.
- **window.py** — wired the **SessionDirector** (morph automation + guided
  **programs** + sleep wind-down) into the loop, mute-aware volume, practice
  **logging** (`store.log_session`), and **last-settings persistence**
  (`_restore_settings` on boot + `save_settings` on close).
Verified: boots; every mode's workspace builds + scrolls cleanly (screenshots);
menus present; a guided program applies its stage 0 (pattern+voice); toggles/mute/
wind-down/choir/pace/morph all act on the core; practice logs; settings round-trip;
core `--selftest` passes (the earlier Brown-Noise warning was intermittent RNG).
Deferred: Qt scenes + face/scene toggle, pitch trainer, voice/pattern editors,
presets manager, retention timer (noted in INTERFACE roadmap).

## Session — Qt scenes + face/scene toggle + pitch trainer + more controls

Built the visual scenes as QPainter widgets and a central face↔scene toggle, plus
new controls. All files < 500 (window trimmed 469→410 by extracting face_motion).
- **scenes.py** — `OrbScene` (radial-gradient glow + guide ring + cycle dot +
  progress arc), `NightScene` (stars + moon halo), `RippleScene` (resonance rings),
  `WaveScene` (layered sea) + shared text overlay + `make`/`names`. Real alpha /
  gradients (an upgrade on the Tk blend-to-bg glow).
- **scene_pitch.py** — `PitchScene` pitch trainer: note grid + bright target line +
  live-pitch trail (green in tune) + plain-words Higher/Lower/In-tune guidance.
- **viz.py** — `VizWidget` hosting a persistent scene (`set_scene`/`update_state`).
- Central area is now a **`QStackedWidget(face, viz)`**; **face↔scene toggle** via
  pinned panel buttons + View menu (+ Scene picker) + **`V`** shortcut; auto-scene
  per mode; the chosen view persists (store settings).
- **pitch.py** — `_PitchMixin`: mic `Tuner` (degrades w/o mic), `show/hide_pitch_guide`
  (switches to the pitch scene + starts mic), `pitch_context`, reference tone.
  `_card_pitch` (Sing & Chant): hold-note / scale exercise + guide + reference.
- **face_motion.py** — pure mouth/nostril routing extracted from window.py.
- More controls: **mindfulness bell** (Meditate, interval chime in the loop) and
  breath-hold **retention timer** (Breathwork, logs holds via `store.log_hold`).
Verified offscreen: all scenes render (screenshots — orb/night/wave/pitch look
great), view toggle + scene picker work, pitch guide switches scene + opens mic,
bell + retention behave, every workspace builds, settings round-trip, core
`--selftest` passes (85 voices, 21 presets).
Remaining: Voice/Pattern editors + Presets manager; phrase-sequencing UI.

## Session — backgrounds behind the face + eyeball-shadow fix

- **Eyeball shadow removed**: `M_EyeOcclusion` was drawn at `skin*0.82` and further
  darkened by lambert → a shadow ring around the eye. Now coloured to the eyelid
  skin (`lid*1.08`, no shadow); lashes kept a faint hint (`skin*0.9`). Verified via
  open + half-closed eye crops — clean, starry eyes, no ring.
- **Animated backgrounds behind the face**: the GPU renderer now clears the FBO to
  **transparent** and returns **RGBA**, so an effect can show behind the head. New
  **face_bg.py** painters — None / **Stars** (matches the starry eyes) / **Aurora**
  / **Nebula** / **Gradient** — all tinted by the breath-phase hue and pulsing with
  the breath. `FaceWidget.paintEvent` paints the backdrop then composites the head;
  `set_background` + `set_state(..., phase=)` for the tint. Picker in **View ▸ Face
  background**, persisted (default Stars).
- The software fallback (no GPU) stays opaque (background hidden) — graceful.
- Perf: `FaceWidget.set_active(False)` throttles the head render thread when the
  scene view is showing (driven by `set_view`).
- Cleanup: removed the now-unused `_hex_rgb`; window 418 lines, all files < 500.
Verified offscreen: head composites over each background (screenshots — Stars +
Aurora look great), eye crops show no shadow, every mode + bg + view toggle works,
face_bg persists, render throttles to inactive when scene shown.

## Session — new story category: soothing sleep-lectures (physics)

Added a **lecture** category to the bedtime storyteller (core `breathsim`, so both
apps get it): authored, finite, poetic deep-dives that lull rather than teach.
- Core: **lectures_physics.py** (content) + **lectures.py** (framework). First
  lecture **"Spacetime & the Quantum"** — relativity, wave–particle duality, the
  quantum universe, cosmology, with critical experiments (Michelson–Morley, the
  1919 eclipse, the double-slit, Bell/Aspect, Hubble, Penzias & Wilson) and the
  recurring *math as metaphor* thread. 7 sections, 82 lines (~1480 words), Brown-
  Noise ambience; delivered slowly (1.4–2.1 s pauses ×pause_scale) with breath/
  body-scan interludes woven between sections.
- `stories.story_units` now dispatches to `lectures` by name; added
  `lecture_names()` + `ambience_for()` (also fixes a latent "Random" KeyError).
- Qt: the Sleep **Bedtime story** picker lists lectures under a separator;
  ambience lookups use `ambience_for`.
Verified: lecture yields 100 finite units (82 lecture + 18 guide), ambience voice
registered, the narrator streams it (subtitle shows the opening line), every scene
still infinite, "Random" no longer crashes, core `--selftest` passes (85 voices).
Framework supports more lectures — drop a content module + one `LECTURES` entry.

**Series → 16 lectures** (core, drafted in parallel batches): Spacetime & the
Quantum · The Life of a Star · The Wandering Moon · The Northern Lights · The
Turning Year · Deep Time · A River to the Sea · The Deep Ocean · The Song of Whales
· The Migrating Birds · The Quiet Life of Plants · The Hidden Kingdom of Fungi ·
The Living Cell · The Human Heart · The Breath (on-theme) · The Sleeping Brain —
each ~1,000–1,500 words, 7 sections, real science + named experiments, closing
toward sleep, ordered cosmos→sky→earth→ocean→life→body→sleep. The Sleep story
picker lists all 16 under a separator; ambiences resolve via `ambience_for`.
Also recalibrated core Pink/Brown Noise gains to 0.16 (worst peak ~0.81/0.83 over
120 runs) so the masking-noise voices never clip — `--selftest` now passes 5/5.
Verified: all 16 load + finite + valid ambience + 0 malformed lines; Qt picker 24
items.

## Session — lectures → 44, grouped into branches in the Sleep picker

The core lecture collection grew to **44 across 6 branches** (The Cosmos · Earth &
Sea · The Living World · The Human Body · Histories · Ideas & Wonders) — added a new
**Histories** flavour (Tea, Silk Road, Alexandria, Bread, Maps, Clocks, Spices,
Salt, Chocolate, Coffee, Paper, Gardens) plus more science/nature/body/ideas.
- Qt: the Sleep **story picker now groups lectures by branch** — for each
  `stories.lecture_categories()` a separator + a disabled "— <branch> —" header,
  then `stories.lecture_names(branch)`. Picker = 63 items, 6 disabled headers.
- Note: this was completed after a multi-hour Anthropic platform outage of the
  write/command safety classifier (resumed automatically via scheduled rechecks).
Verified: all 44 load + finite + valid ambience + unique names + 0 malformed lines;
`--selftest` passes; offscreen Qt picker shows the 6 branch headers and lectures
select + set their ambience.

## Session — text-matched soundscape, lifelike face, +6 lectures, auto-loop

Three feature workstreams + the autonomous loop the user asked for.
- **Soothing sound matched to the text**: core `sound_cues.cue_for_text` maps imagery
  (rain/waves/wind/hearth/stars/thunder/ice…) to ambient voices; the storyteller's
  per-line callback (`_on_story_unit`) steers `_sfx_target`, and `_tick`
  **crossfades the ambience bed** toward it (`_apply_soundscape`, fade 2.5s), easing
  back to the lecture's base ambience over abstract passages. Verified live: the
  Deep Ocean lecture morphs Ocean→Brown Noise at "abyss/stars"→Pink Noise at
  "stillness". Fixed a "the sea**sons**" false positive.
- **More naturalistic face** (`face.py` + `face_motion.emotion_for_text`): wandering
  gaze, tiny head sway, **randomized blinks** (varied gap, occasional double, heavier
  as it winds down), and an **emotion** eased from the line's mood (wonder/awe/
  curiosity/calm → smile/brow/eye-openness), via `_ease_mood` → `set_state(...,
  smile, brow, eye_bias)`. Decays to a serene baseline when idle.
- **Library → 50 across 7 branches**: new **Materials & Making** branch (Glass · The
  Potter's Wheel · The Loom · Ink · Candlelight) + The Constellations (Cosmos).
- **Autonomous update loop**: `UPDATES.md` backlog + a self-paced scheduler — each
  round researches/plans/implements/**tests** one item (selftest + integration must
  pass), logs, and reschedules.
Verified: 50 lectures load/finite/unique/0-malformed; `--selftest` passes; live Qt
soundscape + expressive face confirmed (screenshot).

## Session — self-contained project + stories database + todo tracking

- **Vendored the core** into `vesper/breathsim/` (gui-free, 748K) so the
  project is independent of the sibling `breathing_sim` folder. `vesper/__init__.py`
  now puts the project root on `sys.path` (local `breathsim` wins). Proved
  independence: boots from the vendored copy even with the sibling hidden. Added
  `selftest.py`, `requirements.txt`, `README.md`. faceView (~1.2 GB) stays an
  external pip dep, documented. The autonomous loop now edits the VENDORED core
  (UPDATES.md + the scheduled prompt updated; tests via `python selftest.py`).
- **Stories database**: `breathsim/story_db.py` builds a SQLite record of every
  lecture + scene (`data/stories.db`: 54 lectures · 8 branches · 4,520 lines ·
  67,042 words · 5 scenes), rebuilt on startup (`python -m breathsim.story_db`).
  Query API (`search`/`lectures_in`/`lines_of`/`stats`) + a **Help ▸ Story Library**
  browse/search dialog.
- **Todo tracking**: a task list now mirrors the UPDATES.md backlog (tasks #35–#45);
  the loop maintains it each round. Round 1 (Myth & Legend) + self-contained + DB
  are done; #36–#43 remain.
Verified: independent boot, DB build + query + dialog, `selftest.py` passes (85
voices, 54 lectures, 8 branches).

## Auto-round 2 — The Senses (→ 57 lectures)

Added The Ear and Hearing · The Sense of Smell · The Sense of Touch to The Human
Body branch (now 9). Accurate, gentle, sensory + sleep-tie-in. Vendored core;
selftest passes (85 voices, 57 lectures, 8 branches); DB rebuilt (4,772 lines).

## Auto-round 3 — focus shift to app improvement (per-window theming)

Re-aimed the autonomous loop from "more lectures" to **researched app improvement**
(graphics, effects, sleep/meditation efficacy per window) — rewrote `UPDATES.md`
with evidence-based research notes + a prioritized, per-window roadmap (warm
low-blue Sleep dimming, breathwork patterns + phase visual, scene enrichments, more
ambiences, soundscape ducking, face naturalism, MSAA, pitch scoring…). Stories
continue secondarily (~every 3rd round).
- Implemented: **per-window themed backdrops** — each mode auto-sets a fitting face
  background (Meditate=Gradient · Breathwork/Sing=Aurora · Chant=Nebula ·
  Relax=Underwater · Sleep=Stars) + two new effects: **Underwater** (light shafts +
  bubbles) and **Embers** (warm hearth + rising sparks). Verified: renders clean,
  per-mode theming applies, `selftest.py` passes (85 voices, 57 lectures).

## Auto-round 4 — Sleep warm/low-blue progressive dimming

`face_bg.warm_overlay(p,w,h,amount)` over-blends a dark amber wash that darkens AND
pulls blue down (melatonin-friendlier than a cool screen). FaceWidget + VizWidget
paint it last via `set_warm`; `window._tick` grows it 0→0.5 across the Sleep
wind-down and keeps a gentle window dim (0.3·prog). Verified: selftest passes;
early render clear, late render warm + dim (night scene moon/stars muted amber).

## Hotfix — face-view crash (worker-thread storm)

A regression from round 4: the `set_warm` edit accidentally displaced the render
worker-thread start out of `FaceWidget.__init__` and into `set_warm` — which the
loop calls every frame, so it spawned a fresh moderngl/OpenGL worker thread ~40×/s
→ a thread storm of GL contexts → SIGSEGV (EXC_BAD_ACCESS) on a worker thread when
the face view rendered. Fix: one worker started once in `__init__`; `set_warm` is
now a plain setter; added a `BSQT_FACE=software` escape hatch (force the CPU
renderer if a machine's GL driver is unhappy). Verified: thread count stays at 2
through 60 ticks + view toggles; face renders (GPU, non-black); selftest passes.

## Auto-round 5 — Breathwork patterns + phase visual

Box 4-4-4-4 and 4-7-8 already in PRESETS; added a **Physiological Sigh** (2.5-1-6,
a 4-phase take on the double-inhale). Added an orb **phase-progress ring**: a faint
full ring + a bright arc that fills over the current phase and resets, coloured by
the per-phase hue so inhale/hold/exhale/rest (and the holds) read at a glance
(`_scene_ctx` now passes `progress`). Verified: selftest passes; orb renders the
ring; thread count stable across ~84 ticks (new guardrail check).

## Feature — eyelashes as individual glowing strands

The ICT lashes are a smooth ribbon (12 segments, no UVs → can't alpha-texture), so
our flat fill rendered them as a solid sheet. Now `face_gpu` hides the ribbon in the
main pass and `_lash_lines` generates ~10 fine strands per lid from the lash line,
radiating outward from each eye centre (length scaled by verticality — long top &
bottom, short at corners), drawn as alpha-blended cyan lines (`_LVS`/`_LFS`) on top,
deforming/blinking with the eyes. Verified via eye-crop + full-face renders; thread
count stays at 2; selftest passes.

## Fix — lashes now follow the eyelid rim
The first strand pass radiated from each eye *centre*, so the lashes fanned from a
point instead of tracking the lid. Rewrote `_lash_lines` to use the ribbon's own
geometry: PCA each lid segment into a length axis (along the lash line) and a width
axis, split the verts into the ribbon's two long edges, pick the **root edge** (the
one nearer the eyeball) as the lash line and the other as the free **tip edge**.
Strand roots are the actual root-edge vertices (so they sit on the rim and follow its
curve); each grows toward its paired tip (interpolated at the same position along the
line) with a gentle outward curl (quadratic bezier, perp-to-growth). Blob segments
(aspect < 2.2, e.g. the inner corner) and roots outside the tip-edge span are skipped
to kill the medial-corner tangle. Verified via high-res eye-zoom + both-eyes +
half-closed renders; thread count stays at 2; selftest passes.
Follow-up: shortened the strands a touch overall and added a length **taper along each
segment** (`0.45 + 0.55·sin(πf)`) so lashes are longest mid-lid and short at the
corners (where they had looked strange); curl scales with the tapered length too.

## Feature — hourglass session timer (toggle, flip-to-reset)
An optional countdown of the current session, drawn as a glass hourglass with flowing
sand in the bottom-right corner of either view (visible but out of the way). New
`vesper/hourglass.py` painter: the top bulb drains and the bottom heap (+ falling
stream) fills as `frac = elapsed/session_seconds` goes 0→1; a `spin` arg rotates it
for the flip. `FaceWidget`/`VizWidget` draw it (`set_hourglass`) and forward corner
taps to `_hg_click_cb`. Window logic lives in `vesper/win_hourglass.py` (`_HourglassMixin`):
`_tick_hourglass` pushes frac + eases the flip spin each tick (only shows when a
session length is set), `toggle_hourglass` (View-menu toggle, persisted in store),
`_flip_hourglass` → new `controller.restart()` (resets the session clock without
stopping audio) + a 0.6 s smoothstep spin. Verified: painter strip across fracs +
mid-flip; integrated offscreen run shows it in the corner, the flip reset elapsed
24.2→0.0, view-switch moves the timer + clears the other, toggle hides it; thread
count stays at 2; selftest passes. `window.py` kept under 500 via the mixin split.

## Stories round — Histories +4 (Honey, Lighthouse, Violin, Perfume)
Authored four new Histories sleep-lectures via parallel subagents (each 7 sections,
~12 lines, section 1 a fact-free rest invitation, accurate content woven with calm,
sleep-closing on "Let yourself drift." / "Rest now."): `lectures_honey.py` (Forest
Wind), `lectures_lighthouse.py` (Ocean Waves), `lectures_violin.py` (Gentle Rain),
`lectures_perfume.py` (Forest Wind). Registered in `lectures._CATALOG` Histories
branch → **61 lectures across 8 branches**. Validated structure + ASCII; rebuilt the
stories DB (5,096 lines / 74,626 words); selftest passes.

## App round — enriched the four ambient scenes
Added a shared `vesper/scene_fx.py` (calm, seeded helpers: `Motes`, `Clouds`,
`ShootingStar`, `starfield`) and enriched every scene in `scenes.py`: **Orb** gains
drifting motes, soft exhale rings (emitted at each exhale onset) and a mint
"coherence" halo when the pace is ~5-7 breaths/min (new `bpm` in the scene ctx);
**Night** gains a deeper vertical gradient, slow drifting clouds and a rare faint
shooting star; **Wave** becomes a moonlit sea — sky gradient + faint stars, a moon
with a wavering reflection column on the water, foam dabs on the crests, and smoother
swells; **Ripple** gets tone-reactive ring colour + spacing (louder = brighter,
closer) and a central glow that pulses with the tone. Verified via per-scene PNGs and
a 64-tick offscreen session cycling all four scenes (thread count steady at 2);
selftest passes. `scenes.py` 320 lines, `scene_fx.py` 135 — both under 500.

## App round — five procedural ambiences
Added a new track kind `texture` (`breathsim/textures.py`, `TextureTrack` +
`build_track` dispatch + a `texture` field on `VoiceConfig`) with four event-driven
generators: **Campfire** (brown-noise roar/hiss + Poisson crackles & rare snaps),
**Singing Bowl** (a struck inharmonic resonator with a slow beat, every ~7-12 s),
**Wind Chimes** (gusts of 2-5 pentatonic strikes, panned), **Night Crickets** (4
detuned, panned crickets: tone × trill × chirp-gate over a low hush). Plus **Rain on
a Roof** as a warm brown-noise `NoiseTrack`. A shared `_Struck` resonator uses
absolute-time sinusoids (continuous phase, no accumulator) with a 2 ms attack. All
seeded deterministically; gains calibrated to ~0.75 peak at unit over a 150 s render
(Campfire 0.16 · Bowl 1.10 · Chimes 0.55 · Crickets 0.72 · Rain 0.14) and verified
≤ 0.80 over 300 s. 90 voices; they appear in the Relax/Sleep soundscape picker
(`voices.names(GROUP_NATURE)`); selftest passes; each set live in the engine without
error, thread count steady at 2. `textures.py` ~230 lines.

## Fix — storytelling audio crackle
Two causes, two fixes. (1) Narration plays each sentence via a separate `afplay`
subprocess; the Kokoro WAV had no edge fades, so CoreAudio starting/stopping it
clicked at sentence boundaries → added a 10 ms raised-cosine fade in/out to the
samples before `_write_wav` (`narration._speak_kokoro`). (2) The engine callback is
Python and was on a 1024-frame (~23 ms) buffer, so it could underrun when Kokoro's
ONNX synth saturated the CPU → bumped `AudioEngine` default `blocksize` to 2048
(~46 ms) for headroom (negligible latency for this app). selftest passes; engine
builds at block 2048; fade verified (0 at both edges → 1 mid).

## Parity — ported the 4 remaining authoring features
An audit showed the vendored core was a full superset of the legacy app, but four
GUI features had no Qt equivalent. Ported all four: **Voice Editor**
(`vesper/voice_editor.py` + `vesper/waveform.py` — full VoiceConfig form, live
wave+spectrum preview, Play/Randomize/Save custom voice, Both/In/Out phase),
**Pattern Editor** (`vesper/pattern_editor.py` — sliders + cycle/bpm read-out, save
custom patterns via `patterns.add_pattern` + `store`), **Presets Manager**
(`vesper/presets.py` — capture/apply full preset state + save/load/delete via
`store.presets_list`), and **Export Audio (WAV)** (`vesper/app_io.py` —
offline render of primary+ambience+effects to 16-bit WAV). Wired into File (Presets,
Export), Pattern (Pattern Editor) and Voice (Voice Editor) menus. (Voice/Pattern
editors built by parallel subagents; Presets/WAV + wiring done directly.) Integration
test passes (menu wiring, preset round-trip, WAV render, thread-stable 2->2); selftest
passes; all files < 500 lines. Optional remaining: word-on-exhale + downloaded sample
assets (procedural-first app, low priority).

## Stories round — The Living World +3 (Moths & Fireflies, Sloth, Coral Reefs)
Authored three new Living World sleep-lectures via parallel subagents (7 sections,
12 lines each, section 1 fact-free, accurate content woven with calm, sleep-closing):
`lectures_moths.py` (Forest Wind), `lectures_sloth.py` (Gentle Rain), `lectures_coral.py`
(Ocean Waves). Registered in the Living World branch → **64 lectures / 8 branches**.
Validated structure + ASCII; DB rebuilt (5,348 lines / 77,698 words); selftest passes.

## Polish — README + screenshots, and a cartoon-cat fallback face
Rewrote README around rendered screenshots (full window in Sleep + Meditate, the four
scenes, the avatar, the cat) under `docs/images/`. Fixed the last "Breathing Sim"
strings (panel title, About, `__init__` docstring) -> "Vesper".
New `vesper/cat.py` (`CatFace`): a hand-drawn **2D cartoon cat** that breathes, blinks,
twitches its ears, wanders its pupils and opens its mouth to talk — the fallback face
when faceView isn't installed. `face.py` now imports faceView in a try/except
(`_HAVE_FACEVIEW`); when absent (or `VESPER_FACE=cat`) it skips the GPU worker and paints
the cat from the same per-frame state. Verified: forced cat mode renders (talking +
quiet), default 3D mode still thread-stable (2->2), selftest passes.

## App round — soundscape: richer cues + crossfade ducking + follow toggle
Extended `breathsim/sound_cues.py` to steer the bedtime soundscape toward the new
procedural ambiences — fire/hearth → Campfire, crickets/fireflies → Night Crickets,
bell/gong/singing-bowl → Singing Bowl, wind-chime → Wind Chimes, rain-on-roof/eaves →
Rain on a Roof, birds/forest → Forest Wind — with guards so "belly"/"remember"/
"chimney" don't false-trigger. In `window._apply_soundscape`, each cue crossfade now
**ducks the ambience to 0.5 and eases it back over 1.8 s** (smoothstep) using live
`engine.set_layer_level` (the user's slot level is left untouched), so a cue blooms in
rather than jumping. Added `set_soundscape_follow` + a **Sound ▸ Soundscape follows
story** menu toggle (default on); off holds the story's base ambience. Cue-mapping
unit checks + an offscreen Sleep duck/toggle run pass; selftest passes; threads 2->2.

## Feature — choose the cartoon cat instead of the 3D head (in-app)
Made the cat a runtime choice, not just an env/fallback. `face.py` now separates
`_faceview_ok` (is the 3D head usable) from `_show_cat` (current choice);
`set_use_cat(on)`/`uses_cat()`/`faceview_available()` switch live. The single render
worker is started whenever faceView is present but **idles while the cat is shown** (so
no wasted GPU), and `paintEvent` draws the cat or the 3D frame accordingly. Added
`window.set_face_cat` + a checkable **View ▸ Cartoon cat face** menu item (disabled, and
always-on, when faceView is absent), persisted in settings (`face_cat`). Verified:
toggling cat on/off at runtime swaps the face (rendered the full Sleep window on the
cat), default still starts on the 3D head, thread-stable (2->2), selftest passes.

## Cat — richer face + cat content + cat voices
Reviewed and overhauled the cartoon cat (`vesper/cat.py`): soft **tabby markings**
("M" forehead + body stripes), **cheek tufts**, a pale **chest blaze**; it now
**breathes** (a phase-tinted aura that swells, a widening/rising chest, pupils that
dilate on the in-breath), **smiles** (happy eye-squint + lifted mouth) and **talks**
with a wider-than-tall mouth (tongue + lower lip), perked ears and lifted whiskers;
nose highlight, philtrum, curved whiskers. Examined render grids before/after.
Added cat **content**: a new **"Purr"** procedural ambience (`textures._Purr` — a
warm ~26 Hz rumble swelling with the breath; calibrated gain 0.18), a **"The Cat"**
sleep-lecture (Living World, narrated over the Purr) -> **65 lectures**, and a
**cat/purr sound cue**. selftest passes; DB rebuilt (5,433 lines).
Then made cat sounds **selectable voices**: a new **"Cat"** voice group
(`breathsim/voices_cat.py`) with **Cat Breath** (airflow), **Cat Sigh** + **Meow**
(both gated to the out-breath via `env="exhale"` — the cat answers each exhale; meow
is a vocal `ee`->`oh` glide with an up-down pitch arc) and **Cat Purr** (the purr
texture). Wired `GROUP_CAT` into the voice menus + the panel voice card; gains
calibrated. 95 voices; each plays live, thread-stable, selftest passes.

## App round — face naturalism (both faces)
`face.set_state` is now the single place for naturalistic motion: a slow gaze drift
plus rare micro-**saccades** (quick darts, rescheduled randomly); a rare
**settling-sigh** and **swallow** as one-shot bumps (`_gesture` helper -> a head dip +
soft mouth part); **flatter affect** as the session winds down (gaze, saccade size,
smile and brow all scaled by `calm = 1 - 0.6*prog`, lids already grow heavy); and a
gentle **head-cock on curious lines** (driven by `brow` -> a yaw offset on the 3D head,
a true painter roll on the cat). Gaze + tilt are passed through `_cat_state` so the cat
shares the same life (its eyes use the shared gaze; FaceParams has no roll, so the head
cocks via yaw). Verified: 3D head + cat both render (PNGs), >=40-tick offscreen sessions
thread-stable (2->2), selftest passes.

## Stories round — Earth & Sea +3 (Clouds & Weather, Caves & the Underground, The Tides)
Authored three new Earth & Sea sleep-lectures via parallel subagents (7 sections, 12-13
lines, section 1 fact-free, accurate, sleep-closing): `lectures_clouds.py` (Forest Wind),
`lectures_caves.py` (Brown Noise), `lectures_tides.py` (Ocean Waves) — the tide framed as
a slow breath to follow. Registered in the Earth & Sea branch → **68 lectures / 8
branches**. Validated structure + ASCII; DB rebuilt (5,688 lines / 81,766 words);
selftest passes.

## App round — GPU face MSAA (smooth silhouette)
`face_gpu._ensure_fbo` now probes `ctx.max_samples` once and, when available, renders to
a **4x multisample** colour+depth renderbuffer FBO; `render()` resolves it to a
single-sample RGBA texture via `ctx.copy_framebuffer` before readback. Falls back to the
old single-sample texture FBO if MSAA is unavailable. The head silhouette and the lash
lines are now cleanly antialiased over the animated backgrounds (verified via a 4x
edge-zoom: soft gradient, no staircase). Worker thread + transparent RGBA output
unchanged; default 3D path thread-stable (2->2); cat path untouched; selftest passes.

## App round — Sing pitch scoring/glow + Meditate guidance
Sing: the window now tracks a running **% time-in-tune** (frames where the sung pitch is
within 30 cents of the target, while voiced) reset on each guide start; the PitchScene
draws a soft green **in-tune glow** frame and shows the score top-right, and the in-tune
header carries through. Added 3 exercises to `vocaltrainer.SCALES` (Minor scale, Octave
siren, Sixth stretch) — they appear automatically in the Sing card. Meditate: a new
**Guidance** card (Off / Focused attention / Open monitoring) -> `set_meditation_guidance`;
the window feeds a slow rotating cue (~every 22 s) into the scene `hint`, shown softly
under the orb without hiding the breath count. Verified via PitchScene + orb renders and
a 50-tick offscreen Meditate session (cues rotate, thread-stable 2->2); selftest passes.

## Stories round — Ideas & Wonders +3 (Infinity, Symmetry, The Calendar)
Authored three new Ideas & Wonders sleep-lectures via parallel subagents (7 sections,
12-13 lines, fact-free section 1, accurate, sleep-closing): `lectures_infinity.py` (Brown
Noise — the endless), `lectures_symmetry.py` (Pink Noise — balance, Noether), and
`lectures_calendar.py` (Forest Wind — sun/moon, leap days, Julian/Gregorian). Registered
in the Ideas & Wonders branch → **71 lectures / 8 branches**. Validated structure +
ASCII; DB rebuilt (5,942 lines / 84,730 words); selftest passes.

## Stories round — new branch Ancient Roads & Walls (Great Wall, Appian Way, Hadrian's Wall, Inca Roads)
Added a 25th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate history, ASCII, sleep-closing): `lectures_greatwall.py` (The Great Wall, Wind in Pines -
many walls over 2,000+ years, beacon-fire relays, the recent Ming brick stretches vs older rammed
earth, and the honest "no, it cannot be seen from the Moon"), `lectures_appianway.py` (The Appian
Way, Night Crickets - Rome's "queen of roads" begun by Appius Claudius, its layered surviving
paving, roadside tombs and umbrella pines), `lectures_hadrianswall.py` (Hadrian's Wall, Forest Wind -
the coast-to-coast Roman frontier in northern Britain, forts and milecastles, and the Vindolanda
wooden tablets with their small human voices - a birthday invitation, a request for warm socks), and
`lectures_incaroads.py` (The Inca Roads, Mountain Stream - the Qhapaq Nan across the Andes built
without wheel/horse/iron, grass suspension bridges still rebuilt by hand, chasqui relay runners, the
quipu, tambo rest-houses). Distinct from the existing Silk/Spice Road lectures. New branch in
`_CATALOG` -> **145 lectures / 25 branches**. Validated all four (7 sections, 12-13 lines, pure
ASCII, no NAME collisions); `selftest.py` passes (148 voices); DB rebuilt (12,348 lines / 194,754
words / 5 scenes). The `units()` stream renders each (e.g. The Great Wall = 109 units).

## App round — gentle Meditate orb enrichment (ambient vignette + floor reflection)
Deepened `vesper/scenes.OrbScene` (the Meditate breath orb) with two subtle, low-contrast touches
behind the orb, both driven by the existing `anim_t` / volume / phase (no new state, no API change):
(1) a faint **phase-hue ambient vignette** -- a large radial gradient centred on the orb from a
lightly hue-tinted BG out to transparent, its alpha breathing with the breath volume, so the dark
field gently glows with the inhale/hold/exhale colour; (2) a soft **floor-reflection bloom** -- a
flattened radial glow drawn just below the orb, as if it rests on still water. Both sit behind the
existing exhale rings, glow, motes, coherence halo, travelling guide dot and the phase/session
progress arcs, which are all untouched, so the scene stays clean and uncluttered. `scenes.py` stays
466 lines (<500), so no split was needed. Verified: `selftest.py` passes (141 lectures / 24
branches); offscreen both faces -- in Meditate with the orb scene the viz renders at 564x557 to
non-empty PNGs (~70 KB) that **differ frame-to-frame** (the breathing orb, drifting motes and the
travelling guide dot), thread-stable.

## App round — soundscape preset save/recall (light sound-only mixes)
Let the user save a named mix of just the sound layers and recall it in one tap -- distinct from the
full Presets system (which also captures pattern/voice/persona/scene). `breathsim/store` gains
`soundscapes()` / `soundscape_names()` / `save_soundscape(name, mix)` / `get_soundscape` /
`delete_soundscape` (a `soundscapes.json` dict, mirroring favourites/courses). `vesper/soundscape_presets`
(55 lines) holds `capture(win)` -> a plain dict of the ambience voice + level, the effect voice +
level, master volume, and the spatial / auto-rotate flags, and `apply(win, mix)` which sets them back
through the normal setters (`set_ambience` / `set_slot_level` / `set_effect` / `set_volume` /
`set_spatial` / `set_ambience_rotate`) and **skips any voice no longer in the registry** (so an old
mix referencing a removed bed degrades gracefully, leaving the current one). The app gains
`save_soundscape` / `recall_soundscape` / `delete_soundscape`; the Relax/Sleep soundscape card shows a
saved-mixes combo (recall on pick) plus **Save current...** (a name prompt) and **Delete**, rebuilding
the workspace to refresh the list. Honest framing: it just stores names + levels. Verified:
`selftest.py` passes (141 lectures / 24 branches); the store layer is round-trip unit-tested
(save/list/get/delete via a temp `BREATHSIM_HOME`); offscreen both faces -- saving a distinctive mix
(Gentle Rain @ 0.55, rotate off), changing it (Ocean Waves @ 0.9, rotate on), then recalling restores
the ambience, level and flags, and an unknown-voice mix is tolerated (leaves the current bed),
thread-stable.

## Stories round — new branch Volcanoes & Islands (Iceland, Hawaii, Krakatoa, Galapagos)
Added a 24th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate geology/ecology/history, ASCII, sleep-closing): `lectures_iceland.py` (Iceland, Mountain
Stream - the land of fire and ice on the mid-Atlantic ridge slowly splitting, geothermal heat and
the word "geyser" from Geysir, glaciers and the aurora, the thousand-year Althing),
`lectures_hawaii.py` (The Hawaiian Islands, Ocean Waves - a hotspot building the chain as the Pacific
plate drifts, Mauna Kea taller than Everest from the sea floor, Polynesian voyagers navigating by
stars/swells/birds, life arriving and blooming into endemic forms), `lectures_krakatoa.py` (Krakatoa,
Distant Thunder - the 1883 eruption told **gently and with quiet awe**, the sound heard thousands of
miles off, the world's reddened sunsets, then the patient return of life and the new island Anak
Krakatau, leaning into renewal), and `lectures_galapagos.py` (The Galapagos, Night Crickets - young
volcanic islands on the equator, fearless animals with no large predators, century-old giant
tortoises and marine iguanas, Darwin's 1835 visit and the finches). Distinct from the existing
"Volcanoes and the Deep Earth". New branch in `_CATALOG` -> **141 lectures / 24 branches**. Validated
all four (7 sections, 12-13 lines, pure ASCII, no NAME collisions); `selftest.py` passes (148
voices); DB rebuilt (11,999 lines / 188,664 words / 5 scenes). The `units()` stream renders each
(e.g. Iceland = 109 units).

## App round — richer Chant ripple scene (water sheen + interference ripples)
Deepened `vesper/scenes.RippleScene` (used in Chant & Sing) with two gentle, low-contrast touches
layered onto the existing breath-spawned expanding rings and breath-pulsing central glow, both
driven by the existing `anim_t` / volume / phase context (no new state): (1) a **still-water radial
sheen** -- a large soft radial gradient centred on the ripple origin, from a faintly-tinted
RIPPLE_BG out to transparent, whose tint **drifts with the current breath phase hue** so the pool
quietly changes colour as the breath moves through inhale/hold/exhale; (2) a faint **companion
ripple** drawn just inside each expanding ring (at ~0.82 of its radius, alpha fading as the ring
ages) for an interference-like richness. Both respect the theme palette and never strobe. The
PitchScene and chant timing are untouched. `scenes.py` stays 449 lines (<500), so no split was
needed. Verified: `selftest.py` passes (137 lectures / 23 branches); offscreen both faces -- in
Chant with the ripple scene the viz renders at 564x557 to non-empty PNGs (~47-54 KB) that **differ
frame-to-frame** (expanding rings + the hue-drifting sheen), thread-stable.

## App round — voice loudness-consistency audit (measure, no rebalance needed)
Added `tools/loudness.py` (65 lines, read-only): renders each voice in a group (default GROUP_NATURE,
the ambience beds the soundscape switches between) for a fixed 12 s at a steady breath pattern and
reports **peak + rms**, sorted, with each bed's rms as a multiple of the group median and a LOUD/quiet
flag for outliers beyond 2x / 0.4x. It changes nothing -- it just measures, so the numbers are
auditable (`python -m tools.loudness [GROUP]`). Findings on the **21** ambience beds: median rms
0.1201, and every bed sits within **0.64x-1.36x** of it (quietest Forest Wind 0.0765, loudest Whale
Song 0.1638), with all peaks <= 0.752 -- i.e. they are already well matched, **no jarring outliers**.
Per the careful brief (voice gains are calibrated), the honest outcome is to change **no gains**: the
beds are consistent as they stand. Verified: `selftest.py` passes (137 lectures / 23 branches, all
peaks <= 1.0) and is unchanged by this round (no synthesis edits); offscreen both faces tick a Relax
session thread-stable. The tool stays available for future audits (e.g. after adding beds, or to
check GROUP_MUSIC/BELLS/etc by passing the group name).

## App round — ambience auto-rotate (slowly cycle calm beds)
Added an opt-in mode that lets the soundscape gently evolve over a long session instead of looping
one bed. `breathsim/ambrotate.py` (pure + testable): `next_ambience(beds, elapsed, period=360)` ->
`beds[(elapsed // period) % n]`, deterministic, wrapping, and tolerant of an empty/single list, plus
a curated `BEDS` list of calm GROUP_NATURE beds (Ocean Waves / Gentle Rain / Forest Wind / Mountain
Stream / Night Crickets / Soft Rainstorm). `window._apply_ambience_rotate` crossfades the ambience
slot to that bed (filtered to ones in the registry) via the **existing** gain-ramped
`engine.set_voice(..., "ambience", fade=3.0)`, only firing when the target differs (so it doesn't
re-trigger each frame). It is driven from `_tick` off `controller.elapsed()` (no new clock), guarded
`if self._amb_rotate and not self._story_scene` so it is **suppressed while the Sleep storyteller is
active** and never fights the story-driven soundscape cues. `set_ambience_rotate(on)` toggles it; off
by default, persisted as `ambience_rotate` and restored on launch; surfaced in the Relax/Sleep
soundscape card (a checkbox) and **Sound > Auto-rotate ambience**. Honest framing: it just rotates
the bed. Verified: `selftest.py` passes (137 lectures / 23 branches); `next_ambience` unit-tested
(period boundaries, wrap-around, single bed, empty -> None, negative clamp); offscreen both faces --
with rotation on in Relax the ambience advances Ocean Waves -> Gentle Rain -> Forest Wind across
periods, holds stable once toggled off, and is suppressed when a Sleep story is armed, thread-stable.

## Stories round — new branch Great Train Journeys (Trans-Siberian, Orient Express, Darjeeling, Ghan)
Added a 23rd lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate geography/history, ASCII, sleep-closing), leaning into the soothing rhythm of the rails:
`lectures_transsiberian.py` (The Trans-Siberian, Wind in Pines - the world's longest railway,
Moscow to Vladivostok, ~9,000 km / a week / eight time zones, days through the taiga, around Lake
Baikal, samovar tea and the clicking rails as a lullaby), `lectures_orientexpress.py` (The Orient
Express, Gentle Rain - the 1880s Paris-to-Constantinople luxury sleeper, wood-panelled cars and
white-linen dining, Agatha Christie's novel framed honestly as fiction, rain on the dark window),
`lectures_darjeeling.py` (The Darjeeling Railway, Mountain Stream - the narrow-gauge "toy train"
climbing by loops and zig-zags to Ghum, a century-old World Heritage line, tea gardens and distant
Kanchenjunga), and `lectures_ghan.py` (The Ghan, Night Crickets - Adelaide to Darwin across the red
centre, named for the Afghan cameleers, Alice Springs, Aboriginal land noted respectfully, star-thick
desert nights). Distinct from the existing general "The Railway". New branch in `_CATALOG` -> **137
lectures / 23 branches**. Validated all four (7 sections, 12-13 lines, pure ASCII, no NAME
collisions); `selftest.py` passes (148 voices); DB rebuilt (11,648 lines / 182,733 words / 5 scenes).
The `units()` stream renders each (e.g. The Trans-Siberian = 110 units).

## App round — breath-rate (pace) insight in Stats
Surfaced the breathing pace a user tends to practise at, computed honestly from what is logged.
`store.log_session(minutes, bpm=None)` now records the session's breaths-per-minute into a capped
`bpm` list in `history.json` (added to `_HIST_DEFAULT`; older histories without it just skip the
line). `window._log_practice` computes the bpm from the live pattern's cycle (`60 / (inhale +
hold_full + exhale + hold_empty)`) and passes it when logging. `breathsim/insights` gains pure
`avg_bpm(history)` and `pace_line(history)` -> "You tend to breathe around 6 a minute - a calm,
resonant pace" when the average sits in the ~4-7/min resonance/coherence sweet spot, or a plain
statement otherwise; `insights.lines()` appends it (so it shows in the Practice Stats dialog via
`stats_heatmap`), and there is no pace line at all without data. Honest framing: descriptive, with
resonance noted gently, not prescribed. Verified: `selftest.py` passes (133 lectures / 22 branches);
the helpers are unit-tested (no-data -> None, average of logged bpms, the resonance note for ~6/min
vs none for ~10/min, and `lines()` inclusion); offscreen both faces -- two logged Meditate sits
record bpm (5.45 each -> avg 5.5) and the Stats widget builds with the pace line present,
thread-stable.

## App round — sleep-onset "lights out" auto-dim
Deepened the tail of the Sleep wind-down so the screen eases toward near-dark as you fall asleep.
Added `vesper/sleepdim.py` (pure + testable): `sleep_dim(prog, knee=0.85, floor=0.55)` returns the
window opacity for a Sleep session at progress *prog* -- it is **exactly the old curve** (1 - 0.3*prog)
below the knee, then **smoothsteps to the floor** past it, joined continuously at the knee (0.745) so
there is no jump; it bottoms out around 0.55 by session end and is clamped so it never goes fully
black/unusable. `window._tick`'s Sleep branch now uses `sleepdim.sleep_dim(prog)` for `op` (the
non-Sleep clock-dim branch is unchanged); the launch intro-fade still multiplies on top and the warm
overlay is untouched, so they don't fight. It is fully **reversible** -- the opacity is recomputed
every frame from prog, so a fresh Start, Reset, or leaving Sleep returns to normal brightness. Honest
framing: a gentle visual dim, not a real power-off. Verified: `selftest.py` passes (133 lectures / 22
branches); `sleep_dim` unit-tested (1.0 at 0, 0.85 at 0.5 matching the old curve, continuous 0.745 at
the knee, deeper than linear past it, monotonic non-increasing, never below the 0.55 floor); offscreen
both faces -- the recorded opacity is ~0.85 mid-session (prog 0.5) and eases to ~0.57 deep in the
wind-down (prog 0.97), and returns to ~0.96 after a Reset + Meditate, thread-stable.

## Stories round — new branch Wonders of the Ancient World (Pyramid, Hanging Gardens, Colossus, Artemis)
Added a 22nd lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate history with legend framed honestly, ASCII, sleep-closing): `lectures_pyramid.py` (The Great
Pyramid, Fan (White Noise) - oldest and only surviving wonder, Khufu's ~4,500-year-old tomb, tallest
on Earth for 3,500+ years, millions of fitted blocks, the honest "we are not sure how" with the
fed-and-housed-workers correction over the slave myth, compass alignment, the lost gleaming casing),
`lectures_babylon.py` (The Hanging Gardens, Mountain Stream - the rising green terraces by the
Euphrates and Nebuchadnezzar's homesick queen, framed with the **honest core mystery** that this is
the one wonder whose very existence is unproven -- no trace found, Babylon's own scribes near-silent,
all accounts second-hand, perhaps confused with Nineveh), `lectures_colossus.py` (The Colossus of
Rhodes, Ocean Waves - the giant bronze Helios over the harbour, paid for with the enemy's war
machines, Statue-of-Liberty height, the harbour-straddling pose named honestly as later legend,
felled at the knees by an earthquake, the word "colossus"), and `lectures_artemis.py` (The Temple of
Artemis, Wind Chimes - the vast forest of marble columns at Ephesus, rebuilt grander after a flood
and a fire, Antipater's most-awe-inspiring wonder, slow ruin to a single column). Complements the
existing Pharos + Library of Alexandria lectures. New branch in `_CATALOG` -> **133 lectures / 22
branches**. Validated all four (7 sections, 12-13 lines, pure ASCII, no NAME collisions); `selftest.py`
passes (148 voices); DB rebuilt (11,294 lines / 176,512 words / 5 scenes). The `units()` stream
renders each (e.g. The Great Pyramid = 111 units).

## App round — "tonight's pick" one-tap random bedtime lecture
Added a one-tap "surprise me" for the storyteller. `breathsim/tonight.py` (22 lines, pure):
`pick(names, recent, rng)` returns a random name from *names*, preferring one not in *recent*, falling
back to the full list when all are recent, and returning None on empty -- deterministic with a seeded
`random.Random`. `breathsim/store` gains `recent_picks()` / `push_recent_pick(name, keep=5)`
(`recent_picks.json`, most-recent-last, capped) so a pick doesn't repeat night to night.
`app.tonights_pick()` picks from `stories.lecture_names()` avoiding the recent list, records it,
switches to **Sleep** (only if not already there), arms it via the existing `set_story(name)`
(which sets `_story_scene` + the matching ambience) and calls `_ensure_running()` to begin -- reusing
the normal story-start plumbing, no duplication. Surfaced as a **"Surprise me - tonight's pick"**
button on the Sleep story card and a **Sessions > Tonight's pick (random story)** menu action. Honest
framing: it just picks a lecture at random. Verified: `selftest.py` passes (129 lectures / 21
branches); `pick` unit-tested (deterministic with a seed, avoids the recent list, falls back when all
recent, None on empty, always valid); offscreen both faces -- the action switches to Sleep, arms a
real lecture (e.g. "Shangri-La"), starts the session, and records the pick in `recent_picks`, with no
blocking dialog, thread-stable.

## App round — richer Relax wave scene (horizon glow + moonlight glint)
Deepened `vesper/scenes.WaveScene` with two gentle, low-contrast touches layered onto the existing
swells / stars / moon / shimmer / foam, both driven by the existing `anim_t` (no new clock) and
respecting the theme palette + warm/dim overlay: (1) a **horizon glow** -- a soft 26 px
linear-gradient band just above the waterline (`base`) in a water+moon tint, fading to nothing
upward (alpha tops at ~0.16), so sky and sea meet in a calm light; (2) a **moonlight glint column**
-- a vertical MOON gradient drawn down the sea directly below the moon, fading out toward the bottom,
its width **breathing subtly with the breath volume** (`mr*2.2*(0.85 + 0.4*vol)`), with the existing
shimmer ellipses riding on top so the moon now lays a coherent path of light on the water. `scenes.py`
stays 440 lines (<500), so no split was needed. Verified: `selftest.py` passes (129 lectures / 21
branches); offscreen both faces -- in Relax with the wave scene the viz renders at 564x557 to
non-empty PNGs (~25 KB) that **differ frame-to-frame** (moving swells, shimmer and the breathing
glint), thread-stable.

## Stories round — new branch Great Lakes & Inland Seas (Baikal, Caspian, Dead Sea, Titicaca)
Added a 21st lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate geography/ecology/history, ASCII, sleep-closing): `lectures_baikal.py` (Lake Baikal,
Mountain Stream - the deepest and oldest lake, ~a fifth of the world's unfrozen fresh water, ~25
million years old, glass-clear singing winter ice, the endemic nerpa freshwater seal, a slowly
widening rift), `lectures_caspian.py` (The Caspian Sea, Ocean Waves - the largest enclosed water /
really a lake, slightly salty, five countries, a remnant ancient sea, the Volga in but nothing out,
below ocean level, sturgeon and the Caspian seal, Silk Road shores), `lectures_deadsea.py` (The Dead
Sea, Brown Noise - the lowest land on Earth, so salty you float and almost nothing lives, the Jordan
in but only evaporation out, the rift valley, the Dead Sea Scrolls and ancient Jericho), and
`lectures_titicaca.py` (Lake Titicaca, Wind Chimes - the highest large navigable lake in the Andes,
the Uros people's floating totora-reed islands, the Inca origin tradition framed honestly as belief,
underwater offerings). New branch in `_CATALOG` -> **129 lectures / 21 branches**. Validated all four
(7 sections, 12-13 lines, pure ASCII, no NAME collisions); `selftest.py` passes (148 voices); DB
rebuilt (10,943 lines / 170,641 words / 5 scenes). The `units()` stream renders each (e.g. Lake
Baikal = 106 units).

## App round — session-end "well done" moment (kind closing line)
Added `breathsim/welldone.py` (pure + testable): `message(minutes, streak)` turns a finished sit's
length + current streak into one short, warm, non-clinical line -- "Session complete - 12 minutes. 3
days in a row. Be well." -- with singular/plural handling, the streak clause only when >=2, and
`None` for a too-short sit. `window._log_practice` (the single >=30 s "a real sit happened" hook,
already called on pause / reset / auto-finish / sleep-timer) now sets `self._closing_msg` once via
`welldone.message(elapsed, store.streak())` -- but **only when `current_mode != "Sleep"`**, so a
sleeper is never jarred. `_update_status` shows the line in the **idle status bar** (taking priority
over the launch hint) until the next fresh Start clears it; it is fully non-modal -- no dialog, no
sound. Honest framing: it just acknowledges a finished sit. Verified: `selftest.py` passes (125
lectures / 20 branches); `message` unit-tested (short -> None, 1 minute singular, 12 minutes,
with-streak, streak<2 omitted); offscreen both faces -- finishing a real Meditate session (driven
past its length) sets and shows the line once with no blocking dialog, a fresh Start clears it, and a
finished **Sleep** session leaves it silent (None), thread-stable.

## App round — calmer first-frame fade-in on launch
Added `vesper/introfade.py` (pure + testable): `intro_opacity(elapsed, duration=1.1, floor=0.0)`
eases a window-opacity multiplier from 0 up to 1.0 over the first ~1.1 s with a smoothstep, then
returns 1.0 forever after. `window._tick` was refactored so the three opacity branches (Sunrise
wake, Sleep dim, clock-warm day) now compute a single normal `op` value instead of each calling
`setWindowOpacity` directly; `op` is then multiplied by the intro factor (keyed off `self._anim_t`),
recorded as `self._win_op`, and applied once. So the app arrives softly on launch and the intro then
**yields to** the normal opacity logic rather than fighting it (the Sleep wind-down dim, the
clock-aware night dim and the Sunrise brighten all still set the base; the intro only scales it for
the first second). Offscreen, `setWindowOpacity` remains a harmless no-op. Honest framing: a visual
nicety. Verified: `selftest.py` passes (125 lectures / 20 branches); `intro_opacity` unit-tested
(floor 0 at t=0, 1.0 past the duration, mid 0.5, monotonic non-decreasing 0->1); offscreen both faces
-- the recorded opacity starts well below 1 during the intro (~0.01 at the first frames) and reaches
the normal value (~0.96 daytime) after it completes, and a deep Sleep session still dims it (~0.73),
thread-stable.

## Stories round — new branch Deserts of the World (Sahara, Gobi, Atacama, Namib)
Added a 20th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate geography/ecology/history, ASCII, sleep-closing): `lectures_sahara.py` (The Sahara, Fan
(White Noise) - largest hot desert, more rock/gravel than dune, cold nights, the green "African
Humid Period" and orbital wobble, dust fertilising the Amazon, salt-and-gold caravans and the
Tuareg, ancient groundwater oases), `lectures_gobi.py` (The Gobi, Brown Noise - a cold high desert
across Mongolia/China, the Himalaya rain shadow, the first dinosaur eggs in its red cliffs, the Silk
Road's edge and Bactrian camels, the rare Gobi bear, felt-tent herders under crowding stars),
`lectures_atacama.py` (The Atacama, Wind Chimes - the driest non-polar desert, rain-free stations,
the darkest clearest skies and its great observatories, Mars-rover testing, fog-drinking lichens
and the rare desert bloom, flamingo salt lagoons), and `lectures_namib.py` (The Namib, Ocean Waves -
the oldest desert meeting a cold sea, the towering red Sossusvlei dunes, life drinking the coastal
fog (the fog-basking beetles), the millennia-old welwitschia, Deadvlei's un-rotting trees and buried
shipwrecks). New branch in `_CATALOG` -> **125 lectures / 20 branches**. Validated all four (7
sections, 12-13 lines, pure ASCII, no NAME collisions); `selftest.py` passes (148 voices); DB
rebuilt (10,591 lines / 164,750 words / 5 scenes). The `units()` stream renders each (e.g. The
Sahara = 110 units).

## App round — keyboard-shortcut help overlay (? cheatsheet)
Added a discoverable cheatsheet of the real keyboard shortcuts. `vesper/shortcuts.py` now defines a
single `SHORTCUTS` list of (key, description) pairs right next to `bind()`, so the on-screen list
can never drift from what is actually wired: Space (play/pause), R (reset), V (face/scene), F
(fullscreen), Z (Focus/Zen), Esc (exit fullscreen/Focus), plus the new **"?"** and the Ctrl+S /
Ctrl+Q menu accelerators. `bind()` now also wires **"?"** to open the sheet. `dialogs.open_shortcuts`
builds a calm, theme-styled dialog (an accent-coloured key column beside its description in a
QGridLayout) and is **modeless** (`show()`, never a blocking `exec()`) with `WindowModal` modality,
so "?" and headless tests never trap or hang; a ref is kept on the window so it isn't GC'd. Surfaced
in **Help > Keyboard Shortcuts** too. shortcuts<->dialogs imports are both lazy to avoid a cycle.
Honest framing: it just lists the bindings. Verified: `selftest.py` passes (121 lectures / 19
branches); `SHORTCUTS` unit-tested (non-empty, all (str,str), includes Space/?/Esc); offscreen both
faces -- `open_shortcuts` builds and shows without a blocking exec, every key and description from
`SHORTCUTS` is present in the dialog's labels, building the window auto-pops no blocking dialog,
thread-stable.

## App round — per-voice favourites (star/pin voices for quick access)
Added favourite-voice persistence + a Voice-menu surface. `breathsim/store` gains `favourites()`
(reads `favourites.json`, de-duplicated and order-preserving), `is_favourite(name)` and
`toggle_favourite(name)` (star/unstar; empty-name no-op) -- mirroring the existing courses/history
JSON persistence, no new machinery. `app.toggle_favourite_voice()` stars/unstars the current inhale
voice (`engine.voice_a`), reports it in the status bar and rebuilds the menu. `vesper/menus._voice`
now opens with a **Favourites** submenu -- quick `set_voice_a` over the starred voices, filtered to
those that still exist in the registry (so a removed/renamed voice is silently dropped), with a
friendly disabled placeholder when there are none -- plus a **Star/Unstar "<voice>"** action for the
current inhale voice. Honest framing: a convenience shortcut, nothing more. Verified: `selftest.py`
passes (121 lectures / 19 branches); the helpers are unit-tested (add then remove, `is_favourite`,
empty no-op, external-dupes de-duplicated on read, persistence round-trip via a temp
`BREATHSIM_HOME`); offscreen both faces -- starring the current voice persists and appears in the
menu's favourites list, `menus.build` succeeds with favourites both present and empty, selecting a
favourite sets the inhale voice, and unstarring round-trips, thread-stable.

## Stories round — new branch Great Forests (Taiga, Black Forest, Daintree, Cloud Forest)
Added a 19th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate ecology/history/culture, ASCII, sleep-closing): `lectures_taiga.py` (The Taiga, Forest Wind
- the largest land forest, the boreal belt across Canada/Scandinavia/Siberia, snow-shedding conifers,
the deciduous larch, cold-adapted wildlife, carbon locked in cold peat), `lectures_blackforest.py`
(The Black Forest, Gentle Rain - dark fir hills of south-west Germany, the source of the Danube,
cuckoo clocks and winter woodcraft, the brothers Grimm's tales framed honestly as folklore, spa
towns and the famous cake), `lectures_daintree.py` (The Daintree, Soft Rainstorm - one of the oldest
rainforests, a living remnant of Gondwana older than the Amazon, rainforest meeting the reef, the
cassowary as seed-spreader, Kuku Yalanji custodianship for thousands of years, ancient flowering
plants), and `lectures_cloudforest.py` (The Cloud Forest, Mountain Stream - mountain forest living
inside the clouds, drinking water from the air, epiphytes/moss/orchids, Monteverde and the Andes,
the quetzal and bromeliad pools, watering the lands below). New branch in `_CATALOG` -> **121
lectures / 19 branches**. Validated all four (7 sections, 12-13 lines, pure ASCII, no NAME
collisions; distinct from the existing Redwoods/Plants/Amazon/Bamboo); `selftest.py` passes (148
voices); DB rebuilt (10,239 lines / 158,738 words / 5 scenes). The `units()` stream renders each
(e.g. The Taiga = 109 units).

## App round — breathing-pattern visual guide (phase bar in the pattern card)
Added `vesper/pattern_bar.py` (88 lines): a compact diagram of the current pattern's phases. Pure
`segments(pattern)` turns a `BreathPattern`'s four durations (inhale / hold_full / exhale /
hold_empty) into the **non-zero** phases with their seconds and width fractions; `PatternBar`
(QWidget) paints them as a proportional bar, each segment tinted with the theme's per-phase hue
(`theme.phase_hue`) and labelled with its duration, and softly **highlights the live phase** (a
glow + brighter label) while a session runs. It is change-guarded (a signature on the pattern +
phase) so it only repaints when something actually changes. Wired into `_card_pattern` (combo now
routes through `_on_pattern`, which refreshes the bar), and refreshed from the panel `sync()` (e.g.
when the pace slider or a guided stage changes the pattern) and each frame in `tick()` via
`bar.refresh(controller)`. Honest framing: it just visualises the numbers. Verified: `selftest.py`
passes (117 lectures / 18 branches); `segments` unit-tested (4-7-8 -> 3 segments with fractions
4/19, 7/19, 8/19; zero holds -> 2 equal; box 4-4-4-4 -> 4 equal); offscreen both faces -- the bar is
present in the pattern card, switching to a 4-7-8 pattern updates it to 3 segments and renders to a
non-empty PNG, the live phase highlights ("inhale") while running, thread-stable.

## App round — richer Sleep night scene (parallax stars, horizon glow, moon phase)
Deepened `vesper/scenes.NightScene` with three gentle, low-contrast additions, all driven by the
existing `anim_t` (no new clock) and kept dark/melatonin-friendly so they respect the Sleep + clock
warm/dim overlay: (1) a **far parallax star layer** -- 96 extra stars, smaller, dimmer and drifting
at half the speed of the near layer with a gentler twinkle, giving real depth; (2) a **faint horizon
glow** -- a very dim deep-indigo linear-gradient band over the lowest third of the sky, fading to
nothing upward (alpha tops out at ~0.28, never bright); (3) a **subtle moon crescent / phase** --
after the moon disc and halo, a sky-coloured disc (slightly larger than the moon) is drawn offset to
carve a soft terminator, and the offset drifts very slowly (`0.42 + 0.12*sin(t*0.01)` of the radius)
so the phase eases between gibbous and crescent over minutes. `scenes.py` stays at 430 lines (<500),
so no split was needed. Verified: `selftest.py` passes (117 lectures / 18 branches); offscreen both
faces -- in Sleep mode with the night scene, the viz renders at 564x557 to non-empty PNGs (~35 KB)
that **differ frame-to-frame** (drifting stars/clouds + the moving crescent), thread-stable.

## Stories round — new branch Birds of Myth (Crane, Raven, Swan, Owl)
Added an 18th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate natural history + folklore framed honestly as symbolism, ASCII, sleep-closing):
`lectures_crane.py` (The Crane, Mountain Stream - tall wetland birds, the courtship dance, faithful
pairs, high-mountain migration in bugling V-lines, the red-crowned/sandhill/whooping cranes, Japan's
thousand-year long-life symbol and the senbazuru paper cranes), `lectures_raven.py` (The Raven,
Forest Wind - the largest songbird, remarkable intelligence/play/mimicry, lifelong playful pairs,
the northern range, Norse Huginn and Muninn "Thought and Memory", Pacific-northwest Raven as
light-bringer, the Tower of London tradition), `lectures_swan.py` (The Swan, Gentle Rain - grace over
hidden paddling, heart-curve courtship and lasting pairs, cygnets riding the back, whooper/Bewick's
migration, the swan-song legend named as legend, the Ugly Duckling and Swan Lake), and
`lectures_owl.py` (The Owl, Night Crickets - night vision and far head-turning, silent fringed-feather
flight, offset-ear hearing and the facial disc, barn/tawny/great-horned/elf owls, Athena's owl as a
symbol of wisdom). New branch in `_CATALOG` -> **117 lectures / 18 branches**. Validated all four
(7 sections, 12-13 lines, pure ASCII, no NAME collisions; distinct from the existing "The Migrating
Birds"); `selftest.py` passes (148 voices); DB rebuilt (9,891 lines / 152,836 words / 5 scenes).
The storyteller `units()` stream renders each (e.g. The Owl = 109 units).

## App round — export / share a session summary (text + PNG card)
Added `breathsim/summary.py` (55 lines, pure + testable) and `vesper/session_export.py` (87 lines).
`summary.summary_lines(last, hist, today)` / `summary_text` build a few honest, friendly lines from
an optional last-session dict (`{minutes, mode}`) plus `store` history: a title, the date, "This sit:
N min of <mode>", "All time: N sessions, M min", the current streak, and a kind closing note -- with
a graceful new-user empty state and a short-sit guard (<0.5 min is dropped). `session_export`
provides `write_summary_txt` (plain .txt) and `save_summary_card` (a 600x360 themed PNG card drawn
with QPainter in the night palette: accent title, muted date/footer, the lines beneath) plus
`export_summary`/`save_card` menu wrappers that mirror `save_screenshot`/`export_wav` (save dialog,
status-bar report, never crash). Wired into **File > Export Session Summary... / Save Summary Card
(PNG)...**. Honest framing: it only summarises logged data, no claims. Verified: `selftest.py` passes
(113 lectures / 17 branches); the builder is unit-tested (new user empty state, short-sit guard, a
logged sit with streak, the closing line); offscreen both faces -- a simulated 2-min Meditate sit is
logged, then `write_summary_txt` writes a 163-byte .txt with the right lines and `save_summary_card`
writes a ~27 KB .png, thread-stable.

## App round — accessibility: global UI text-size setting
Added `vesper/fontscale.py` (41 lines, pure + testable): `OPTIONS` (Small / Normal / Large /
Extra-large -> 0.85 / 1.0 / 1.25 / 1.5), `scaled_css(css, scale)` (regex-multiplies only
`font-size: Npx` values, leaving paddings/borders/widths untouched so geometry stays stable), and
`label_for`/`scale_for`. `window.set_text_scale(scale)` applies it two ways so everything follows:
it scales the **Qt application font** (capturing the unscaled base point size once, in `_base_pt`,
so repeated changes don't drift) and re-applies the **theme stylesheet** scaled -- dialogs and the
menu bar inherit it via `win.styleSheet()`. Persisted as `font_scale` (saved in `closeEvent`,
restored in `_restore_settings`), surfaced via a **View > Text size** submenu (checkable, reflects
the current scale). Honest framing: a readability setting, nothing more. Verified: `selftest.py`
passes (113 lectures / 17 branches); `scaled_css` unit-tested (1.0 unchanged, 1.25 -> 13->16/15->19px
with padding/border preserved, 0.85 -> 11px) plus the label helpers; offscreen both faces -- each of
the four sizes scales the app font (base 9 pt -> 7.6 / 9 / 11.2 / 13.5) and the stylesheet body
(11 / 13 / 16 / 20 px), the choice persists (font_scale 1.25 round-trips), thread-stable.

## Stories round — new branch Great Mountains (Everest, Fuji, Kilimanjaro, Matterhorn)
Added a 17th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate geology/history/culture, ASCII, sleep-closing): `lectures_everest.py` (Everest, Brown Noise
- highest on Earth on the Nepal/Tibet border, the sacred names Sagarmatha / Chomolungma, the
India-into-Asia collision still lifting the range, sea fossils in the summit limestone, the death
zone, Tenzing Norgay and Hillary in 1953, the Sherpa), `lectures_fuji.py` (Mount Fuji, Wind Chimes -
Japan's highest, a near-perfect volcanic cone built layer on layer, long quiet since the early-1700s
Hoei eruption, revered in Shinto with centuries of pilgrims, Hokusai's Thirty-six Views, the sunrise
Goraiko), `lectures_kilimanjaro.py` (Kilimanjaro, Night Crickets - Africa's highest, free-standing
above the Tanzanian plain, three cones with Kibo/Uhuru "freedom", the climate-belt ascent from
rainforest to equatorial ice, the East African Rift, a walk-up needing only a slow pace), and
`lectures_matterhorn.py` (The Matterhorn, Mountain Stream - the glacier-carved "horn" on the
Swiss/Italian border above Zermatt, far-travelled African-side summit rock, Whymper's 1865 first
ascent and the tragedy on descent, alpenglow). New branch in `_CATALOG` -> **113 lectures / 17
branches**. Validated all four (7 sections, 12-13 lines, pure ASCII, no NAME collisions);
`selftest.py` passes (148 voices); DB rebuilt (9,540 lines / 146,876 words / 5 scenes). The
storyteller `units()` stream renders each (e.g. Everest = 111 units).

## App round — richer Stats insights (honest summaries from the existing logs)
Added `breathsim/insights.py` (115 lines, pure + testable): `average_minutes`, `busiest_weekday`
(by minutes, needs >=2 weekdays to be meaningful), `time_of_day` (morning/afternoon/evening/night
from an hour histogram, needs >=3 logged hours), `week_over_week` (this vs last 7 days via
`store.daily_minutes`), and `lines(hist, today)` which assembles a few kind one-liners (total
sessions/minutes, average sit, usual time of day, most regular weekday, week-over-week up/down) --
each skipped honestly when the data isn't there, so a brand-new user simply sees nothing. To support
time-of-day without overclaiming, `store.log_session` now also keeps an **hour histogram**
(`history["hours"]`, added to `_HIST_DEFAULT`); older histories lacking it just skip that one line.
The Stats widget (`vesper/stats_heatmap.build`) now appends these lines beneath the streak/heatmap
and above the mood-trend line. Honest framing: descriptive, never clinical. Verified: `selftest.py`
passes (109 lectures / 16 branches); the helpers are unit-tested (empty/new user -> [], averages,
evening time-of-day with the <3 guard, busiest weekday, week-over-week up, and a full 5-line set);
offscreen both faces -- two logged sits stamp the hour histogram, the Stats widget builds with the
insight lines present **without any blocking exec**, thread-stable.

## App round — sleep-timer auto-stop (gentle fade-out + pause after N minutes)
Added `vesper/sleeptimer.py` (50 lines, pure + testable): `fade_gain(armed_minutes, elapsed,
fade_seconds=30)` -> `(gain, done)` -- full volume before the mark, a slow linear ramp to 0 over the
fade once reached, then `done` (time to pause); plus `remaining_seconds`, `OPTIONS` (Off/15/30/45/60)
and `label_for`. The window keeps **no second clock**: `_tick` passes the session's elapsed-since-
armed into `fade_gain` each frame and eases the master volume down via the existing
`engine.set_master_volume` path (respecting mute), then on `done` stops the narrator and pauses
transport through the same route the session-finished path uses (and offers the after-mood check-in).
`set_sleep_timer(minutes)` arms it (counts from now); it is **off by default each launch** (not
persisted, so it never silently stops a future session) and the countdown restarts on a fresh Start
and on reset. Surfaced in the **Sleep wind-down card** (a combo) and a **Sound > Sleep timer**
submenu. Honest framing: it only fades + pauses, no claims. Verified: `selftest.py` passes (109
lectures / 16 branches); the pure helper is unit-tested (off / before-mark / at-mark / mid-fade=0.5 /
after=done / remaining / labels); offscreen both faces -- master holds at 0.8 before the mark, eases
to 0.4 at mid-fade (15 min + 15 s) while still running, then reaches 0.0 with transport paused and
the timer marked done after the fade, thread-stable.

## Stories round — new branch Great Rivers (Nile, Amazon, Ganges, Yangtze)
Added a 16th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate geography/history/culture, ASCII, sleep-closing): `lectures_nile.py` (The Nile, Night
Crickets - flows south-to-north to the Mediterranean, White + Blue Nile meeting at Khartoum, the
19th-c quest for the source, the yearly silt flood and Kemet "the black land", papyrus, the Aswan
High Dam), `lectures_amazon.py` (The Amazon, Soft Rainstorm - the greatest river by far by volume,
Andes snowmelt crossing a continent to the Atlantic, 1000+ tributaries and the largest rainforest,
wet-season flooding with fish among the trunks, pink dolphins, the mouth staining the sea brown),
`lectures_ganges.py` (The Ganges, Singing Bowl - the Gangotri glacier source, the fertile peopled
plains, Varanasi's ghats and the evening aarti of floating lamps, the Brahmaputra delta - religious
belief framed respectfully as Hindu tradition, not asserted as fact), and `lectures_yangtze.py` (The
Yangtze, Mountain Stream - longest in Asia, the Tibetan Plateau source, Chang Jiang "the long
river", the misty Three Gorges, cliff trackers, the finless porpoise and the lost baiji, the Three
Gorges Dam, old river poems). New branch in `_CATALOG` -> **109 lectures / 16 branches**. Validated
all four (7 sections, 12-13 lines, pure ASCII, no NAME collisions; distinct from the existing
lectures_water "A River to the Sea"); `selftest.py` passes (148 voices); DB rebuilt (9,195 lines /
140,997 words / 5 scenes). The storyteller `units()` stream renders each (e.g. The Nile = 108 units).

## App round — launch suggestion (a gentle, non-modal "what suits you now")
Added `vesper/suggest.py` (86 lines, pure + testable): `suggest(hour, history, courses_state, today)`
returns a `Suggestion(text, action, kind)`. Priority: an **in-progress multi-night course** is the
kindest hint and wins ("Pick up \"7 Nights to Sleep\" - Night 3 of 7"); otherwise a friendly
time-of-day mode (reusing `clocktheme.suggested_mode_for_hour`) coloured by the practice state -- a
fresh user ("New here? ... is a gentle place to start"), an active streak ("You are on a 3-day
streak"), or having already practised today. It reads nothing global (the hour/history/course-state
and `today` are all injectable), so it unit-tests cleanly. It lives in the GUI layer because the
mode mapping comes from `clocktheme` (a vesper module). Surfaced **gently**: `window` computes it
once at launch (guarded; never raises) into `self._launch_suggestion`, and `_update_status` shows it
in the **idle status bar** only while elapsed==0 and before the first Start; `toggle_transport` sets
`_started_once` so the hint retires on Start and never returns -- no popup, no nag. Honest framing: a
hint, not advice. Verified: `selftest.py` passes (105 lectures / 15 branches); the helper is
unit-tested across morning/night, fresh vs 3-day-streak vs practised-today vs in-progress vs
completed course; offscreen both faces -- the suggestion is produced on launch with **no** blocking
dialog, shown in the idle status bar, then replaced by the running display after Start, thread-stable.

## App round — multi-night courses (guided sequences over days)
Added `breathsim/courses.py` (`Course`/`Day`, 121 lines): an optional, gentle sequence of sessions
across days, each day **reusing an existing building block** -- a `programs` program or a mode -- plus
a one-line spoken intention (no new audio invented). Three courses ship: **7 Nights to Sleep** (7),
**Ten Days of Calm** (10), **Five Mornings to Energize** (5). `apply_day` dispatches via the normal
machinery (`start_session_mode` for a program day; `apply_mode` + `_ensure_running` for a mode day)
and announces the intention through the existing `SpeechCue`. Progress persists per course in
`store` (`courses.json`): `course_day` (next 0-based day), `advance_course(name,total)` (caps + a
`completed` flag + dated `done` log), `reset_course`. Advancing is **honest**: a day only counts when
a session actually completes, hooked into `window._log_practice` (the same >=30 s sit gate that logs
practice), then `_active_course` is cleared so it advances once. A **Sessions > Courses (multi-night)**
submenu lists each course with live progress ("Night 3/7" / "complete") + a Restart action; the app
gains `start_course_day`/`restart_course` and a `_active_course` field. Honest framing: gentle
structured practice, not clinical. Verified: `selftest.py` passes (105 lectures / 15 branches);
pure course-model + persistence round-trip unit-tested (advance caps, completed flag, reset);
offscreen both faces -- a mode day sets the mode + runs, a program day sets `director.program`, a
real >=30 s sit advances the day and clears the active course while a 5 s sit does not, thread-stable.

## Stories round — new branch Mythic Places (Atlantis, Shangri-La, El Dorado, Avalon)
Added a 15th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
ASCII, sleep-closing), each legend framed **honestly as a legend** -- the wonder is the tale and the
real history of believing in / searching for it, never a claim the place was real: `lectures_atlantis.py`
(Atlantis, Ocean Waves - Plato's Timaeus/Critias as a moral parable about pride, most scholars hold
he invented it, the 19th-c hunt after Donnelly, the Thera/Minoan possible echo, no continent has
sunk), `lectures_shangrila.py` (Shangri-La, Mountain Stream - fiction from James Hilton's 1933 Lost
Horizon, rooted in the Tibetan Shambhala legend, a between-the-wars longing for refuge, the US
retreat later renamed Camp David, Yunnan's renamed county), `lectures_eldorado.py` (El Dorado,
Forest Wind - "the gilded one" began as the real Muisca gold-dust raft rite at Lake Guatavita near
Bogota, swelling through retelling into a golden city never found, Raleigh's voyages, the lake
drained but no city, the surviving golden raft), and `lectures_avalon.py` (Avalon, Gentle Rain - the
Arthurian Isle of Apples first written by Geoffrey of Monmouth, the wounded king carried across the
water to heal, the once-and-future-king, Glastonbury's likely pilgrim-drawing grave claim). New
branch in `_CATALOG` -> **105 lectures / 15 branches**. Validated all four (7 sections, 12-13 lines,
pure ASCII, no NAME collisions); `selftest.py` passes (148 voices); DB rebuilt (8,846 lines /
135,019 words / 5 scenes). The storyteller `units()` stream renders each (e.g. Avalon = 111 units).

## App round — spatial polish (gentle, peak-safe ambience width + slow auto-pan)
Added `breathsim/spatial.py` (`Spatializer` + `SpatialTrack`, 80 lines): two subtle, peak-safe,
click-free stereo effects on the ambience bed. (1) **Pseudo-stereo widening** -- each output channel
is a *convex* blend of its own channel and a short, differently-delayed copy of the other (dl 17 ms,
dr 23 ms, weight 0.35); being a convex combination its magnitude is bounded by the input peak, yet
the two distinct delays decorrelate L and R so even a mono bed gains width (Schroeder/complementary-
comb pseudo-stereo). (2) **Very slow auto-pan** -- a ~0.02 Hz balance drift that only ever
*attenuates* one side (gains <= 1), so the bed sways without ever raising the peak. Both carry state
across blocks (a maxd-sample dry tail + a free-running LFO sample counter) so they stay click-free.
The `ambience` layer is wrapped in `engine.set_voice` when `engine.spatial` is on; `set_spatial(on)`
re-wraps live; **Sound > Spatial width (ambience)** toggles it (default on), persisted as `spatial`
and restored in `window._restore_settings` before `apply_mode`. Honest framing: a width/pan effect,
not 3D/binaural. Verified: `selftest.py` passes (101 lectures / 14 branches); a 300 s spatialized
render of Gentle Rain / Slow-Wave Pulse / Ocean Waves / Forest Wind keeps wet peak <= dry peak and
<= 0.95 with no NaNs and L/R correlation falling from ~1.0 to ~0 (real widening); offscreen the
ambience layer wraps when on and unwraps after toggling off, thread-stable (1->2), both faces.

## App round — first-run onboarding (gentle welcome, re-openable from Help)
Added `vesper/onboarding.py`: a calm, skippable 4-step welcome (what Vesper is -> the mode bar ->
press play -> everything is in the menus). It is **modeless** (uses `show()`, never a blocking
`exec()`) with `WindowModal` modality, so it can't trap the user or hang a headless session;
`open_onboarding(win)` builds/pages it (Skip / Back / Next / Begin, dotted progress) and
`maybe_show(win)` shows it once on first launch only -- gated on a persisted `onboarded` flag and
**skipped entirely when `QApplication.platformName() == "offscreen"`** so tests/offline renders stay
quiet. The flag is read in `window._restore_settings`, set on finish/close/Esc via a read-modify-
write merge (since `store.save_settings` overwrites the whole file) and also re-saved in
`closeEvent`. Re-openable from a new **Help > Welcome / Getting Started** menu entry (`menus._help`).
Honest framing (no wellness claims beyond "a quiet place to breathe"); matches the night theme.
Verified: `selftest.py` passes (101 lectures / 14 branches); offscreen, building the window auto-pops
**0** dialogs, `open_onboarding` then paging to "Begin" sets + persists `onboarded`, a 24-frame loop
is thread-stable (1->2), on both the 3D and cat faces; settings isolated via `BREATHSIM_HOME`.

## Stories round — new branch Trees of the World (Oak, Bamboo, Baobab, Cherry Blossom)
Added a 14th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate botany/history, ASCII, sleep-closing): `lectures_oak.py` (The Oak, Forest Wind - Quercus,
slow centuries, a single tree as a kingdom of life, mast years + the forgetful jay, mycorrhizal
web, ship timber + iron-gall ink + thunder gods), `lectures_bamboo.py` (Bamboo, Soft Rainstorm - a
giant grass, near a metre a day, hollow silica-strong culms that bend not break, one rhizome-joined
grove, once-in-decades synchronous world-wide flowering and death, panda food, flutes + the first
lightbulb filament), `lectures_baobab.py` (The Baobab, Night Crickets - the upside-down tree, a
trunk holding thousands of litres against drought, one-to-two-thousand-year lives, hollow trunks as
shelters, the tree of life, night-only bat-pollinated flowers, Madagascar's avenue), and
`lectures_cherryblossom.py` (Cherry Blossom, Gentle Rain - sakura, the grafted Somei-yoshino clone
flowering as one, mono no aware + the thousand-year hanami custom, the blossom front, Kyoto's
millennium of records showing warming, the blossom blizzard, the gift to Washington). New branch in
`_CATALOG` -> **101 lectures / 14 branches**. Validated all four (7 sections, 12-13 lines, pure
ASCII, no NAME collisions); `selftest.py` passes (148 voices); DB rebuilt (8,495 lines / 128,801
words / 5 scenes). The storyteller `units()` stream renders each (e.g. Cherry Blossom = 112 units).

## App round — Slow-Wave Pulse sleep ambience (~0.8 Hz pink-noise swell)
Added `textures._SlowPulse` -> the **"Slow-Wave Pulse"** GROUP_NATURE ambience (now 148 voices). A
warm pink+brown noise wash (one-pole-LP'd at 900 Hz) amplitude-modulated by a slow ~0.8 Hz sine
(depth 0.38, ~48 swells/min) so it rises and falls like deep, slow breath. **Honestly framed** in
the blurb as open-loop soothing, not EEG-entrained — no closed-loop claims. Gain calibrated to 0.176
(150 s unit peak 2.135; verified 300 s peak 0.752, rms 0.137). An FFT of the rendered envelope
confirms the modulation sits at 0.80 Hz. Verified: `selftest.py` passes (97 lectures / 13 branches);
a >=45-tick offscreen Relax session selecting it as the ambience is thread-stable (2->2) on both the
3D and cat faces. Fixed the headless test hang: the mood "before" check-in opens a modal on a fresh
non-Sleep Start, which blocks offscreen — disabled mood in the test, and (follow-up) defaulted the
auto mood check-in to **off** so it no longer pops a modal before every meditation unless the user
opts in via Sound > Mood check-ins.

## App round — clock-aware theming
Added `vesper/clocktheme.py` (pure, testable): `clock_warm_for_hour(h)` (0 by day, ramping up in
the evening to a capped 0.22 overnight, easing back before dawn) and `suggested_mode_for_hour(h)`
(night->Sleep, early morning->Meditate, late morning->Breathwork, midday->Meditate,
afternoon/evening->Relax). `window._tick` now applies a gentle time-of-day warmth via the existing
warm overlay, combined as `warm = max(sleep_warm, clock_warm)` with a tiny matching opacity dim, so
it never fights the Sleep wind-down or the Sunrise wake; a **View > Clock-aware light** toggle
(default on, persisted in settings). On launch, when no mode has been saved, the app opens in a
time-fitting mode (no popup). Verified: helpers (warm @12=0.0, @23=0.22; modes sensible); selftest
passes; offscreen the launch mode suits the hour, clock warmth is 0.22 at a patched night hour and
0 when toggled off, thread-stable (2->2) on both faces; the night PNG shows a subtle warm dim.

## Stories round — new branch Gems & Stones (Amber, Pearl, Jade, Diamond)
Added a 13th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate science/history, ASCII, sleep-closing): `lectures_amber.py` (Forest Wind - fossilised
resin, trapped insects, elektron/electricity, Baltic shores), `lectures_pearl.py` (Ocean Waves -
nacre layered around an irritant, the only gem made by a creature, divers), `lectures_jade.py`
(Singing Bowl - toughest gem, nephrite/jadeite, ground with sand, prized in China + Mesoamerica)
and `lectures_diamond.py` (Brown Noise - carbon under deep heat/pressure over billions of years,
volcanic pipes, the honest note on "forever"). Verified no file/name collisions first. Registered
the new `("Gems & Stones", [...])` branch in `_CATALOG` -> **97 lectures / 13 branches**. Validated
structure + ASCII + sleep-close + no duplicate names; DB rebuilt (8,141 lines / 123,451 words);
selftest passes.

## App round — particle weather overlay
Added `vesper/scene_particles.py`: a `ParticleLayer` (kinds off/snow/leaves/bubbles/fireflies)
drawn on top of any scene each frame. Snow drifts down and sways; leaves tumble down rotating;
bubbles rise and wobble; fireflies drift and twinkle with a soft radial glow - all from seeded
per-particle params + anim-time motion (deterministic, nothing per frame random), thin and
low-contrast so it never gets busy. Wired into `VizWidget` (a held layer drawn between the scene
and the warm overlay; `set_weather(kind)`), with `window.set_weather` and a **View > Weather**
submenu (Off default). selftest passes; offscreen scene session with snow then fireflies is
thread-stable (3->3); PNGs confirm soft snow over the night scene and glowing fireflies over the
sea. 105 lines.

## App round — gentle mood check-in
Added an optional, pressure-free mood check-in. `breathsim/store.py`: `log_mood(value, when)` +
pure `mood_entries()`/`mood_summary()` (count, avg before/after, avg shift); added "moods" to the
history default. `vesper/mood.py`: `ask_mood(win, when)` - a small modal with five calm choices
(Tense..Serene -> 1..5) + Skip, returning the value or None; `maybe_check_in` (no-op in Sleep mode
or when disabled) and `summary_text()` for Stats. `window`: a `_mood_on` flag + `set_mood_checkins`,
a **before** check-in offered only on a *fresh* non-Sleep Start (before the controller starts) and an
**after** check-in offered when a non-Sleep sit (>=60 s) ends - on pause/reset directly, and on
natural completion via `QTimer.singleShot` so it never re-enters the tick. A **Sound > Mood
check-ins** menu toggle (default on). `stats_heatmap.build` shows a kind one-liner when there are
entries. Verified: `mood_summary` on 4 synthetic entries gives (4, 2.5, 4.0, +1.5); selftest passes;
offscreen the picker + Stats dialog construct (the Stats PNG shows the mood trend line), Sleep mode
skips the prompt, thread-stable (2->2) on both faces.

## Stories round — new branch The Elements (Fire, Water, Air, Earth)
Added a 12th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section 1,
accurate science, ASCII, sleep-closing): `lectures_fire.py` (Campfire - combustion as released
sunlight, the fire triangle, flame colour/soot, embers), `lectures_waterelement.py` (Mountain
Stream - the water cycle, ice floating, heat capacity, surface tension, a drop's long journey),
`lectures_air.py` (Forest Wind - nitrogen/oxygen, air pressure, wind, the thin blue shell, shared
breath) and `lectures_earth.py` (Brown Noise - crust over moving rock, living soil, the rock cycle
+ deep-time layers, the iron core + gravity holding you). NOTE: the existing `lectures_water.py`
("A River to the Sea", Earth & Sea) was accidentally overwritten by the Water subagent; restored it
from git and kept the new Elements water as `lectures_waterelement` (NAME "Water", distinct from "A
River to the Sea") to avoid a name/file collision. Registered the new `("The Elements", [...])`
branch in `_CATALOG` -> **93 lectures / 12 branches**. Validated structure + ASCII + sleep-close +
no duplicate names; DB rebuilt (7,797 lines / 117,646 words); selftest passes.

## App round — practice streaks + calendar heatmap in Stats
`breathsim/store.py` now keeps a per-day practice log (a `days` dict of {date: {min, sits}}, written
by `log_session` using `datetime.date.today()`; backward-compatible via the history default). Added
pure, unit-testable helpers: `daily_minutes()`, `streak()` (current + best runs of consecutive days
with any practice; an un-practised today does NOT break the current streak - it counts back from
yesterday) and `week_minutes()` (last 7 days). New `vesper/stats_heatmap.py`: a kind streak line
("3 days in a row - lovely", inviting message at 0), this-week minutes, and a GitHub-style 13-week
x 7-day grid painted in `paintEvent` with cells shaded by minutes (theme.CARD->ACCENT), plus a
friendly empty state; embedded in `dialogs.open_stats`. Verified: streak/daily/week helpers on a
synthetic history give (3,5)/(2,2)/(0,0) as expected; selftest passes; offscreen Stats dialog +
heatmap construct without error, thread-stable; PNG looks like a clean calm calendar.

## Feature (user request) — best voices: British-female default + marked best + TTS research
Researched offline TTS engines and set the most realistic voice we can ship as the default.
**Decision**: Kokoro neural (already integrated, ~300 MB ONNX, Apache, faster-than-real-time on
CPU, #1 on TTS Arena, true British voices) is the right shipping engine; Fish Speech (12-16 GB
GPU) and XTTS/Coqui (2-8 GB VRAM, ~1.8 GB model, sub-real-time on CPU) are higher-ceiling for
cloning/emotion but would break the offline/laptop/graceful-degrade guarantees, so they are
documented as an optional future GPU add-on, not bundled. **Implemented**: default narration voice
is now **Kokoro `bf_emma` (British female)** - reordered `kokoro_tts.RELAXING` (British females
first) + added `RECOMMENDED`; reordered the `say` fallback `RELAXING` (UK females first) and made
`_say_best` prefer a UK female (Premium/Enhanced); defaulted the spoken-cue voice to a UK female in
`window` init. Added `narration.voice_label/recommended/is_recommended` - the Sleep "Narration
voice" picker (`sections._card_story`) now shows friendly labels with accent + gender and a leading
★ on the most realistic voices, best-first (e.g. "★ Emma - British female"), mapping label->id so
selection still passes the engine id. Verified: bf_emma synthesises clean audio (2.9 s, finite,
peak 0.65); `best_voice` -> bf_emma; picker labels starred + British-female-first; selftest passes;
offscreen Sleep workspace builds the labeled picker and switches voices, thread-stable on both
faces.

## App round — 5 more procedural ambiences
Added five GROUP_NATURE ambiences. NoiseTrack voices in `voices.py`: **Rain on a Tent** (mid-band
pink patter on canvas), **Wind in Pines** (steady pink wind, slow auto-pan), **Fan (White Noise)**
(smooth lowpassed masking). Two new event/tonal generators in `textures.py`: **Womb Heartbeat** (a
muffled ~54 Hz lub-dub at 64 bpm over a lowpassed brown blood-flow wash) and **Whale Song** (slow
sine-glissando moans via integrated phase, swelling, over a deep sea wash). All env="volume", in
the soundscape ambience picker. Gains calibrated; worst peak over 300 s <= 0.78 (the noise beds got
extra headroom). selftest passes (147 voices); offscreen Relax session selects + crossfades them,
thread-stable (2->2) on both faces.

## App round — Breathing mandala scene
Added `vesper/scene_mandala.py` (a `MandalaScene`, registered at the bottom of scenes.py via
`_CLASSES["mandala"]` + `AMBIENT.append`): a calm, centred mandala of 5 concentric rings (6/12/24-
fold radial symmetry) of petals, dots and small arcs, drawn by rotating a motif N times around the
centre. It **expands on the inhale and contracts on the exhale** (radius follows `volume`),
neighbouring rings **counter-rotate** very slowly over anim time, and a soft `QRadialGradient`
centre pulses with the breath; colour is the per-phase `theme.phase_hue`. Slow, low-contrast,
deterministic (no per-frame RNG / threads). In the View > Scene menu (Meditate/Chant). selftest
passes; offscreen scene session thread-stable (2->2); PNG confirms a clean symmetric mandala.
98 lines.

## Feature (user request) — Poetry storyteller (soothing nocturnes)
Added `breathsim/poetry.py`: an original collection of 8 calming sleep/night poems (The Last
Light, Tide, Rain at Night, The Night Train, Stars, Snowfall, Lullaby for the Restless Mind, The
River) - written for Vesper, so no copyright concerns. The storyteller speaks a title then one
line at a time with breath-length pauses (2 s), a longer rest at each stanza break (3.2 s) and a
long silence between poems (5.2 s), cycling endlessly in a shuffled order. Surfaced as a Sleep
storyteller option "Poetry" via `stories.extra_names`/`story_units`/`ambience_for` (Soft Rainstorm
bed), reusing the whole narration + talking-head + wind-down path; lines carry `kind="poem"` so the
`window._on_story_unit` guard holds the bed steady (no cue flicker on the shifting imagery).
selftest passes; offscreen Sleep session recites poems, bed steady, thread-stable (2->3) on both
faces. More poems can be added in future rounds. The autonomous loop continues building the FOCUS
backlog (mandala next).

## Stories round — The Cosmos +3 (The Sun, Galaxies, Meteor Showers)
Expanded the Cosmos branch via 3 parallel subagents (7 sections, 12 lines, fact-free section 1,
accurate astronomy, ASCII, sleep-closing): `lectures_sun.py` (Brown Noise - a nearby yellow-dwarf
star, core fusion, 8-light-minute light, corona, sunspots), `lectures_galaxies.py` (Pink Noise -
island of stars, the Milky Way barred spiral, Andromeda, the galactic year, the cosmic web) and
`lectures_meteors.py` (Wind Chimes - Earth crossing a comet's dust trail, the radiant,
Perseids/Geminids, meteoroid/meteor/meteorite). Cosmos branch now 14 -> **89 lectures /
11 branches**. Validated structure + ASCII + sleep-close; DB rebuilt (7,459 lines / 111,678
words); selftest passes.

## Feature (user request) — Rhythmic / environmental FX (instrument suite complete)
Added `breathsim/synth_fx.py` (instrument suite, part 4, final): composite filtered-noise + event
generators. `_Train` (Steam + Diesel) = paired wheel "clickety-clack" clacks on a tempo + a
lowpassed brown rumble + a band-passed engine chuff per beat. `_Ship` = a band-passed water wash
that swells (lapping hull) + occasional low wooden creaks + a rare slow horn blast. `_Storm` = a
distant lowpassed rumble bed + randomly-spaced thunder events (a brief high-passed crack then a
multi-second rolling lowpassed rumble), gentle/far-off. `_Buoy` = a struck two-mode bell tolling
irregularly (rocked by the swell) over a faint sea wash. 5 voices in a new **Environmental FX**
group (GROUP_FX), plugged in via `textures.register_generator`, in the ambience picker + a
**Sound > Environmental FX** menu. Gains calibrated; worst peak over 300 s <= 0.75 (these stack
noise + random events). selftest passes (142 voices); offscreen Relax session selects + crossfades
them, thread-stable (2->2) on both faces. 218 lines.

This COMPLETES the user's synthesised-sound suite: **synth_bell** (12) + **synth_drum** (7) +
**synth_wind** (7) + **synth_fx** (5) = **31 new synthesised instruments/effects** across Bells &
Gongs, Drums, Winds & Organs and Environmental FX - all `kind="texture"` generators sharing the
struck-resonator / additive-drone / scheduled-event / filtered-noise primitives, calibrated, in
the soundscape pickers + Sound submenus.

## Feature (user request) — Whistles / Organs / Horns synthesis module
Added `breathsim/synth_wind.py` (instrument suite, part 3): sustained additive tonal sources in
two shapes. `_Organ` is a continuous drone (a harmonic stack + a tremulant + slight detune beating
+ optional breath chiff) - Pipe Organ (full/churchy), Harmonium/Shruti (buzzy reed, ideal under
chants), Reed Organ (soft), Wooden Flute (breathy, near-pure). `_Horn` schedules periodic blasts
(`_Blast` = a chord with a slow raised-cosine swell-in, hold, slow release) - Train Whistle (a
wistful 4-pitch chord), Fog Horn (deep octave), Ship Horn (low two-tone). 7 voices in a new
**Winds & Organs** group (GROUP_WIND), plugged in via `textures.register_generator`, in the
ambience picker + a **Sound > Winds & Organs** menu. Gains calibrated over a 120 s render
(~0.72 peak); FFT confirms the spectra (Pipe Organ 131/262, Harmonium 147/294/440, Flute 330/659,
Train Whistle 440/524/660/783, Fog Horn 140). selftest passes (137 voices); offscreen Chant
session selects + crossfades them, thread-stable (2->2) on both faces. 174 lines.

## Feature (user request) — Drums synthesis module
Added `breathsim/synth_drum.py` (instrument suite, part 2): a membrane/percussion synth. Each hit
(`_Hit`) is one-or-two membrane modes - decaying sines with a gentle **downward pitch glide** (a
struck head slackens as it rings, via the integrate-frequency-to-phase trick) - plus a short
**noise attack transient** (shared seeded noise gated by per-hit envelopes, bandpassed). `_DrumGen`
strikes on a steady slow tempo with a little swing, cycling a per-spec hit **pattern** (djembe
bass/slap, slit-drum two tones, tabla cycle). 7 drums in a new **Drums** group (GROUP_DRUMS):
Frame Drum, Taiko, Tabla, Djembe, Log Drum, Woodblock, Bodhran - plugged in via
`textures.register_generator`, offered in the **effects-slot** picker (`vesper/sections.py`) + a
**Sound > Drums** menu (`win.set_effect`). Gains calibrated over a 120 s render (~0.72 peak); FFT
confirms the right pitches (Frame 87 Hz, Taiko 61 Hz, Tabla 207 Hz, Woodblock 890 Hz). selftest
passes (130 voices); offscreen Relax session selects + crossfades drums in the effects slot,
thread-stable (2->2) on both faces. 164 lines.

## Feature (user request) — Bells & Gongs synthesis module
Researched bell/gong/bowl acoustics (Hemony partials hum 0.5 / prime 1 / tierce 1.2 / quint 1.5 /
nominal 2 with long-quiet lows + short-bright highs; gong bloom; bowl beating from close modes;
triangle = mostly high overtones) and built `breathsim/synth_bell.py`: a configurable struck
resonator (`_Bell`: decaying, optionally blooming sine partials with a soft onset) + a slow strike
scheduler (`_BellGen`) + a sustained rubbed-bowl drone (`_SungBowl`). A library of 12 instruments
in a new **Bells & Gongs** group (GROUP_BELLS): Meditation Bell (rin), Temple Bell (bonsho),
Church Bell, Hand Bell, Tibetan + Crystal + Sung Singing Bowls, Tam-tam Gong, Nipple Gong,
Triangle, Tingsha, Tubular Bell. They toll slowly on their own as a meditation/chant/ambience bed,
plugged in via `textures.register_generator` (kind="texture", env="volume", floor=1.0), surfaced in
the Relax/Sleep soundscape picker AND a global **Sound > Bells & Gongs** menu. Gains calibrated over
a 160 s render (~0.72 peak); FFT confirms the right spectra (Meditation Bell at 523 Hz, Gong dense
& low 75-158 Hz, Bowl beating 196/197, Triangle all-high 4.5-12 kHz). selftest passes (124 voices);
offscreen Relax session selects + crossfades bells, thread-stable (2->2) on both faces. This also
ticks the backlog's "Gong bath / tuned bowl set". Queued follow-on modules (researched + tasks):
drums (`synth_drum.py`), whistles/organs/horns (`synth_wind.py`), rhythmic/environmental FX -
train/ship/thunder (`synth_fx.py`).

## App round — Aurora scene (northern lights)
Added `vesper/scene_aurora.py` (an `AuroraScene`, registered at the bottom of scenes.py via
`_CLASSES["aurora"]` + `AMBIENT.append`): a dark starry night with four slow northern-lights
curtains - soft green/teal/violet vertical drapes drawn as overlapping vertical-gradient columns
whose top edge undulates and whose brightness drifts in slow patches, each curtain also drifting
sideways on layered near-coprime sines (so it never repeats), the glow swelling with the breath -
over a faint twinkling star field (`scene_fx.starfield`, upper sky only) and a dark horizon
silhouette. Deterministic (seeded + anim-time, nothing per-frame). selftest passes; offscreen
scene session thread-stable; PNG confirms soft shimmering aurora. scene_aurora.py ~110 lines.

## Stories round — new branch Small Wonders (Dew, Dust in Sunlight, Seeds, Snowflakes)
Added an 11th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section
1, accurate science, ASCII, sleep-closing): `lectures_dew.py` (Forest Wind - condensation at the
dew point on still clear nights, frost), `lectures_dust.py` (Soft Rainstorm - motes lit by a
sunbeam via light scattering, house dust + cosmic dust, Brownian motion), `lectures_seeds.py`
(Mountain Stream - embryo + endosperm in a coat, dormancy, dispersal, germination) and
`lectures_snowflakes.py` (Wind Chimes - vapour freezing on a speck, six-fold symmetry from water's
lattice, no two alike). Registered the new `("Small Wonders", [...])` branch in `_CATALOG` ->
**86 lectures / 11 branches**. Validated structure + ASCII + sleep-close; DB rebuilt (7,207 lines
/ 107,062 words); selftest passes.

## App round — Rain-on-window scene
Added `vesper/scene_rain.py` (a `RainScene`, kept out of the now-large scenes.py and registered
at the bottom of scenes.py via `_CLASSES["rain"]` + `AMBIENT.append`): a dark cosy night window
with a warm streetlamp glow blurred beyond the pane (breathing gently with the breath), a faint
fogged-glass haze and still condensation beads, and 34 sliding drops + 6 slow rivulets running
down the glass (each a soft trail with a brighter rounded head; trail length slowly elongates to
suggest merging). Deterministic (seeded per-drop params + anim-time motion, no per-frame RNG).
Slow, low-contrast; pairs with the Rain ambiences. selftest passes; offscreen scene session
thread-stable (2->2); PNG confirms rain on a glowing window.

## Feature (user request) — natural-sound breath voices (in/out combinations)
Added `breathsim/voices_breath_nature.py`: 7 airflow-driven breath voices (GROUP_BREATH) where
the breath becomes a soothing natural sound, with the in-breath and out-breath taking on distinct
character via `exhale_mul` + the airflow-swept brightness: **Tide & Pebbles** (wave rolls in, draws
back bright through pebbles), **Deep Surf** (deep dark sea hush), **Spring Rain** (fine high patter),
**Pine Wind** (gusts that drift across the stereo field), **Ember Glow** (a fire fanned brighter on
the in-breath, settling on the out), **Cosmic Wind** (a vast airy wind of space) and **Snowfall
Hush** (an almost-silent winter stillness). Because they are GROUP_BREATH they can be set as the
inhale voice AND the exhale voice, so any in/out pairing works (e.g. Pine Wind in, Tide & Pebbles
out). Impressionistic filtered-noise (noise colour + resonant filter + brightness sweep + stereo
motion), calibrated to ~0.70 peak; selftest passes 3x (peak-safe vs the non-deterministic noise),
airflow voices silent on holds (<=0.008); offscreen in/out-combo session thread-stable (2->2) on
both faces. 112 voices now.

## Feature (user request) — Sleep Hypnosis guided session
Researched sleep hypnosis (the classic induction -> deepening -> suggestion arc; Cordi & Rasch
2014 found hypnotic suggestion can boost slow-wave sleep up to ~80% in suggestible people;
delivery is slow + permissive with long silences) and added `breathsim/hypnosis.py`: a narrated
script that settles the listener, slows the breath (a few breath-paced breaths), relaxes the body
head-to-toe, deepens with a 10->1 countdown + a gentle descent image, gives permissive sleep
suggestions, and drifts into sleep (no re-alerting), then thins into an endless sparse drift tail.
Surfaced as a Sleep storyteller option "Sleep Hypnosis" via `stories.extra_names`/`story_units`/
`ambience_for` (Soft Rainstorm bed), reusing the whole narration + talking-head + wind-down path;
a `kind="hypnosis"` guard in `window._on_story_unit` keeps the bed steady. Honest framing in the
docstring (promising evidence, not a cure). selftest passes; offscreen Sleep session selects it,
holds the bed, thread-stable (2->3) on both faces.

## App round — Fireplace scene (warm flickering fire)
Added `scenes.FireplaceScene` (a 5th ambient scene): a warm pulsing hearth glow that breathes
with the breath, seven soft swaying flame tongues built from stacked warm radial-gradient blobs
(slow flicker derived from anim time - no strobing), two crossed dark logs, a bright central
heart, and 14 embers drifting upward and fading. Warm, low-contrast, melatonin-friendly; pairs
with the Campfire ambience. Registered in `AMBIENT`/`_CLASSES` so it appears in the View > Scene
menu (`win.set_scene("fireplace")`). Deterministic (seeded params, anim-time motion - no
per-frame randomness or thread spawns). selftest passes; offscreen scene session thread-stable
(2->2); PNG confirms a cosy fire. scenes.py ~395 lines.

## App round — Sunrise / Wake mode (dawn simulation, inverse of the wind-down)
Added a gentle dawn wake-up. `session.SessionDirector.start_wake` + `_update_wake` mirror the
sleep path inverted: over the duration the breath pattern eases slow->normal (Extended 7-11 ->
Coherent 5.5, raised-cosine) and the master volume rises from 15% to full by ~80%. `window._tick`
gains a wake branch that BRIGHTENS the view: the warm dim wash fades (0.4 -> 0) and the window
opacity rises (0.55 -> 1.0) as the wake progresses (the inverse of the Sleep warm-dim). `app.start_sunrise`
arms it (Forest Wind dawn-chorus bed + a soft waking chime, clock restarted from 0), wired to a
new **Sessions > Sunrise (gentle wake-up)** menu entry; switching mode/program cancels it via
`set_mode` (now clears `wake`). selftest passes; offscreen wake verified early-dim vs late-bright
(warm 0.40->0.03, breath cycle 18.0s->11.1s), thread-stable (2->2), both faces; PNGs confirm the
visible brightening.

## Stories round — new branch The Quiet Crafts (Bookbinding, Blacksmith, Basketry, Stained Glass)
Added a 10th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free section
1, accurate craft history, ASCII, sleep-closing): `lectures_bookbinding.py` (Soft Rainstorm -
signatures, the bone folder, the codex, sewn cords, headbands, gold tooling), `lectures_blacksmith.py`
(Campfire forge - bellows, iron softening not melting, anvil, quench + temper, the Iron Age),
`lectures_basketry.py` (Forest Wind - older than pottery, soaked willow, the slath, stakes and
weavers, the border) and `lectures_stainedglass.py` (Singing Bowl - metal-oxide colours, the
cartoon, fired glass-paint, lead cames, Gothic rose windows). Registered the new
`("The Quiet Crafts", [...])` branch in `_CATALOG` -> **82 lectures / 10 branches**. Validated
structure + ASCII + sleep-close; DB rebuilt (6,871 lines / 101,327 words); selftest passes.

## Music round — Aurora Tones + Saturn Ring Shimmer presets
Added two more Cosmic Music presets to `cosmic.py`: **Aurora Tones** (ethereal, slowly shifting
mid/high pentatonic pads, wide stereo, gentle high shimmer, large reverb, breath-synced - cold
glowing curtains) and **Saturn Ring Shimmer** (a brighter/higher palette with more high partials
and a fine 7.8 kHz shimmer, wide stereo, big reverb - icy and glittering). Calibrated over a
200 s breath render (Aurora gain 0.563, Saturn 0.757; peaks ~0.59/0.73); FFT confirms tonal,
consonant content and near-zero window correlation (non-repeating). **10 Cosmic Music voices**
now; selftest passes; offscreen Relax session selects + crossfades both, thread-stable (2->2)
on both faces. cosmic.py 340 lines.

## Music round — Sound > Cosmic Music menu (one-click generative music)
Surfaced the generative music as first-class: added a **Cosmic Music** submenu under the Sound
menu (`vesper/menus.py`) listing all 8 `GROUP_MUSIC` voices, each calling `win.set_ambience`
to play it as the ambience bed in one click (they were previously only in the Relax/Sleep
soundscape combo, which still lists them). selftest passes; offscreen Relax session rebuilds the
menu without error, all 8 set_ambience callbacks work, thread-stable (2->2); window PNG renders
cleanly with no layout change, both faces.

## Music round — true data sonification (Kepler planets + real pulsar)
Grounded the cosmic music in real astronomy. Added `cosmic._planet_scale()`: takes the real
planetary orbital periods (Mercury..Neptune), turns each into an orbital-frequency ratio vs the
slowest (Neptune), folds it into an octave and snaps it to the nearest just-intonation degree -
yielding a consonant scale [1, 5/4, 4/3, 9/5, 2, ...] that literally encodes the solar system.
New **"The Planets"** preset plays it over a low C2 drone (Kepler's harmony of the spheres made
audible). Also retuned the **Pulsar Pulse** beat to the real **PSR B1919+21** spin period
(1.3373 s -> 0.748 Hz, the first pulsar ever found). Calibrated The Planets over a 200 s render
(gain 0.497, peak 0.66); FFT confirms tonal content at base x scale and a measured pulsar beat
of ~0.74 Hz; non-repeating (corr ~-0.1). 8 Cosmic Music voices; selftest passes; offscreen
Relax session selects The Planets, thread-stable (2->2) on both faces.

## Stories round — new branch Voyages & Journeys (Compass, Caravan, Railway, Balloon)
Added a 9th lecture branch via 4 parallel subagents (7 sections, 12-13 lines, fact-free
section 1, accurate history, ASCII, sleep-closing): `lectures_compass.py` (Mountain Stream -
needle, Earth's molten core, lodestone, declination), `lectures_caravan.py` (Forest Wind -
camels, the Silk Road web, caravanserais, oases), `lectures_railway.py` (Soft Rainstorm -
steam, steel rails, clickety-clack, railway time, sleepers) and `lectures_balloon.py` (Forest
Wind - warm-air lift, the 1783 sheep/duck/rooster, going with the wind). Registered the new
`("Voyages & Journeys", [...])` branch in `_CATALOG` -> **78 lectures / 9 branches**.
Validated structure + ASCII + sleep-close; DB rebuilt (6,533 lines / 95,249 words); selftest
passes.

## Music round — breath-synced cosmic music (it breathes with you)
Made the Cosmic Music breathe with the listener. `textures.TextureTrack` now feeds the breath
state to opt-in generators (`wants_state`), keeping the existing nature textures unchanged.
`cosmic._Cosmic` reads lung volume (`BreathState.volume`) and, per a new per-palette `breath`
amount, gently (a) raises pad spawn density, (b) opens a brightness lowpass, and (c) applies a
click-free level swell (ramped across the block) on the inhale, settling them on the exhale.
All 7 presets opt in at gentle amounts (Solar Wind strongest at 0.6, deep/slow ones 0.3-0.35).
Recalibrated all gains under a 4-2-6-2 breath (peaks ~0.73); verified the music tracks the
breath (Solar Wind vol/RMS corr +0.65; slow presets +0.15..0.22) while staying tonal +
non-repeating. selftest passes (102 voices); offscreen Relax session selects/crossfades the
music, thread-stable (2->2) on both faces.

## Music round — Cosmic music +4 presets (ringdown glide + pulsar beat)
Expanded `cosmic.py`: added an optional **click-free pitch glide** to `_Pad` (integrate
frequency to phase, f0->f1 over the note) and a **pulsar amplitude pulse** to the drone, then
4 new Cosmic Music presets: **Solar Wind** (bright airy shimmer, E3), **Nebula Bloom** (lush
formant-tinged blooming chords, C3), **Pulsar Pulse** (a soft 0.7 Hz beat over sparse tones,
D2) and **Gravity Well** (deep minor tones sliding down an octave - a black-hole ringdown,
G1). Gains calibrated over a 200 s render (peaks ~0.74); verified tonal/consonant + non-
repeating (window corr ~0), glide descends click-free (max sample jump 0.005), pulsar beat
measured at 0.70 Hz. 7 Cosmic Music voices now; selftest passes (102 voices); offscreen Relax
session selects + crossfades the new voices, thread-stable (2->2) on both faces.

## Feature (user request) — Cosmic generative music ("music of the spheres")
Researched generative-music best practice (Eno/Reich phasing of near-coprime loops; constrain
randomness to a consonant scale; drone + slow harmonic drift for gentle tension/release;
layered detuned voices + reverb for richness; NASA-style cosmic sonification) and built a
real engine to match. New `breathsim/reverb.py` (a click-free **block-delay feedback-comb**
reverb: all delays exceed one audio block so feedback is purely from past blocks, fully
vectorised, with damped tails) and `breathsim/cosmic.py` (a `_Pad` additive-stack voice with
raised-cosine attack/hold/release + vibrato; a `_Cosmic` scheduler that overlaps pads on slow
near-coprime gaps, draws pitches from **just-intonation** scales over a steady drone, drifts
the root slowly through consonant roots, and optionally adds a **vowel formant** colour for a
choir or an **airy shimmer** for deep space). Three presets in a new **Cosmic Music** group
(`GROUP_MUSIC`): **Music of the Spheres**, **Starlight Choir**, **Deep Space**, wired via
`textures.register_generator` (no `tracks.py` change) and surfaced in the Relax/Sleep
soundscape picker. Gains calibrated over a 200 s render (peaks 0.71-0.74, ~0.75 target);
spectra confirm pure tonal/consonant content (Spheres 110/330/440/660 Hz; Deep Space 55/66/132
with a just minor third) and near-zero window correlation = never repeats. selftest passes
(98 voices); offscreen Relax session selects + crossfades the music, thread-stable (2->2) on
both faces.

## Stories round — The Cosmos +3 (Comets, Nebulae, Saturn's Rings)
Authored three new Cosmos sleep-lectures via parallel subagents (7 sections, 12-13 lines,
fact-free section 1, accurate astronomy, ASCII, sleep-closing): `lectures_comets.py` (Brown
Noise — dirty snowballs, Oort Cloud, tails point away from the Sun, Halley), `lectures_nebulae.py`
(Singing Bowl — gas/dust clouds, stellar nurseries, planetary/supernova remnants, "star
stuff"), `lectures_saturnsrings.py` (Wind Chimes — icy particles, paper-thin disc, Cassini
Division, ring rain). Registered in the Cosmos branch → **74 lectures / 8 branches**.
Validated structure + ASCII + sleep-close; DB rebuilt (6,196 lines / 89,069 words); selftest
passes.

## App round — Cognitive Shuffle sleep-onset aid
Added `breathsim/shuffle.py`: a narrated **cognitive shuffle** (Beaudoin's serial-diverse
imagining). A soft letter is chosen, then 3-5 ordinary, neutral, easily-pictured objects
beginning with it are named slowly with long picture-it gaps (3.6-5.2 s), then a fresh
letter, on and on — monotone, low-arousal, crowding out rumination. 185-word bank across
25 letters; a steady **Brown Noise** bed, with a `kind="shuffle"` guard in
`window._on_story_unit` so the random nouns don't pull the soundscape around. Wired through
the existing storyteller path: `stories.story_units`/`ambience_for` dispatch to it and a new
`stories.extra_names()` surfaces it as **"Cognitive Shuffle"** in the Sleep story picker.
Stream validated (well-formed units, ambience resolves); offscreen 50-tick Sleep session
holds the bed steady and is thread-stable (2→3, one narrator thread) on both faces;
selftest passes.

## App round — NSDR / Yoga Nidra guided session
Added an 8-stage `programs.Program` "NSDR / Yoga Nidra (12 min)" (11.5 min): settle in →
settle the mind → breath awareness → rotation of awareness right side → left side →
back & front → whole-body heaviness → rest. Monotone-calm spoken cues (the classic
"rotation of consciousness") with long quiet pauses between them — each stage speaks once,
then breath alone — closing on a slow 8-12 breath at low volume over the night scene.
Auto-listed in the Sessions menu + the Breathwork programs card via the existing
`programs.names()` wiring; all stage patterns/voices/ambience/effect resolve; offscreen
60-tick run advances through all 8 stages, thread-stable (2→2); selftest passes.

## Roadmap to parity with the Tk app
- Per-mode **workspaces** + control cards (Breath/Voice/Chant/Sing/Relax/Sleep).
- Visual **scenes** as Qt painters (orb, ripple, wave, night, pitch trainer) +
  a scene/face toggle.
- **Dialogs**: mixer, pattern editor, voice editor (+ wave/spectrum), presets,
  stats; **menus**; keyboard shortcuts; **guided programs** / session director.
- **Background-sound toggles**, naturalness, morph/automation, spoken-cue picker.
- **GPU face** (moderngl `*_gpu` modes) for smooth ICT/decimated; lip-sync
  visemes; persona/appearance picker.
