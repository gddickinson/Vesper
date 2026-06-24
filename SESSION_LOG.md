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
