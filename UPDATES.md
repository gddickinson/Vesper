# UPDATES — autonomous improvement backlog

A self-paced loop works through this list, **one item per round**: research → plan →
implement → **test** → mark done. **Focus now = improving the app** (graphics,
effects, and the sleep/meditation efficacy of every window), keeping to each
window's theme. Keep adding stories too, but secondary: take the next *Stories
(ongoing)* item roughly every 3rd round.

Guardrails (every round):
- Do ONE unchecked `[ ]` item (top-down, but a Stories item every ~3rd round); check
  `[x]` only when tests pass.
- Keep every file **< 500 lines**; one concept per file.
- **Self-contained project**: the live core is the VENDORED copy at
  `vesper/breathsim/` — edit code/lectures THERE (not `../breathing_sim`).
- Audio voice gains are **calibrated**: build at unit gain, set `gain = 0.8/peak`.
  Keep all motion/colour/sound **slow, low-contrast, predictable** (calming).
- Test from the project root: **`python selftest.py`**. If lectures changed, rebuild
  the DB (`python -m breathsim.story_db`). If the UI changed, run a brief **offscreen
  session** (`QT_QPA_PLATFORM=offscreen`, ≥40 `_tick` calls + a view toggle) AND
  assert `threading.active_count()` stays stable (catches per-frame thread/resource
  leaks — e.g. spawning a render thread per tick); render + LOOK AT a PNG for graphics
  changes. If anything fails, fix or revert before marking done.
- Append a one-line note to `SESSION_LOG.md`; update the matching todo task; reschedule.
- When the focus list empties, append 3–5 new researched items + tasks, then do one.

## Research notes — cast narration / dramatized books + more characters (user-requested 2026-06-25)
The user asked to (1) **add more characters + costumes**, and (2) let **multiple characters act out the
different voices in a book** -- the LLM can pre-read the book to work out which characters to cast, when
each speaks, *how* they speak (delivery/emotion), what costumes/props they wear, and which background
sounds to play and when. Ground the rounds in these:
- **Reuse what exists**: `vesper/characters.py` + `char_*` (15 2D characters), `char_costume.py` (12
  costumes drawn over the head), `char_voice` (per-character narration voices), `narration.Narrator.
  set_voice` (voice switching mid-stream), `books`/`bookreader` (the sentence/paragraph stream),
  `sound_cues` (text->ambience), `story_char` (storyteller picks a character per scene), the face mood
  (`_mood_target` / `emotion_for_text`). Most of the machinery is already here.
- **The new core = a "book script"**: an annotation over a Book's sentences -> per-segment
  ``{speaker, voice, emotion, character, costume, prop, sound}``. TWO producers, both honouring the
  safety rules: (a) a **pure OFFLINE heuristic** (the safe default) -- detect quoted dialogue + "...,
  said Alice" attribution, map each recurring speaker deterministically to a distinct narration voice +
  2D character/costume, annotate ambience via `sound_cues`; works with no LLM. (b) an **OPT-IN LLM
  "director"** -- pre-reads the book in chunks and returns a richer cast (characters with voice traits,
  a suggested 2D character + costume + prop, emotions) + a per-passage speaker/emotion/sound map;
  treated as **untrusted** (validated against the existing character/costume/voice/ambience registries,
  clamped, fail-closed) and **saved once per book**.
- **Dramatized player**: on each unit, switch the narration voice to the speaker's voice, swap the 2D
  character + costume + prop, set the face mood from the emotion, and trigger the cued background sound.
  **Sleep-gentle by default** (quiet voice variation so it still lulls), with a "more expressive" option
  for the daytime Reader.
- **Safety**: the LLM director is OPT-IN only (no backend -> the heuristic is used); all LLM output is
  validated against existing registries + clamped + never executed; no new network beyond the existing
  opt-in LLM; everything degrades to the plain single-voice narrator.
- **Round plan**: CAST-1 = more characters + costumes/**props** (the direct ask; sleep-friendly adds
  like Nightcap / Sleep Mask + held props Book/Lantern/Candle/Teacup the cast needs). CAST-2 =
  `breathsim/bookcast.py` heuristic (pure dialogue/attribution detection -> a Script; offline-tested).
  CAST-3 = the **Dramatized** playback toggle (Reader + Sleep) wiring voice/character/costume/prop/mood/
  sound per segment. CAST-4 = `breathsim/llm_cast.py` opt-in LLM director (validated cast, saved per
  book, heuristic fallback). CAST-5 = polish (props rendering, smoother crossfades, per-book cast
  memory, a who's-who cast list). Interleave with the Stories cadence (every ~3rd round).
- [x] **CAST-1 done — more characters + costumes**: 2 new 2D characters (Mouse, Sheep, with voices)
  -> **17 characters**; 5 new costumes (Nightcap, Sleep Mask, Earmuffs, Witch Hat, Pirate Hat) ->
  **17 costumes**. Montage PNG eyeballed; selftest + both-faces drive (0 issues) + a thread-stable
  offscreen FaceWidget character swap; all 13 offline tests pass; README/CLAUDE bumped. (Next CAST-2:
  bookcast.py heuristic Script.)
- [x] **CAST-2 done — `bookcast.py` heuristic cast Script** (pure, offline, no LLM): `script(book)`
  assigns a speaker per sentence (quoted dialogue + "said Alice"/"Alice asked" attribution, a
  stop-list, a one-sentence look-ahead for tags split after `?`/`!`, last-speaker continuation),
  casts recurring speakers deterministically to distinct characters + voice archetypes, with a
  per-line emotion + `sound_cues` ambience; pure (no vesper import). Offline test
  `tools/test_bookcast.py`; selftest + both-faces drive (0 issues); all 14 offline tests pass. (Next
  CAST-3: dramatized playback.)
- [x] **CAST-3 done — Dramatized playback** (`vesper/cast.py` + a Books-menu toggle, default OFF,
  persisted): a book is read by its cast -- per line the narrator switches to the speaker's character
  **voice** (`unit["voice"]`, now honoured by `narration.Narrator._loop`), the visible 2D **character**
  swaps to the speaker (`face.set_character`, visual only -- never restarts narration), and a gentle
  **mood** is set from the emotion; an **Expressive** toggle adds soft sound-following for daytime.
  Wired into the Sleep "Book:" path + the Reader; empty-safe (off / no dialogue -> single voice). Pure
  `cast.segment_plan` offline-tested (`tools/test_cast_plan.py`). selftest + both-faces drive (0
  issues) + a dramatized offscreen drive (2 distinct voices + 2 characters, zero thread leak); all 15
  offline tests pass. (Next CAST-4: opt-in LLM director.)
- [x] **CAST-4 done — opt-in LLM cast director** (`breathsim/llm_cast.py`, validated + fail-closed):
  when a backend is configured, `direct(book, characters, costumes, complete=None)` pre-reads a capped
  sample, asks for STRICT JSON, and **clamps every field against the registries** (unknown character/
  costume dropped to the heuristic / "None"), failing closed to the CAST-2 heuristic on any error / no
  backend; caches once per book (`~/.breathsim/casts.json`). `vesper/cast.build_cast` prefers the saved
  cast + kicks off the director **off-thread** only when Dramatized is on AND a backend exists AND no
  cast is saved (opt-in; default-safe). Offline test `tools/test_llm_cast.py` (stubbed completer).
  selftest + both-faces drive (0 issues) + an offscreen drive honouring a saved LLM cast (zero leak);
  all 16 offline tests pass. (Next CAST-5: polish -- costumes, crossfades, who's-who.)
- [x] **CAST-5 done — dramatized polish; CAST THREAD COMPLETE**: (1) per-speaker **costume** rendering
  (`cast.apply_cast_tick` sets the visible `face.set_costume` to the speaker's costume; restored with
  the character on end); (2) a **"Who's in this book..."** dialog (Books menu) via pure
  `cast.cast_summary` (speaker -> character + costume + source heuristic/AI), with a **Re-cast** button
  (`llm_cast.delete_cast`). Offline test `tools/test_cast_summary.py`. selftest + both-faces drive (0
  issues) + an offscreen dramatized drive (3 character+costume combos, zero leak) + dramatized-face &
  who's-who PNGs; all 17 offline tests pass. **The cast/dramatized-books thread is COMPLETE (CAST-1..
  CAST-5)** -- more characters/costumes, a who-speaks Script, dramatized playback (voice+character+
  costume+mood+sound), an opt-in validated LLM director, and a who's-who + re-cast UI; all opt-in,
  sleep-gentle, offline-degrading. Loop returns to normal top-down improvements next.

## Research notes (evidence-based — ground each round in these)
- **Slow breathing ~6 breaths/min (0.1 Hz)** maximizes HRV via the baroreflex
  (resonance/coherence breathing); a **longer exhale** drives vagal/parasympathetic
  calm. Acute calmers: **4-7-8**, **box 4-4-4-4**, **physiological sigh** (double
  inhale, long exhale).
- **Evening light**: blue light suppresses melatonin; **warm, dim, low-blue** light
  and a gradual fade aid sleep onset. → Sleep should warm + dim over the wind-down.
- **Pink/brown noise** deepens slow-wave sleep and masks disturbances.
- **Plotless, low-arousal narration + body-scan/PMR** reduce rumination (a calm
  "cognitive shuffle"). Predictable, slow, low-contrast visuals soothe; avoid abrupt
  change. **Per-window coherence**: look + sound + guidance match the activity.
- **NSDR / Yoga Nidra**: a slow, guided rotation of awareness through the body + breath
  ("non-sleep deep rest") restores alertness and lowers stress — monotone calm, long
  pauses, no goal but rest.
- **Cognitive shuffle (serial diverse imagining)**: gently picturing a stream of random,
  neutral, concrete objects mimics pre-sleep micro-dreams and crowds out rumination — an
  evidence-based sleep-onset aid (Beaudoin); deliver random nouns with long breath gaps.
- **Dawn/dusk light**: gradual **dawn simulation** (warm→bright over ~20–30 min) eases
  waking, lifts mood, helps seasonal low mood; warm dim **dusk** light cues wind-down.
- **Generative ambient sound**: slow, **non-repeating** tonal textures (Eno-style) relax
  better than loops — the brain habituates less and there's no loop-seam to notice.
- **ASMR & soft repetition**: for many, soft whispers, gentle taps and slow repetitive
  sounds trigger a calming low-arousal "tingle"; keep them quiet, regular, optional.
- **Honest framing**: binaural beats need headphones and the evidence is mixed; true
  slow-wave boosting (closed-loop pink-noise bursts) needs EEG. Offer gentle ~0.8 Hz
  pink pulsing / headphone tones, framed honestly — never over-claim.
- **Awe & nature (Attention Restoration)**: vast, slow, awe-evoking nature (night sky,
  ocean, forest) restores attention and lowers rumination — keep scenes nature-rich.
- **Gentle habit support**: a consistent wind-down ritual aids sleep; **non-judgemental**
  streaks / feedback support adherence without pressure.

## Agreed roadmap (current — do in this order)
Set with the user after the realistic-chanting round. Tick as completed.
1. [x] **Reverb / sacred-space send** — `reverb.SpaceReverb` master room
   (Off/Room/Hall/Cathedral), Sound ▸ Space menu, persisted. Done.
2. [x] **Chant workspace controls + sing-along** — phrase card now has "Sing the whole
   phrase per breath" + "Reciting tone" toggles and a live ♪ syllable read-out
   (`engine.current_syllable`). Done.
3. [x] **Body-scan + PMR guided program** — "Body Scan & PMR (15 min)" in
   `programs.py`: tense->release feet-to-head on a (4,3,9,0) breath, then melt. Done.
4. [x] **Physiological-sigh reset** — "Physiological Sigh Reset (3 min)" program
   (double inhale -> long sigh), auto-listed in Sessions / Breathwork. Done.
5. [~] **Characters -> story binding + story-following dynamic backgrounds**
   - a) [x] the storyteller picks a fitting character per scene (`story_char.py` +
     Face ▸ "Character follows the story", restores the user's pick). Mood reaction
     already flows via `_ease_mood` -> smile. Done.
   - b) [x] **story-following themed backgrounds** — `story_bg.bg_for_text` maps narrated
     imagery -> backdrop; `face.set_background(fade)` crossfades slowly; new Rain/Forest/
     City backdrops; Sound ▸ "Backdrop follows the story" toggle (persisted). Done.
   - (original spec:) subtle dynamic scene backdrops that
     follow what's being narrated -- themes like **starry sky, fire/hearth, weather
     (rain/snow/wind/clouds), natural scenes (forest/sea/meadow), urban scenes** --
     with **gentle, slow crossfades** between them as the imagery shifts. Soothing and
     low-contrast; reuse the existing `sound_cues` text->imagery mapping so picture +
     soundscape move together. NEVER startling/dramatic: long fades (multi-second),
     small motion, dim palette; default-on but toggle-able; honours Sleep dimming.

## App improvements — FOCUS (do these first)
- [x] Per-window **themed backdrops** behind the face + two new effects
      (**Underwater** for Relax, **Embers** cozy). Modes auto-theme the bg.
- [x] **Sleep — warm, low-blue progressive dimming**: a warm amber wash on the view
      grows 0→0.5 over the wind-down (`face_bg.warm_overlay`, applied in face + viz),
      plus a gentle window dim. Verified early (clear) vs late (warm/dim) renders.
- [x] **Breathwork — patterns + phase visual**: Box 4-4-4-4 & 4-7-8 already existed;
      added a **Physiological Sigh** preset (2.5-1-6); added an orb **phase-progress
      ring** that fills over each phase (per-phase hue makes inhale/hold/exhale/rest
      read at a glance). Thread-stable; selftest passes.
- [x] **Orb scene** (Meditate/Breathwork): floating motes, soft exhale rings, and a
      gentle mint "coherence" halo near ~6 breaths/min (uses new ctx `bpm`).
- [x] **Night scene** (Sleep): deeper vertical gradient, slow drifting clouds, an
      occasional faint shooting star, over the existing moon + stars.
- [x] **Wave scene** (Relax): night-sky gradient + faint stars, a moon with a
      wavering reflection column on the water, foam dabs on crests, smoother swells.
- [x] **Ripple scene** (Chant/Sing): tone-reactive ring colour + spacing (louder =
      brighter, closer) + a central glow that pulses with the tone.
      (All four via shared calm helpers in new `vesper/scene_fx.py`; thread-stable.)
- [x] **More procedural ambiences** (range of effects): Campfire, Singing Bowl,
      Wind Chimes, Night Crickets (new `kind="texture"` event generators in
      `breathsim/textures.py`) + Rain on a Roof (NoiseTrack). Deterministically
      seeded; gains calibrated (~0.75 peak; 300 s worst peak ≤ 0.80). 90 voices now;
      appear in the Relax/Sleep soundscape picker; selftest passes, engine-safe.
- [x] **Soundscape**: extended `sound_cues` to map the new ambiences + fire / bells /
      wind-chimes / crickets / rain-on-roof / birds (with false-hit guards for
      belly/remember/chimney); the bed now **ducks to 0.5 then eases back** on each
      crossfade (via live `set_layer_level`, leaving the user level intact); added a
      **Sound ▸ Soundscape follows story** toggle (default on) that holds the base
      ambience when off. Cue + offscreen duck/toggle tests pass; thread-stable.
- [x] **Face naturalism**: `face.set_state` now adds micro-**saccades** on top of the
      slow gaze drift, a rare **settling-sigh** and **swallow** (one-shot gesture
      bumps -> head dip + soft mouth), **flatter affect** as the session winds down
      (gaze/saccade/smile/brow all damped by a `calm = 1-0.6*prog` factor), and a gentle
      **head-cock on curious lines** (brow -> yaw on the 3D head, a true roll on the
      cat). Shared by both faces via the gaze/tilt in `_cat_state`. Both verified
      (renders + >=40-tick offscreen, thread-stable); selftest passes.
- [x] **GPU face**: antialias the silhouette (MSAA) so the head edge is smooth over
      the backgrounds — `face_gpu` now renders to a **4x multisample FBO** and resolves
      to a single-sample texture for readback (`copy_framebuffer`), with a graceful
      single-sample fallback if the driver lacks MSAA. Worker thread + transparent
      RGBA intact; edge-zoom confirms smooth; thread-stable; cat path unaffected.
- [x] **Sing — pitch trainer**: a running **% time-in-tune** score + an **in-tune glow**
      frame on the PitchScene, and **3 more exercises** (Minor scale, Octave siren, Sixth
      stretch). **Meditate** — a **guidance** card (Off / Focused attention / Open
      monitoring) showing slow rotating cues softly under the orb (~every 22 s). Verified
      via renders + offscreen ticks; thread-stable; selftest passes.

### Researched batch — restful practices (efficacy)
- [x] **NSDR / Yoga Nidra** guided session: an 8-stage `programs.Program` (settle →
      breath → rotation of awareness right/left/back+front → whole-body heaviness →
      rest), 11.5 min, monotone-calm spoken cues with long quiet pauses, closing on a
      slow 8-12 breath. Auto-listed in the Sessions menu + Breathwork programs card;
      stages/names validated, offscreen run thread-stable (8 stages advance).
- [x] **Cognitive Shuffle** sleep-onset aid: new `breathsim/shuffle.py` (serial-diverse
      imagining, Beaudoin) — a soft letter is chosen, 3-5 ordinary objects beginning with
      it are named with long picture-it gaps, then a new letter, forever. 185-word neutral
      bank; steady Brown Noise bed (a `kind="shuffle"` guard stops the noun stream pulling
      the soundscape). Dispatched via `stories.story_units`/`ambience_for`/`extra_names`;
      picks as "Cognitive Shuffle" in the Sleep story card. Offscreen (both faces)
      thread-stable; selftest passes.
- [x] **Sleep Hypnosis** (user-requested): `breathsim/hypnosis.py` - a slow, permissive guided
      hypnosis script (induction: settle + breath + head-to-toe relaxation; deepening: 10->1
      countdown + descent imagery; permissive sleep suggestions; drift into sleep, no
      re-alerting), surfaced as a Sleep storyteller option via `stories.extra_names`. Steady bed
      (cue-suppressed); honest framing (evidence promising, esp. for the suggestible). Tested
      both faces, thread-stable.
- [x] **Body-scan + PMR** guided program: slow timed tense→release cues head-to-toe,
      paced to the breath. (Delivered as roadmap item 3 — "Body Scan & PMR (15 min)" in
      `programs.py`.)
- [x] **Physiological-sigh reset**: a 2–3 min "Sigh" mini-session (double inhale, long
      exhale) + a matching visual, for a quick down-regulation. (Delivered as roadmap
      item 4 — "Physiological Sigh Reset (3 min)".)

### Researched batch — light & circadian
- [x] **Sunrise / Wake mode**: `director.start_wake` + `app.start_sunrise` + a Sessions menu
      "Sunrise (gentle wake-up)" - over N min the view brightens (warm dim->clear, inverse of
      the Sleep wash), the volume rises (quiet->full), the breath quickens (Extended 7-11 ->
      Coherent 5.5) and a Forest Wind dawn bed + soft chime fade in. Verified early-dim vs
      late-bright renders (warm 0.40->0.03, cycle 18s->11s), thread-stable, both faces.
- [x] **Clock-aware theming** (`vesper/clocktheme.py`): a gentle time-of-day warmth on the view
      (0 by day, up to ~0.22 warmer + a touch dimmer overnight) via the existing warm overlay
      (combined as `max(sleep_warm, clock_warm)` so Sleep still dominates), with a **View >
      Clock-aware light** toggle (persisted); and on launch, when no mode is saved, it opens in a
      time-fitting mode (night->Sleep, morning->Meditate, etc.). Pure helpers unit-tested; PNG +
      both faces verified.

### Researched batch — new visual scenes
- [x] **Fireplace scene** (`scenes.FireplaceScene`): a warm pulsing hearth glow, soft swaying
      flame tongues (slow flicker, no strobing), crossed logs and embers rising + fading; the
      fire breathes with you. In the View > Scene menu; pairs with Campfire. Verified PNG +
      thread-stable offscreen.
- [x] **Rain-on-window scene** (`scene_rain.RainScene`): a dark cosy night window - a warm lamp
      glow blurred beyond the pane (breathes with the breath), a fogged-glass haze with still
      condensation beads, and many drops + slow rivulets sliding down the glass (heads + trails,
      gently elongating). In the View > Scene menu; pairs with the Rain ambiences. PNG +
      thread-stable verified.
- [x] **Aurora scene** (`scene_aurora.AuroraScene`): slow northern-lights curtains - soft
      green/teal/violet vertical drapes that undulate, shimmer and drift on layered near-coprime
      sines over a faint star field and a dark horizon; the glow swells with the breath. In the
      View > Scene menu. PNG + thread-stable verified.
- [x] **Breathing mandala** (`scene_mandala.MandalaScene`): concentric 6/12/24-fold rings of
      petals, dots and arcs that expand on the inhale and contract on the exhale, with
      neighbouring rings counter-rotating very slowly, a soft central glow and the per-phase
      breath hue. In the View > Scene menu. PNG + thread-stable verified.
- [x] **Particle weather** (`vesper/scene_particles.py`): an optional `ParticleLayer` drawn over
      any scene - Snow (drifting), Leaves (tumbling + rotating), Bubbles (rising), Fireflies
      (twinkling glow). Deterministic anim-time motion; thin and low-contrast. Wired into
      `VizWidget` + a **View > Weather** submenu (Off default). PNGs + thread-stable verified.
- [x] **Candle / trataka scene** (`vesper/scene_candle.py`, `CandleScene`): a single warm
      candle flame in the dark to rest the gaze on (*trataka* focused-attention practice -
      suits Meditate). A pale wax body, the warm pool of light it casts, an ambient glow that
      **breathes with the breath**, faint rising glints, and a layered teardrop flame (outer->
      core radial gradients + the cool **blue base** of a real flame) that sways + flickers
      gently (low amplitude, no strobing) and grows on the inhale. Deterministic; self-registers
      in the **View > Scene** menu; default per-mode scenes unchanged. Also added a reusable
      `tools/drive_check.py` (cycle every scene + mode, assert threads stay flat). Verified:
      selftest passes; both-faces drive 9 scenes / threads 2->2 / 0 issues; inhale vs exhale
      PNGs read calm + warm.

### Researched batch — next (added 2026-06-24; focus list had emptied)
Grounded in the research notes above; calming, honest, self-contained. Do one per round
(top-down), Stories every ~3rd. Tick `[x]` only when tests pass.
- [x] **Ease-to-resonance pacing** (Meditate/Breathwork): an opt-in **Settle in (ease to
      your pace)** toggle (Pattern menu, persisted). A fresh session starts a touch faster
      than the chosen pattern and the breath period eases up to the target over ~2.5 min,
      then holds — a gentler entry to ~6 breaths/min than starting there cold. Implemented in
      `SessionDirector` (`start_settle`/`stop_settle`/`_update_settle`/`settle_info`, a cosine
      ease from a `ratio`-scaled faster start up to the target, then locks; mirrors the wind-
      down lerp); `app_actions.set_settle` arms it at the next fresh start (or now if running,
      and re-aims at a newly chosen pattern); faint "easing to your pace…" read-out under the
      scene. Verified: numeric ease test (11.0s target: 6.6->8.8->11.0, locks + restores),
      window+menu integration test, selftest, both-faces drive (0 issues).
- [x] **Breath-paced auditory swell** — **Sound ▸ "Breathing soundscape (bed swells with
      you)"** (opt-in, persisted). The ambience bed gently rises with the inhale and softens
      ~22% on the exhale (follows lung fullness `BreathState.volume`), a soft auditory pacer
      that entrains slow breathing without a spoken count. Folded into the single per-frame
      ambience writer `_apply_soundscape` as `level = base * duck * swell` so it can never
      fight the story-cue duck; leaves the user's base level intact. Verified: integration
      test (off = flat at base; on = base at inhale-top -> base*0.78 at exhale-bottom,
      monotonic + bounded + restorable); selftest; both-faces drive (0 issues).
- [x] **Themed self-help hypnosis sessions** (user-requested) — 6 new Sleep storyteller
      options in `breathsim/hypnosis_topics.py`: Letting Go of Stress, Quiet Confidence, Calm
      Focus, Letting Go of Worry, Deep Self-Acceptance, Peaceful Gratitude. Refactored
      `hypnosis.py` to expose reusable `induction`/`drift_tail`; each theme = that arc with a
      swapped permissive suggestion block, always winding down to sleep (no alerting language,
      honest framing). Wired via `stories.extra_names`/`ambience_for`/`story_units`; appear in
      the Sleep picker. Verified: dispatch + ambience resolve + sleep-close; selftest + drive.
- [x] **Bedtime gratitude / "one good thing"** (Sleep, opt-in): a single, gentle end-of-
      session reflection ("one good thing about today") shown softly + optionally logged to
      Stats — no scoring, fully skippable. Evidence: bedtime gratitude reduces pre-sleep
      worry and improves sleep quality. Reused the mood-check-in plumbing: `store.log_gratitude`
      / `gratitude_entries` / `gratitude_count` / `gratitude_last_date` (cap 200, 280-char clamp,
      malformed-value safe); `vesper/gratitude.py` (`should_offer` pure gate · `ask_gratitude`
      Keep/Skip dialog · `maybe_offer_bedtime`, once-per-Sleep-start, off by default). Wired into
      `window.toggle_transport` (fresh start), `app_actions.set_gratitude`/`gratitude_now`,
      Sessions menu ("One good thing…" + "Bedtime gratitude" toggle), a kind "Good things noted: N"
      line in Stats, and settings persistence. Verified: `tools/test_gratitude.py` + offscreen GUI
      smoke (menus present, threads stable) + selftest + drive_check.
- [x] **Stories (next branch)** — **The Dwarf Planets** (4): *Pluto* (Clyde Tombaugh's patient
      1930 find, school-children naming, the gentle dwarf-planet reclassification, New Horizons 2015,
      the pale heart Tombaugh Regio + Sputnik Planitia nitrogen glaciers, the blue haze, the
      waltzing moon Charon), *Ceres* (largest in the asteroid belt, first dwarf planet found by
      Piazzi on the first night of 1801, harvest-goddess name, Dawn mapping, the Occator/Cerealia
      Facula salt that briny water left behind, the ice-volcano Ahuna Mons), *Eris* (a 557-year
      orbit out in the scattered disc, Mike Brown's 2005 discovery, near-twin of Pluto that gently
      birthed the "dwarf planet" name, the moon Dysnomia), and *Haumea* (egg-shaped Kuiper-Belt
      world whose calm tireless ~4-hour spin eased it into an oval, bright water-ice gleam, the
      first ring found on such a world, the moons Hiiaka and Namaka). Each = 7×12 second-person
      present sleep-closing ASCII lines; ambiences Brown Noise / Singing Bowl / Pink Noise / Wind
      Chimes. Drafted via four parallel writers, validated (7×12, pure ASCII, every section
      sleepward), registered in `lectures._CATALOG`. Verified: **selftest 225 lectures / 45
      branches**; story DB rebuilt (303k words); all 20 offline tests; drive_check 0 issues.
- [x] **Stories (next branch)** — **The Inner Planets** (4): *Mercury* (smallest, airless,
      closest to the Sun; ancient craters + Caloris Basin; the slow 3:2 spin so a day lasts months;
      a large iron heart; the near-perihelion double sunrise; polar-shadow water ice; Messenger),
      *Venus* (the morning/evening star; a near-twin under a golden mirror-cloud veil; slow backward
      spin with a day longer than its year; Ishtar/Aphrodite Terra; Galileo's phases; Magellan radar
      — kept soft, no hellish-heat dwelling), *Mars* (rust-red desert; Phobos & Deimos; Olympus Mons
      + Valles Marineris; thin butterscotch sky and cool-blue sunsets; seasonal polar caps; ancient
      riverbeds; the patient Curiosity/Perseverance rovers), and *Earth from Space* (the tender
      closer — the blue marble, the apple-peel-thin atmosphere, day into night with city lights and
      auroras, the overview effect, the Moon, the Voyager pale blue dot + Carl Sagan, ending in
      belonging, held safe on the turning world). Each = 7×12 second-person present sleep-closing
      ASCII lines; ambiences Brown Noise / Soft Rainstorm / Forest Wind / Ocean Waves. Drafted via
      four parallel writers, validated (7×12, pure ASCII, every section sleepward), registered in
      `lectures._CATALOG`. Verified: **selftest 221 lectures / 44 branches**; story DB rebuilt (297k
      words); all 19 offline tests; drive_check 0 issues.
- [x] **Stories (next branch)** — **The Great Voyages** (4): *The Wayfinders* (Polynesian
      star-path navigation — the star compass of rising/setting stars, reading the deep swells
      in the hull, seabirds and lagoon-lit clouds as land signs, the Hawaii/Aotearoa/Rapa Nui
      triangle, chant-kept knowledge, the Hokule'a revival with Mau Piailug & Nainoa Thompson),
      *The Treasure Fleet* (Zheng He's early-1400s Ming voyages — the great treasure ships, the
      monsoon breathing the fleet to Calicut, Hormuz and Malindi, watertight bulkheads + floating
      compass, the giraffe welcomed home as a qilin), *The First Voyage Around the World*
      (1519-1522 — the patient search for the strait, naming the calm Pacific, the long quiet
      crossing, Elcano bringing the Victoria home, the gently-folded missing day), and *The
      Endurance* (Shackleton 1914-1916, told entirely as patience/stillness/togetherness — the
      ship held calm in the Weddell ice, the long starlit polar night with the southern lights,
      warm lamplit routines, **every crewman home safe**, and the wreck found upright and at
      peace in 2022). Each = the standard 7 sections x 12 second-person present-tense sleep-closing
      lines, accurate science/history kept gentle (no peril dwelt on); ambiences Ocean Waves /
      Soft Rainstorm / Whale Song. Drafted via four parallel writers, validated (7x12, pure ASCII,
      sleepward closes), registered in `lectures._CATALOG`. Verified: **selftest 217 lectures /
      43 branches**; story DB rebuilt (291k words); all 18 offline tests; drive_check 0 issues.
- [x] **Stories (next branch)** — **The Moons of the Giants** (4): *Io, the Volcano Moon*
      (tidal heating, Galileo 1610, Loki Patera, Voyager's plume / Linda Morabito), *Europa,
      the Ocean Moon* (smooth ice shell, lineae, the hidden global ocean), *Titan, the Veiled
      Moon* (nitrogen haze, methane rivers/seas Kraken & Ligeia Mare, the Huygens 2005 landing
      + rounded pebbles), *Enceladus, the Geyser Moon* (tiger-stripe plumes, the warm hidden
      sea, Cassini tasting the plumes, the E ring). Standard 7x12 second-person sleep-closing
      sentences, accurate + wonder-led, distinct NAMEs/modules, ambiences Distant Thunder /
      Whale Song / Gentle Rain / Singing Bowl. Registered as a 36th branch. **189 lectures /
      36 branches**; DB rebuilt (255,791 words); selftest + both-faces drive (0 issues).

### Research notes — storytelling craft & world poetry (user-requested, 2026-06-24)
The storyteller has grown large (189 lectures + procedural scenes + poetry + hypnosis +
shuffle). The user asked to (a) **deepen storytelling craft** for sleep, and (b) **weave
poetry, philosophy and scientific thinking / epistemology** through stories, with **pure
poetry sessions**, drawing on world poetic systems **especially Japan**. Ground future rounds
in these notes:
- **Sleep storytelling is *inverted* dramatic structure.** No tension, stakes, or
  cliffhangers; the craft is *de-escalation* — a "descending" arc that dissolves. Techniques:
  slow sensory immersion (narrative transportation crowds out rumination), meandering /
  low-stakes digression (Sleep-With-Me style boredom-adjacency), refrains + rhythmic
  repetition (lullaby cadence, rule of three), diminishing detail / "zoom out and fade" toward
  the end, cozy safe settings (hygge), spatial wandering ("a slow walk through a place"),
  embedded breath invitations (already done as interludes).
- **Kishotenketsu** (ki-sho-ten-ketsu): the East-Asian 4-movement structure with **no
  conflict** — introduction, development, a gentle *turn* (a shift of view, not a clash),
  reconciliation. Ideal for calm narrative sleep tales; adopt as a story shape.
- **Japanese poetic forms**: *haiku* (5-7-5, a season word *kigo*, a cutting *kireji*, one
  image); *tanka/waka* (5-7-5-7-7, a pivot); *renga/renku* (endless linked verse); ***haibun***
  (gentle prose + haiku — Basho's travel sketches — the natural way to *weave* poem through
  story). Aesthetics to carry as mood + philosophy: *mono no aware* (tender transience),
  *wabi-sabi* (beauty in impermanence/imperfection), *yugen* (subtle depth), *ma* (eloquent
  pause / negative space — pairs with narration silences).
- **Other traditions**: Chinese Tang nature poems (Wang Wei, Li Bai — moon, mountains,
  rivers, solitude); Persian *ghazal* (couplets with a lulling *radif* refrain) + *rubaiyat*
  (Khayyam quatrains on transience); Korean *sijo*; Sanskrit *doha*; English nocturne /
  villanelle (refrains) / lullaby cadence.
- **Philosophy & epistemology, gently**: write so wisdom *soothes*, never lectures. Stoic
  night-counsel (Marcus Aurelius's Meditations were literally written at night), Taoist *wu
  wei* / the watercourse way, Buddhist impermanence, Epicurean *ataraxia*, Heraclitus's river.
  Epistemology as comfort: how we come to know (observation, doubt, models vs. reality,
  instruments extending the senses), and the *peace* of uncertainty ("we don't know, and that
  is a soft and roomy thing"). Always honest, wonder-over-mastery.

### Researched batch — storytelling & poetry (user-requested; do these next, top-down)
- [x] **Pure poetry sessions across cultures** — the `poetry` storyteller is now **selectable
      traditions**, all "Pure Poetry: <tradition>" Sleep options: *English Nocturnes* (the
      original 8, renamed; old "Poetry" name kept as a backward-compat alias), *Haiku & Tanka*
      (new `poetry_world.py`, Japanese short forms, *mono no aware*), *Tang Nature* (in the
      spirit of Wang Wei / Meng Haoran), *Persian* (ghazal couplets with a lulling *radif*
      refrain + rubaiyat quatrains). Refactored `poetry.recite(poems,...)` as the shared
      reciter; `poetry_world` reuses it. All verses **original, written in the spirit of** each
      tradition (no copyright), honestly framed as homage not authentic text; ASCII; beds Wind
      in Pines / Gentle Rain / Singing Bowl. Wired via `stories.extra_names`/`ambience_for`/
      `story_units`. Verified: dispatch + ambiences resolve + ASCII + alias; selftest + drive.
- [x] **Procedural haiku/tanka generator** (`breathsim/haiku.py`, "Drifting Haiku") — a small
      season-aware grammar: per-season image banks (opening / middle / quiet turn = the *kigo*
      built in) compose endless haiku (short/longer/short, in the haiku spirit), ~30% become
      tanka via a shared two-line reflective tail; the seasons drift slowly through the year,
      announced softly. Original fragments (no copyright); deterministic with an injected seed;
      bed "Night Crickets". Wired via `stories.extra_names`/`ambience_for`/`story_units`.
      Verified: dispatch + ambience resolve + ASCII + determinism; selftest + both-faces drive.
- [x] **Haibun storyteller** (`breathsim/haibun.py`, "A Wandering Haibun") — weaves poem
      *through* story, in the spirit of Basho: a slow first-person wandering prose passage
      (assembled from the same `stories` scene vocabulary, with an a/an fixup) is crystallised
      every few lines by a season haiku from `haiku.compose`, then a soft closing line eases
      the walk on, forever. Original; deterministic with an injected seed; bed "Wind in Pines".
      Wired via `stories.extra_names`/`ambience_for`/`story_units`. Verified: dispatch +
      prose/haiku interleave + ASCII + determinism + a/an; selftest + both-faces drive.
- [x] **Lecture branch: Ways of Knowing** (epistemology + science, 4) — *How We Know the Stars*
      (parallax, Bessel + 61 Cygni 1838, light-years, the cosmic distance ladder / Leavitt's
      Cepheids, humility), *The Art of Doubt* (the patient notice->wonder->guess->test loop;
      doubt as kindness; "knowing you do not know"; glad to be corrected), *The Map and the
      Territory* (models/words/memories as maps; "the map is not the territory"; the world is
      larger + gentler than our drawing), *What the Eye Cannot See* (the thin visible ribbon;
      Leeuwenhoek's animalcules; telescope; infrared/UV/radio/x-ray extending the senses).
      Standard 7x12, fact-free section 1, all sleep-closing; ambiences Singing Bowl / Gentle
      Rain / Wind in Pines / Night Crickets. **193 lectures / 37 branches**; DB rebuilt; selftest
      + both-faces drive (0 issues).
- [x] **Lecture branch: Quiet Philosophies** (4) — *The Stoic Night* (in the spirit of Marcus
      Aurelius's night-notes: letting go of what is not yours, the view from above, the calm
      inner citadel), *The Watercourse Way* (Taoism / Lao Tzu: wu wei, water as the soft
      teacher, the low quiet place, letting the muddy water settle clear), *The Beauty of
      Passing Things* (mono no aware + wabi-sabi + kintsugi: impermanence and imperfection as
      beautiful), *The Garden of Tranquility* (Epicurean ataraxia: simple pleasures already
      near, wanting little, the quiet friendship of the garden). Standard 7x12, fact-free
      section 1, all sleep-closing, paraphrased + softly attributed (no verbatim quotes);
      ambiences Singing Bowl / Mountain Stream / Gentle Rain / Wind in Pines. **197 lectures /
      38 branches**; DB rebuilt; selftest + both-faces drive (0 issues).
- [x] **Lecture branch: Colours & Pigments** (4) — *The Story of Indigo* (the rare blue in nature;
      green leaves that secretly hold blue; the fermentation vat and the green-to-blue turn in the
      open air; aizome / West African cloth / denim; the dyer's blue-stained patient hands),
      *Ultramarine* (the longing for a heavenly blue; lapis lazuli flecked with gold from the far
      mountains; "beyond the sea"; the patient grinding/washing that frees the colour; costlier than
      gold, the Madonna's robe, Vermeer), *Tyrian Purple* (purple between red and blue, between day
      and night; the murex snails of Tyre; thousands of shells per cloth; the sunlit yellow->green->
      purple turn; emperors and the lost secret), *Cochineal Red* (the hunger for a true crimson; the
      tiny insects under the prickly pear's white bloom; the careful Mexican harvest; the astonishing
      carmine from grey specks; the guarded trade across the sea). Standard 7x12, fact-free section 1,
      all sleep-closing; ambiences Gentle Rain / Singing Bowl / Ocean Waves / Forest Wind. Registered
      as a 39th branch. **201 lectures / 39 branches**; selftest + both-faces drive (0 issues).
- [x] **Lecture branch: The Polar Worlds** (4) — *The Arctic* (the frozen ocean at the top of the
      world; the long polar night and day; the creaking sea ice; bear, seal and the people of the long
      winter; the aurora), *Antarctica* (the white continent; the mile-deep ice sheet; dry valleys and
      ice shelves; emperor penguins through the winter dark; the explorers' huts), *Icebergs* (calving
      from a glacier; the vast hidden bulk below the water; blue ice and ancient trapped air; the slow
      melting drift home), *The Tundra* (the treeless plain; permafrost; moss, lichen and dwarf willow;
      the brief bright summer bloom and the caribou herds; the long snow). Standard 7x12, fact-free
      section 1, all sleep-closing; ambiences Brown Noise / Forest Wind / Ocean Waves / Wind in Pines.
      Registered as a 40th branch. **205 lectures / 40 branches**; DB rebuilt; selftest + both-faces
      drive (0 issues); all 9 offline tests pass.
- [x] **Lecture branch: Weathers of the World** (4) — *The Monsoon* (the long dry wait; the turning
      wind off the warm sea; petrichor and the first downpour; the green return; steady rainy-day
      calm), *Fog and Mist* (a cloud come to rest on the ground; droplets forming in the still cool
      night; a muffled walk through halos and dissolving trees; sea fog and valley mist; the slow gold
      lifting), *The Thunderstorm* (deliberately gentle + safe-indoors: the warm heavy evening; soft
      distant flicker; rain on the roof while you are dry; the flash-and-count receding; the washed
      calm after), *The Trade Winds* (the steady reliable winds of the warm latitudes; the age of
      sail; a slow blue voyage; leaning palms and coral shores; the faithful wind through the night).
      Standard 7x12, fact-free section 1, all sleep-closing; ambiences Soft Rainstorm / Forest Wind /
      Distant Thunder / Ocean Waves. Registered as a 41st branch. **209 lectures / 41 branches**; DB
      rebuilt; selftest + both-faces drive (0 issues); all 11 offline tests pass.
- [x] **Lecture branch: The Microscopic World** (4) — *A Drop of Pond Water* (a whole tiny ecosystem
      in one drop: drifting algae, the soft amoeba, gliding paramecia, rotifers and water fleas),
      *Diatoms* (microscopic algae that build jewel-like glass shells in endless patterns, drifting in
      billions, settling into pale drifts over ages), *The Water Bear* (the tardigrade -- a plump
      moss-dweller that survives by SLEEPING: curls into a barrel for years through any hardship, wakes
      unharmed; a perfect sleep theme), *Pollen* (the golden dust of flowers, each grain a sculpted
      jewel, drifting on wind and bees to make next year's meadow). Standard 7x12, fact-free section 1,
      all sleep-closing; ambiences Mountain Stream / Ocean Waves / Forest Wind / Gentle Rain. Registered
      as a 42nd branch. **213 lectures / 42 branches**; DB rebuilt; selftest + both-faces drive (0
      issues); all 14 offline tests pass.
- [x] **LLM in the GUI — opt-in API-key Settings dialog** (`vesper/llm_settings.py`, Help ▸ "AI
      Assistant (optional)…") — the safe gateway that finally exposes the (already-built) LLM stack,
      strictly opt-in + fail-closed. The ONE place a key is typed: **password-masked**, never shown
      back / logged / committed; choose where it lives — **session only** (default), **OS keychain**
      (if `keyring` present, else the radio is disabled + labelled), or **chmod-600 file** (labelled
      plaintext-on-device); **Forget** wipes session+file+keychain; **Ollama** opt-in checkbox (no
      network unless ticked), persisted (default off). Status shows backend + key SOURCE, never the
      key. New Qt-free `llm_keys.keychain_available()`; Qt-free helpers unit-tested by
      `tools/test_llm_settings.py` (key stored where chosen, source transitions, chmod-600 lands at
      the user path not the repo, key NEVER echoed). Verified: selftest; both-faces drive (0 issues);
      a ~60-tick offscreen open/close of the modal dialog (zero thread leak, backend `none`); rendered
      + eyeballed the dialog PNG; all 6 LLM offline tests pass with no backend. (Next: a Sleep
      "Generate a bedtime story" action via `llm_story`, then the quiet-helper assistant.)
- [x] **LLM in the GUI — Sleep "Generate a bedtime story"** (`vesper/llm_story_action.py`, a button
      on the Sleep story card) — opt-in + fail-closed. Enabled only when a backend is configured
      (`llm_story.available()`), else **disabled** with a hint to Help ▸ AI Assistant. Asks a topic,
      runs `llm_story.generate` on a **daemon thread** (untrusted reply linted to 7x12 + repaired/
      rejected), returns via a **queued Qt signal** so the UI never blocks. A valid story registers
      into `lectures.LECTURES` ("AI Stories", labelled `AI:`), arms as tonight's Sleep story and
      narrates like any lecture; user chooses **Keep it** (persist) or **Just tonight**. Qt-free
      `can_generate`/`make_story` unit-tested by `tools/test_llm_story_action.py`. Verified: selftest;
      both-faces drive (0 issues); Sleep-panel PNG (button + hint); all 7 LLM offline tests pass with
      no backend. (Next LLM step: the quiet-helper assistant `llm_assist` as an opt-in chat.)
- [ ] **Audiobooks / novels for sleep + a reader** (user-requested 2026-06-24) — narrate full
      public-domain books (Project Gutenberg, on-demand downloader → library + DB), resume where you
      fell asleep, a narration **fade-out** timer, a non-sleep **book-reader** mode with reading
      presets, and **user-uploaded** texts (.txt/.epub). See the research batch + round plan below.

### Research notes — audiobooks / novels (user-requested 2026-06-24)
The narrator already streams sentence "units"; a book is just a very long unit stream, so the core
pipeline (narration, pacing, sleep-timer fade, ambience) is reusable. Ground the rounds in these:
- **Free, legal text sources** (public domain only, downloaded on demand — never bundled/redistributed):
  **Project Gutenberg** (~75k books, plain UTF-8 + EPUB; **search via the Gutendex JSON API**
  `gutendex.com`, fetch the text from a PG **mirror** with a real User-Agent + rate-limit — the main
  site forbids bulk crawling, single on-demand is fine; strip the PG header/footer boilerplate);
  **Standard Ebooks** (smaller, beautifully clean public-domain EPUBs, OPDS feed); **Wikisource** API;
  (LibriVox offers *human* audiobooks — out of scope since we synthesise). Copyright stance: in-app
  download is **public-domain only**; **user-uploaded** texts are the user's own (narrated + stored
  **locally**, never uploaded anywhere).
- **Reuse what exists**: `narration.Narrator` (unit stream), the **sleep-timer** fade-out + `_story_level`
  schedule, `resume.py` + `store.*_lecture_progress` (extend to a per-book sentence index), the Story
  Library dialog (add books + progress), `tools/download_samples.py` (the opt-in best-effort download
  precedent), the stories DB.
- **Segmentation**: split into chapters → paragraphs → sentences (a small, pure, tested tokenizer);
  ASCII-fold smart quotes/dashes for the synth; keep paragraph breaks for natural pauses.
- **Safety**: the downloader is **opt-in** (network only on an explicit user action), rate-limited,
  public-domain only; uploads stay local; everything degrades to "absent" with no network.
- **Decisions (user, 2026-06-24)**: build the **reader mode FIRST** (before the sleep-narration
  slice); the reader view offers **both** scrolling read-along text **and** audio-only, as a
  **toggle**; the downloader covers **all three** sources — **Project Gutenberg + Standard Ebooks +
  user uploads**.
- **Round plan** (reordered per the decisions; one per loop, Stories cadence still applies):
  (1) **`breathsim/books.py` core** — Book model + pure sentence/paragraph tokenizer + PG/Standard-
  Ebooks boilerplate strip + local library at `~/.breathsim/books` + a books table; offline tests on a
  fixture. (2) **Reader mode / reading presets** (non-sleep, FIRST per the user) — steady pace, a
  **text↔audio toggle** (scrolling read-along OR audio-only), no breath-gating/dimming; a `BookReader`
  yielding sentence units dispatched through `stories.story_units`. (3) **Sleep narration of a book** —
  the same `BookReader` under the Sleep wind-down; **resume by sentence index**; fade-out timer wired.
  (4) **On-demand downloader** — Gutendex search + PG mirror fetch **and** Standard Ebooks (opt-in,
  rate-limited, progress) + Library browser with per-book progress. (5) **User upload** — import `.txt`
  then `.epub`. (6) **Polish** — "continue your book" launch hint, per-book voice/preset memory,
  optional LLM "previously…" recap on resume.
- [x] **R1 done — `books.py` + `booktext.py` core** (offline, no network): pure ASCII-folding +
  PG boilerplate strip + abbreviation-aware sentence/paragraph tokenizer + chapter detection; a
  `Book` model + a **local library** at `~/.breathsim/books` (content files + a self-contained
  `_index.json` "books table" + `_progress.json` resume, so `store.py` stays < 500); save/load/list/
  delete + resume position. Offline test `tools/test_books.py`; selftest + both-faces drive + all 7
  LLM tests still pass. (Next R2: BookReader narration + reader mode.)
- [x] **R2 done — Reader mode + `BookReader`** (non-sleep, per the user, before the sleep slice):
  pure `breathsim/bookreader.py` (`units`/`resume_units` -- one narrator unit per sentence, longer
  pause at paragraph ends, resume from the saved index) + `vesper/reader.py` (a new **Books ▸ Read a
  book…** dialog: book picker (empty-safe), **TEXT↔AUDIO toggle**, paragraph-pause preset, reading-
  speed slider; narrates through the shared Narrator at a steady reading pace with a `_reading` guard
  so the session loop doesn't fight it; persists resume per sentence; read-along **highlights + scrolls**
  the current sentence via a GUI-thread QTimer). Offline test `tools/test_bookreader.py`. selftest +
  both-faces drive (0 issues) + a thread-stable offscreen open/close + a populated Reader PNG; all 9
  offline tests pass. (Next R3: BookReader under the Sleep wind-down + fade-out.)
- [x] **R3 done — a book under the Sleep wind-down**: a library book is now a **Sleep storyteller
  option** ("Book: <title>"). `stories.py` gains `BOOK_PREFIX`/`BOOK_AMBIENCE`, `book_names()`,
  `book_id_for()` and dispatch so `story_units("Book: ...")` yields `bookreader` units resuming from
  the saved sentence index and `ambience_for` resolves a calm bed; the Sleep picker appends
  `book_names()` (empty-safe). `win_story._start_story` resolves the book + a resume note;
  `_on_story_unit` persists `books.set_position` per spoken sentence and holds the bed steady for a
  novel. It rides the SAME path as a lecture, so the existing Sleep wind-down + **sleep-timer
  fade-out** quietens/stops it for free, and it resumes next night. Offline test
  `tools/test_book_story.py`; selftest + both-faces drive (0 issues) + a thread-stable offscreen Sleep
  session (book listed, armed, calm ambience); all 10 offline tests pass. (Next R4: downloader +
  Library browser.)
- [x] **R4 done — on-demand downloader + Library browser** (the first networked round, opt-in):
  `breathsim/booksource.py` (pure `parse_gutendex`/`text_to_book` + networked `search`/`download`
  reaching Project Gutenberg via the open **Gutendex** API -- NO key) and `vesper/booklib.py` (Books ▸
  "Find & manage books..." -- search -> results -> **Download** off-thread -> local library + Reader +
  Sleep picker; a Your-library list with Delete). SAFETY: network ONLY on an explicit Search/Download;
  public-domain only; descriptive UA + timeout + 6 MB cap + >=1 s rate limit; fail-closed (no net ->
  []/None, never raises); untrusted bytes parsed as text only. Offline test `tools/test_booksource.py`
  (injected fetch, zero sockets). selftest + both-faces drive (0 issues) + thread-stable offscreen
  open/close + dialog PNG; all 11 offline tests pass with no network. (SE is EPUB-only -> arrives with
  the importer in R5.) (Next R5: user upload .txt then .epub.)
- [x] **R5 done — import your own .txt / .epub** (local, untrusted-safe; also unlocks Standard
  Ebooks): pure `breathsim/bookimport.py` (`import_txt`/`import_epub`/`import_file` -- defensive
  decode; stdlib zipfile+xml.etree EPUB parse via the OPF spine + an XHTML tag-stripper; **zip-bomb
  guards**: per-entry + total + entry-count caps; non-XHTML ignored; fail-closed, never executes) and
  a GUI hook in `vesper/booklib.py` (Books ▸ "Import a book (file)..." + an Import button in the
  dialog) that refreshes the Reader + Sleep picker on success. Offline test `tools/test_bookimport.py`
  (in-memory epub + txt, odd encodings, path dispatch, zip-bomb + junk refused). selftest + both-faces
  drive (0 issues) + a thread-stable offscreen Sleep session (imported epub in the picker) + dialog
  PNG; all 12 offline tests pass with no network. (Next R6: polish.)
- [x] **R6 done — progress polish; AUDIOBOOK THREAD COMPLETE**: pure `books.percent_read` +
  `books.in_progress` + `resumehint.book_continue_hint`; the launch hint now prefers "Continue your
  book: \"<title>\" (N% read)." when a book is partway through, and **% read** shows in the Find &
  manage library list + the Reader note. Offline test `tools/test_bookprogress.py`. selftest +
  both-faces drive (0 issues) + a thread-stable offscreen launch surfacing the hint; all 13 offline
  tests pass with no network. **The audiobooks/novels feature is now end-to-end (R1-R6)**: search +
  download public-domain books, import your own .txt/.epub, read (read-along/audio) or fall asleep to
  them, resume by sentence, % read, continue-at-launch -- all opt-in, local-first, offline-degrading.
  The loop returns to normal top-down improvements next.
- [x] **Kishotenketsu sleep-tales** (`breathsim/tales.py`, "Quiet Tales") — 6 authored,
      conflict-free 4-movement micro-tales (ki intro -> sho development -> **ten** a soft turn
      of view, never a clash -> ketsu reconciliation/dissolve into sleep): The Lamplighter, The
      Still Lake, Snow on the Village, The Old Gardener, The Tea House on the Hill, The Child
      and the Moon. A gentle *narrative* storyteller class distinct from the factual lectures;
      recited forever in shuffled order with a breath between movements + a long rest after each
      tale. Original; deterministic with an injected seed; bed "Soft Rainstorm". Wired via
      `stories.extra_names`/`ambience_for`/`story_units`. Verified: dispatch + 4-movement
      structure + ASCII + determinism + every ketsu sleep-closing; selftest + both-faces drive.
- [x] **Story-craft polish for the procedural scenes** — applied the descending-structure
      toolkit to the `stories.py` scene generator (refactored `_sentence` to share `_fill` +
      take a `fade` factor): a per-session **refrain** (a scene-flavoured recurring line, e.g.
      "And the river goes on, slowly, on and on.", repeated at the close of each pass); a slow
      **zoom-out-and-fade** as the session deepens -- pauses lengthen (`fade` 1.0 -> 2.2) and the
      pass shrinks (`run` -> min 4 sentences), with **widen** lines appearing from the 4th pass
      ("Smaller and softer now, the whole {place} settling into the dark."); and a 4th
      **contemplative interlude** (`_contemplate`/`_REFLECT`: mono-no-aware / Taoist water /
      Stoic night-thoughts) woven into the breath/body-scan/relax rotation. Deterministic;
      Scene/SCENES API + dispatch unchanged. Verified: every scene yields valid ASCII units, the
      refrain recurs, pauses fade (974 -> 2220), contemplative lines appear; selftest + drive.

### Research notes — optional LLM integration (user-requested, 2026-06-24)
A major direction: incorporate an LLM (Claude when a key is present, else a local **Ollama**
model) to (1) generate stories/content on the fly, savable to the library; (2) act as a quiet
in-app helper that speaks through the face; (3) let users add modifications. Assessment +
guardrails for the rounds below:
- **Optional + graceful degradation is non-negotiable.** The app must work fully with no LLM
  (feature hidden). Mirror the narration-engine auto-select + the **XTTS isolation precedent**
  (heavy AI dep, separate env, app fine without it). **Offline-first via Ollama** to keep the
  no-network promise; Claude API only when a key is set (and *disclose* that prompts leave the
  device). Persisted opt-in.
- **Sleep pacing gives latency headroom** (multi-second gaps between lines) -> generate/buffer
  the next passage while the current one narrates; indefinite-length stories pair with the
  existing endless-tail design.
- **Declarative-first, NO arbitrary code execution by default.** The app already has a
  declarative content model (BreathPattern = 4 numbers, VoiceConfig dataclass, phrase
  vowel/pitch/onset segments, 7x12 lecture text). The LLM **fills validated schemas** the app
  already renders; everything passes the existing lint/selftest **before** it can enter the
  library (store.py). A validate->retry loop is the "bug test". This covers most "user
  modifications" safely.
- **Honest labelling.** AI-generated content is marked AI-written; AI *stories* are framed
  atmospheric/imaginative (do NOT claim the authored lectures' factual accuracy unless
  verified). No medical claims. The assistant is a bounded helper, never medical advice.
- **Free-form code-plugins: defer / experimental / sandboxed.** Do NOT auto-write+execute
  Python in the running app. If pursued: write to a `plugins/` dir, explicit opt-in, **bug-test
  in an isolated subprocess** (the selftest/drive harness), never auto-load. Declarative path
  first; this last.

### Researched batch — LLM (DECIDED 2026-06-24 — do AFTER the storytelling & poetry batch)
User decisions: **sequence** = finish the storytelling & poetry batch first, then this; **backend**
= **auto-select** (prefer Claude when an API key is present, else local **Ollama** as the
fallback, else hide the feature); **scope** = declarative content **and** an *optional*
experimental **sandboxed code-plugin** path for advanced users who accept the extra risk
(off by default). Do these top-down once poetry is complete.

**SAFETY FIRST (user: "I want everything to be as safe as possible"):** at every design
choice prefer the safest option; default OFF; least privilege; no network unless the user opts
in; never auto-execute generated code; treat all model output as untrusted (validate before
use); fail closed. A pre-commit secret scan must pass before any LLM-round commit (no `sk-ant-`,
no `ANTHROPIC_API_KEY=<value>`, no long key-like tokens in the diff).

**KEY-SECURITY REQUIREMENTS (mandatory, from the user):**
- The Anthropic API key must **NEVER** be committed to git or shipped in any distribution.
  No key literal anywhere in the repo; `.gitignore` the user config (`~/.breathsim/*`) and any
  local secrets; never bundle a key in packaging; never print/log the key (mask in all UI/logs).
- **Users choose how to provide it (or not):** (a) `ANTHROPIC_API_KEY` env var (app stores
  nothing); (b) OS **keychain** via `keyring` if installed (most secure; optional dep); (c) a
  local file `~/.breathsim/llm.json` written **chmod 600**, opt-in, with a clear "stored in
  plaintext on this device" warning; (d) **session-only** (typed into a masked dialog, kept in
  memory, never persisted); (e) **none** -> fall back to Ollama, else the feature is hidden.
- A small Settings dialog picks the method, pastes a **masked** key, **tests** the connection,
  and **clears** it. The key is the user's own; docs say so and that it is never shipped.
- [x] **LLM provider module** (`breathsim/llm.py` + `breathsim/llm_keys.py`) — **auto-selecting**
      backend: Claude when a key resolves (env -> keychain via `keyring` -> chmod-600
      `~/.breathsim/llm.json` -> session-only, in that order) else **Ollama** (local fallback,
      **off by default / opt-in** so there is no network unless the user opts in) else a null
      provider (`available()` False; `complete`/`chat` raise `LLMUnavailable`). API:
      `available()`, `backend_name()`, `status()` (safe -- backend + key *source*, never the
      key), `complete(prompt, ...)`, `chat(messages, tools=...)`. The key is fetched lazily via
      `llm_keys.resolve()` and **never stored on a provider object** (cannot leak via repr),
      never logged (errors sanitised), never committed/shipped. NO network at import or in
      tests. Unit test `tools/test_llm.py` (passes with no key + no Ollama): null backend when
      empty; a `set_session` key resolves but is never written to disk nor shown in `status()`;
      `mask()` hides all but the last 4; the chmod-600 file store round-trips + `clear()` wipes
      it. Verified: import (no network), the unit test, selftest + both-faces drive; files <500.
- [x] **LLM story generation** (`breathsim/llm_story.py`) — when `llm.available()`, asks the
      model for a sleep story in the lecture **7x12** schema, then treats the reply as
      **untrusted**: parses the JSON, runs `validate()` (7x12 / ASCII / end-punct / fact-free
      section 1 / sleep-closing final) and **repairs** by re-prompting with the specific errors
      (a few times) before rejecting (None). Valid stories register straight into the lecture
      library under the **"AI Stories"** category with an **"AI: "** name prefix (clearly
      labelled, framed atmospheric -- no factual-accuracy claims), so they narrate through the
      ordinary storyteller and can be **saved** to `~/.breathsim` (store `ai_stories`, reloaded
      via `register_saved` from `store.register_all`). Fully gated on `llm.available()` (raises
      `LLMUnavailable` with no backend; the feature is simply absent). Offline test
      `tools/test_llm_story.py` (stubbed completer + temp store, NO network): gating, validator
      accept/reject, the repair loop, and save -> narrate -> persist -> reload -> delete.
      Verified: the test, `tools/test_llm.py`, selftest, both-faces drive; files < 500.
- [x] **LLM structured content** (`breathsim/llm_content.py`) — turns a plain-language request
      into the app's own *data* (no code): a **breathing pattern** -> `BreathPattern` (4 phase
      seconds, ranges clamped, cycle 3-60s) saved via `store.save_pattern`; a safe **breath
      voice** -> a `VoiceConfig` restricted to a whitelisted breath-family field set (unknown
      fields dropped, enums restricted, gain/freq/Q clamped) that is **constructed AND rendered**
      (a few blocks must be finite + non-clipping, gain auto-reduced if it peaks) then saved via
      `store.save_voice`; and a simple **mantra** -> validated letters-only syllables + a real
      tonic note, saved. Model JSON is treated as UNTRUSTED: parse -> coerce/clamp -> construct
      -> (voice) render-check -> repair by re-prompting with errors -> else reject. Gated on
      `llm.available()`; absent with no backend. Offline test `tools/test_llm_content.py`
      (stubbed completer + temp store, NO network): gating; clamp out-of-range; drop unknown
      fields; render-check; reject non-JSON; save + register + reload. Verified: that test + the
      other llm tests + selftest + both-faces drive; files < 500.
- [x] **Quiet helper assistant** (`breathsim/llm_assist.py`) — plain language -> a **whitelist**
      of 9 bounded app actions (set_mode / set_pattern / set_ambience / set_voice / play / pause
      / set_volume / start_story / set_sleep_timer) via `llm.chat(tools=...)`. Returns a
      normalized `{reply, actions, refused}`: a short calm reply + **validated** intents (every
      name checked against the real registries -- modes / `preset_by_name` / `voices.names` /
      story names -- and numbers clamped: volume 0..1, timer 1..180), with everything unknown or
      out of range **refused, never executed**. GUI-free + stateless (the Qt layer maps intents
      to its methods + may voice the reply later -- no GUI change this round). Never runs
      free-form code. Gated on `llm.available()`; absent with no backend; calm, brief, no medical
      advice. Offline test `tools/test_llm_assist.py` (stubbed `llm.chat`, NO network): gating; a
      known action validates/clamps; unknown action / unknown name / out-of-range / off-whitelist
      are refused; only whitelisted actions are ever returned. Verified: that test + all LLM tests
      + selftest + both-faces drive; files < 500.
- [x] **(Optional, advanced, experimental) Sandboxed plugin generation** (`breathsim/llm_plugin.py`)
      — **off by default**; `enable(accept_risk=True)` is required (refuses otherwise). The LLM
      writes a plugin to a **gitignored** `~/.breathsim/plugins` dir (never the repo tree); the
      code is **never executed in the app process**. Each candidate is (1) **statically
      pre-screened** (a denylist rejects subprocess/socket/ctypes/network libs/eval/exec/compile/
      __import__/os.system/exec/remove/write-mode `open` ... before it is even written), then (2)
      **bug-tested in an isolated subprocess** (`python -I`, minimal env with no inherited
      secrets, cwd = plugin dir, hard timeout) that imports it + runs `selfcheck()`, capturing
      stdout/stderr/returncode, with a generate -> test -> repair loop. Even after passing, the
      app does NOT auto-load it -- `loadable()` only exposes manifests; loading stays a separate
      explicit user action. PRIMARY guarantees: opt-in + process isolation + no in-process exec
      (the static screen is defence-in-depth). Marked **Experimental**. Offline test
      `tools/test_llm_plugin.py` (stubbed completer + temp dir, NO network): off-by-default +
      opt-in gate; screen flags dangerous + passes benign; a dangerous plugin is rejected and
      never written; a benign plugin passes in the **subprocess** (its print is captured;
      `plugin_under_test` never enters `sys.modules` in-process); an erroring plugin is caught
      (nonzero rc, no crash). Verified: that test + all LLM tests + selftest + both-faces drive;
      files < 500. **The LLM batch is now complete (5/5).**

### Researched batch — audio & synthesis
- [x] **Generative ambient pad** (user-requested "cosmic music"): new `breathsim/cosmic.py`
      + `breathsim/reverb.py` — a generative engine (Eno/Reich coprime-phasing pads,
      just-intonation consonant scales, steady drone + slow root drift, vowel-formant choir,
      deep-space shimmer) through a block-delay feedback-comb reverb. Three **Cosmic Music**
      voices (Music of the Spheres · Starlight Choir · Deep Space) in the Relax/Sleep
      soundscape picker. Calibrated (~0.75 peak), tonal/consonant + non-repeating; selftest
      + offscreen (both faces) pass.

### Researched batch — cosmic / generative music (expand the engine)
- [x] **True data sonification**: a `_planet_scale()` helper derives a consonant scale from
      the **real planetary orbital periods** (freq ~ 1/period, folded to an octave, snapped to
      just intonation) → a new **"The Planets"** preset (Kepler's harmony of the spheres made
      audible); and the **Pulsar Pulse** beat is now the real **PSR B1919+21** spin (0.748 Hz,
      the first pulsar found). 8 Cosmic Music voices; calibrated, tonal + non-repeating.
- [x] **More presets / themes** (+4): Solar Wind (airy shimmer), Nebula Bloom (lush
      formant chords), Pulsar Pulse (a 0.7 Hz beat), Gravity Well (a click-free descending
      black-hole "ringdown" glide via frequency->phase integration in `_Pad`). Calibrated
      ~0.74 peak; 7 Cosmic Music voices now.
- [x] **Aurora Tones + Saturn Ring Shimmer** presets: ethereal shifting curtains of light +
      icy glittering high tones -> **10 Cosmic Music voices**; calibrated, tonal + non-repeating.
- [x] **Breath-synced harmony**: the Cosmic Music now breathes WITH you — `TextureTrack` feeds
      the breath state to generators that opt in (`wants_state`); `_Cosmic` reads lung volume to
      gently raise pad density, brightness and a click-free level swell on the inhale and settle
      them on the exhale (per-palette `breath` amount). Verified it tracks the breath
      (Solar Wind vol/RMS corr +0.65, slow presets +0.15..0.22), recalibrated, selftest passes.
- [x] **Music menu**: a **Sound ▸ Cosmic Music** submenu lists all 8 generative voices, each
      one click to play it as the ambience bed (`win.set_ambience`); they're also in the
      Relax/Sleep soundscape pickers. (A full first-class "Music" *mode* with key/scale/space
      sliders is still open as a stretch.)
- [x] **Add reverb as a shared send** — superseded by the **master** design: `SpaceReverb`
      is applied to the whole mix buffer (`engine._callback`: `buf = self.space.process(buf)`),
      so when a space (Room/Hall/Cathedral) is selected the bowls, chimes, drone and every
      ambience already sit in it. A separate per-slot send would duplicate this for no real
      gain, so the master send stands.
- [x] **More ambiences** (+5): Rain on a Tent · Wind in Pines · Fan (White Noise) [NoiseTrack]
      and Womb Heartbeat · Whale Song [new `textures.py` generators], all GROUP_NATURE in the
      soundscape picker. Calibrated (300 s peak <= 0.78). **147 voices.**
- [x] **Slow-wave pink pulses** (`textures._SlowPulse` -> "Slow-Wave Pulse" ambience): a warm
      pink+brown noise wash amplitude-modulated by a gentle ~0.8 Hz swell (about 48/min), framed
      honestly (open-loop soothing, not EEG-locked). Calibrated (300 s peak 0.75); the envelope
      FFT confirms 0.80 Hz; in the soundscape picker. 148 voices.
- [x] **Gong bath / tuned bowl set** (user-requested, delivered by `synth_bell.py`): a
      physically-grounded struck-resonator engine + 12 instruments (Meditation/Temple/Church/Hand
      Bell, Tibetan + Crystal + Sung Bowl, Tam-tam + Nipple Gong, Triangle, Tingsha, Tubular Bell)
      that toll slowly as a meditation/chant/ambience bed - in the soundscape picker + a Sound
      menu. Hemony bell partials, gong bloom, bowl beating; calibrated; selftest passes.

### Researched batch — instrument & effect synthesis (user-requested "sonorous sounds")
- [x] **Drums** (`synth_drum.py`): a membrane/percussion synth (pitched modes with a downward
      pitch glide + a noise attack transient), struck on a slow tempo. 7 drums - Frame Drum,
      Taiko, Tabla, Djembe (bass/slap), Log Drum, Woodblock, Bodhran - in a new GROUP_DRUMS, in
      the effects-slot picker + a Sound > Drums menu. Calibrated ~0.72 peak; selftest passes.
- [x] **Whistles / organs / horns** (`synth_wind.py`): sustained additive sources - `_Organ`
      drones (Pipe Organ, Harmonium/Shruti, Reed Organ, Wooden Flute - harmonics + tremulant +
      beating + chiff) and `_Horn` periodic blasts (Train Whistle as a 4-pitch chord, Fog Horn,
      Ship Horn - slow swell). 7 voices in a new GROUP_WIND, in the ambience picker + a Sound menu.
      Calibrated; FFT confirms the spectra; selftest passes.
- [x] **Rhythmic / environmental FX** (`synth_fx.py`): composite filtered-noise + event
      generators - Train (Steam/Diesel: clickety-clack + rumble + chuff), Ship / Harbour (hull
      wash + creaks + far horn), Thunderstorm (rumble bed + soft thunder rolls), Ocean Buoy Bell
      (irregular tolling over a sea wash). 5 voices in a new GROUP_FX, in the ambience picker + a
      Sound menu. Calibrated (300 s peak <= 0.75); selftest passes. **Instrument suite complete:
      Bells & Gongs + Drums + Winds & Organs + Environmental FX = 31 synthesised voices.**
- [x] **Spatial polish** (`breathsim/spatial.py`): gentle, peak-safe stereo width + a very slow
      (~0.02 Hz) auto-pan on the ambience bed. Widening is a complementary-comb pseudo-stereo
      (each channel a *convex* blend of itself + a short, differently-delayed copy of the other),
      so it decorrelates L/R — even mono beds gain width — while a convex combination can never
      exceed the input peak; the auto-pan only ever attenuates one side, so calibrated peaks are
      untouched. Wraps the `ambience` layer in `engine.set_voice`; **Sound > Spatial width** toggle
      (default on, persisted). Done: selftest passes; 300 s spatialized peak <= dry peak and <= 0.95
      on Rain/Slow-Wave/Ocean/Forest with L/R correlation dropping to ~0; offscreen both faces,
      ambience layer wraps/unwraps on toggle, thread-stable.

### Researched batch — engagement & structure
- [x] **Streaks + calendar heatmap** in Stats: `store` now keeps a per-day practice log
      (`days`), with pure helpers `daily_minutes()`, `streak()` (current + best consecutive days;
      an un-practised today doesn't break it), `week_minutes()`. New `vesper/stats_heatmap.py` adds
      a kind streak line ("3 days in a row - lovely"), this-week minutes, and a GitHub-style
      13-week day grid shaded by minutes (theme colours), with a friendly empty state - shown in
      the Practice Stats dialog. Pure helpers unit-tested; heatmap PNG verified; selftest passes.
- [x] **Mood check-in** (`vesper/mood.py` + `store` mood log): a gentle, optional, skippable
      1-tap picker (Tense..Serene -> 1..5) offered at the start of a fresh non-Sleep sit and when
      it ends (never during Sleep, so it can't wake a sleeper); a **Sound > Mood check-ins** toggle.
      `store.log_mood/mood_entries/mood_summary` (avg before/after/shift); a kind trend line in
      Practice Stats ("you usually feel a little calmer afterwards"). Unit-tested; selftest passes.
- [x] **Multi-night courses** (`breathsim/courses.py`): optional guided sequences over days, each
      day reusing an existing program or mode + a one-line intention. Three courses — **7 Nights to
      Sleep**, **Ten Days of Calm**, **Five Mornings to Energize**. Per-course progress persists in
      `store` (`courses.json`: `course_day`/`advance_course`/`reset_course`) and advances **honestly**
      — only when a session actually completes (hooked in `_log_practice`, the >=30 s sit gate).
      Sessions > **Courses (multi-night)** submenu shows live progress (e.g. "Night 3/7") + Restart.
      Honest framing (gentle structured practice, not clinical). Done: selftest passes; course model
      + persistence round-trip unit-tested; offscreen both faces — mode & program days apply, advance
      only on a real sit, short sits don't advance, thread-stable.
- [x] **Launch suggestion** (`vesper/suggest.py`): a gentle, non-modal hint on launch. Pure +
      testable `suggest(hour, history, courses_state, today)` -> a `Suggestion(text, action, kind)`:
      an in-progress multi-night course wins ("Pick up 7 Nights to Sleep - Night 3 of 7"), else a
      friendly time-of-day mode (via `clocktheme.suggested_mode_for_hour`) coloured by streak /
      fresh-user / practised-today. Shown as a one-line message in the **idle status bar** until the
      first Start, then it retires (no nag, no popup). Honest: a hint, not advice. Done: selftest
      passes; helper unit-tested (morning/night, fresh vs 3-day streak vs mid-course vs completed);
      offscreen both faces — suggestion produced on launch with no blocking dialog, shown while idle,
      retired after Start, thread-stable.
- [x] **Sleep-timer auto-stop** (`vesper/sleeptimer.py`): an optional timer that gently fades the
      sound out (a ~30 s ramp on the master volume) and then pauses the session after a set time, so
      you can fall asleep without the audio playing all night. Off by default; Off / 15 / 30 / 45 /
      60 min in the **Sleep wind-down card** and a **Sound > Sleep timer** submenu. Reuses the
      per-frame loop + the master-volume path (no second clock); counts from when armed/started and
      restarts each fresh session; stops the narrator + pauses via the existing path. Honest: it just
      fades + pauses. Done: selftest passes; pure `fade_gain`/`remaining` unit-tested; offscreen both
      faces — full volume before the mark, ~half mid-fade, silent + paused after, thread-stable.
- [x] **Richer Stats insights** (`breathsim/insights.py`): gentle, honest summaries computed from
      the existing logs — total sessions/minutes, average sit length, your usual **time of day** and
      most regular **weekday**, and a **week-over-week** minutes line — all pure + unit-tested with
      injected history, with graceful empty states (a new user just sees fewer lines). Added an
      honest **hour histogram** to `store.log_session` (older histories without it skip the
      time-of-day line, no overclaiming). Shown as a few calm lines in the Practice Stats dialog.
      Done: selftest passes; helpers unit-tested (empty/new, a week of data, mood, week-over-week);
      offscreen both faces build the Stats widget without a blocking exec, thread-stable.
- [x] **Accessibility — text size** (`vesper/fontscale.py`): a global UI text-size scale (Small /
      Normal / Large / Extra-large -> 0.85 / 1.0 / 1.25 / 1.5) via **View > Text size**. Scales the
      Qt application font *and* the theme stylesheet's `font-size` values (only font sizes, so layout
      stays stable; dialogs and menus inherit `win.styleSheet()`). Persisted as `font_scale`,
      restored on launch. Honest: a readability setting. Done: selftest passes; `scaled_css`/labels
      unit-tested (geometry preserved); offscreen both faces — each size scales the app font (e.g.
      9->11.2 pt at Large) and the stylesheet (13->16px), persists, thread-stable.
- [x] **Export / share a session summary** (`breathsim/summary.py` + `vesper/session_export.py`): a
      small friendly summary of a sit + overall practice (date, this-sit duration/mode, all-time
      sessions/minutes, current streak, a kind note) you can save as **text** or a themed **PNG card**.
      `summary_lines`/`summary_text` are pure (last-session dict + `store` history/streak), with a
      graceful new-user empty state; the exporters mirror `save_screenshot`/`export_wav` (save dialog,
      status-bar report, never crash). **File > Export Session Summary / Save Summary Card (PNG)**.
      Honest: it only summarises logged data. Done: selftest passes; builder unit-tested (new vs
      logged, short-sit guard); offscreen both faces write a non-empty .txt + .png, thread-stable.
- [x] **Richer Sleep night scene** (`vesper/scenes.NightScene`): deeper, calmer night visuals — a
      **far parallax star layer** (smaller/dimmer/slower with gentler twinkle), a **faint horizon
      glow** (very dim deep-indigo band low on the sky, never bright), and a **subtle moon crescent**
      (a sky-coloured disc carves a slowly-drifting terminator into a gentle phase). All driven by
      the existing `anim_t` (no new clock), low-contrast/melatonin-friendly, respecting the
      Sleep/clock warm+dim overlay. Done: selftest passes; `scenes.py` stays 430 lines; offscreen
      both faces render the night scene (564x557) to non-empty PNGs that change frame-to-frame,
      thread-stable.
- [x] **Breathing-pattern visual guide** (`vesper/pattern_bar.py`): a compact phase diagram in the
      pattern card. Pure `segments(pattern)` -> the non-zero inhale/hold/exhale/hold phases with
      their seconds + width fractions; `PatternBar` paints them proportional, tinted with the theme
      per-phase hues, each labelled with its duration, and softly highlights the **live phase** while
      running (refreshed via the panel `sync`/`tick`). Honest: it just visualises the numbers. Done:
      selftest passes; `segments` unit-tested (4-7-8 -> 3 segments / correct fractions, zero-holds
      -> 2, box -> 4 equal); offscreen both faces show the bar, switching patterns updates the
      segments, the live phase highlights, thread-stable.
- [x] **Per-voice favourites** (`store` + `vesper/menus._voice`): star/pin favourite voices for
      quick access. `store.favourites()`/`is_favourite()`/`toggle_favourite()` persist a de-duplicated,
      order-preserving list in `favourites.json`; `app.toggle_favourite_voice()` stars/unstars the
      current inhale voice and reports it. The **Voice menu** gains a **Favourites** submenu (quick
      `set_voice_a`, only listing voices that still exist) and a **Star/Unstar "<voice>"** action.
      Honest: a convenience shortcut. Done: selftest passes; helpers unit-tested (add/remove,
      is_favourite, empty no-op, dedupe, persistence round-trip); offscreen both faces — starring
      persists, the menu builds with favourites present and empty, selecting a favourite sets the
      inhale voice, thread-stable.
- [x] **Keyboard-shortcut help overlay** (`shortcuts.SHORTCUTS` + `dialogs.open_shortcuts`): a calm
      "?" cheatsheet of the REAL bindings, defined once next to `shortcuts.bind` so it can't drift
      (Space / R / V / F / Z / Esc + "?" + the Ctrl+S / Ctrl+Q menu accelerators). Opened by the new
      **"?"** shortcut and **Help > Keyboard Shortcuts**; a themed, modeless dialog (uses `show()`,
      never a blocking exec, so it's offscreen-safe). Honest: it just lists the bindings. Done:
      selftest passes; `SHORTCUTS` unit-tested (non-empty, well-formed); offscreen both faces build
      the dialog without a blocking exec, every key + description is listed, thread-stable.
- [x] **Calmer first-frame fade-in** (`vesper/introfade.py`): the window arrives softly — its opacity
      eases from 0 up to full over ~1.1 s (smoothstep) on launch, then yields to the normal opacity
      logic. `intro_opacity(elapsed)` is pure; `window._tick` computes the normal opacity (`op`) then
      multiplies by the intro factor and records `self._win_op`. Coordinates with — doesn't fight —
      the Sleep dim, clock warmth and Sunrise brightening (they set the base, the intro just scales it
      for the first second). Done: selftest passes; `intro_opacity` unit-tested (floor at 0, 1.0 past
      duration, monotonic); offscreen both faces — opacity starts <1 and reaches the normal value,
      Sleep dimming still applies afterward, thread-stable.
- [x] **Session-end "well done" moment** (`breathsim/welldone.py`): a brief, kind closing line when a
      real sit completes. Pure `message(minutes, streak)` -> e.g. "Session complete - 12 minutes. 3
      days in a row. Be well." (singular/plural, streak only when >=2). `window._log_practice` sets
      `self._closing_msg` once (the >=30 s sit gate; **not** during Sleep, so a sleeper isn't
      jarred); `_update_status` shows it in the idle status bar until the next fresh Start clears it
      — non-modal, no dialog, no sound. Honest: it just acknowledges a finished sit. Done: selftest
      passes; `message` unit-tested (short None, singular/plural, with/without streak); offscreen both
      faces — a finished sit shows the line once with no blocking dialog, a fresh start clears it,
      Sleep stays silent, thread-stable.
- [x] **Richer Relax wave scene** (`vesper/scenes.WaveScene`): deeper, calmer sea visuals on top of
      the existing swells/stars/moon — a **faint horizon glow** band at the waterline (a soft
      water+moon tint, alpha <=0.16) and a **moonlight glint column** down the sea below the moon (a
      vertical MOON gradient that fades out, its width **breathing a touch with the breath volume**),
      under the existing shimmer + foam. Driven by `anim_t` (no new clock), low-contrast, respecting
      the theme palette + warm/dim overlay. Done: selftest passes; `scenes.py` stays 440 lines;
      offscreen both faces render the wave scene (564x557) to non-empty PNGs that change
      frame-to-frame, thread-stable.
- [x] **"Tonight's pick" — one-tap random lecture** (`breathsim/tonight.py` + `app.tonights_pick`):
      pick a random bedtime lecture from the 129-strong library, gently avoiding recently-heard ones,
      and start the Sleep story in one tap. Pure `pick(names, recent, rng)` (deterministic with a
      seeded rng, falls back when all are recent, None on empty); `store.recent_picks`/
      `push_recent_pick` keep the last 5 so it doesn't repeat night to night. Surfaced as a Sleep
      story-card **"Surprise me - tonight's pick"** button + **Sessions > Tonight's pick (random
      story)**; reuses the existing `set_story` + `_ensure_running` plumbing. Honest: it just picks at
      random. Done: selftest passes; `pick` unit-tested (deterministic, avoids recent, fallback,
      empty); offscreen both faces — the action switches to Sleep, arms a real lecture, starts, and
      records the pick, with no blocking dialog, thread-stable.
- [x] **Sleep-onset "lights out" auto-dim** (`vesper/sleepdim.py`): the very end of the Sleep
      wind-down now eases the screen toward near-dark. Pure `sleep_dim(prog, knee=0.85, floor=0.55)`
      is exactly the old curve (1 - 0.3*prog) below the knee, then smoothsteps to the floor past it
      (a continuous join), so the window opacity settles around ~0.55 by session end — gentle, never
      fully off, fully reversible (reset / fresh start / leaving Sleep recomputes it), and coordinated
      with the launch intro-fade + warm overlay. Honest: a visual dim, not a power-off. Done: selftest
      passes; `sleep_dim` unit-tested (knee continuity at 0.745, deeper past it, monotonic, floor
      0.55); offscreen both faces — opacity is ~0.85 mid-session and ~0.57 deep in the wind-down, and
      returns to ~0.96 after reset, thread-stable.
- [x] **Breath-rate (pace) insight** (`store.log_session` bpm + `breathsim/insights`): each logged
      session now also records its breaths-per-minute (60 / the pattern's cycle), an optional field
      older entries simply lack. `insights.avg_bpm`/`pace_line` average it into a kind, honest line
      ("You tend to breathe around 6 a minute - a calm, resonant pace" for the ~4-7/min resonance
      range, plain otherwise), shown in Practice Stats; no line without data. Honest: descriptive, and
      resonance is a gentle note not a prescription. Done: selftest passes; helpers unit-tested
      (no-data None, average, resonance note vs fast, lines() inclusion); offscreen both faces — two
      logged sits record bpm and the Stats widget shows the pace line, thread-stable.
- [x] **Ambience auto-rotate** (`breathsim/ambrotate.py` + `window._apply_ambience_rotate`): an opt-in
      mode that slowly cycles the ambience through a curated set of calm GROUP_NATURE beds (Ocean
      Waves / Gentle Rain / Forest Wind / Mountain Stream / Night Crickets / Soft Rainstorm) every
      ~6 min, reusing the engine's gain-ramped crossfade. Pure `next_ambience(beds, elapsed, period)`
      (deterministic, wraps, empty/single-tolerant). Driven off the per-frame loop + controller
      elapsed (no new clock) and **suppressed while the Sleep storyteller is active** so it never
      fights the story cues. Off by default, persisted (`ambience_rotate`); toggled in the
      Relax/Sleep soundscape card + **Sound > Auto-rotate ambience**. Honest: it just rotates the bed.
      Done: selftest passes; `next_ambience` unit-tested (period boundaries, wrap, single, empty,
      negative); offscreen both faces — beds advance per period (Ocean Waves -> Gentle Rain ->
      Forest Wind), hold stable when off, are suppressed under the storyteller, thread-stable.
- [x] **Voice loudness-consistency audit** (`tools/loudness.py`): a read-only offline tool that
      renders each bed in a voices group for a fixed time and reports peak + rms, flagging rms
      outliers (>2x / <0.4x the group median). Ran it on the ambience beds (the set the soundscape
      switches between): all **21** GROUP_NATURE beds already sit within **0.64x-1.36x** the median
      rms (0.12), every peak <= 0.75 — i.e. no jarring outliers — so **no gains were changed**
      (the honest outcome; the calibrated gains stand). Done: tool added + numbers recorded; selftest
      peaks <= 1.0 unchanged; offscreen both faces thread-stable.
- [x] **Richer Chant ripple scene** (`vesper/scenes.RippleScene`): deeper resonance visuals on top
      of the existing breath-spawned rings + breath-pulsing central glow — a soft **still-water
      radial sheen** that gently **colour-drifts with the breath phase hue**, and a faint **companion
      ripple** just inside each ring for an interference-like richness (alpha fading as the ring
      ages). Low-contrast, driven by the existing `anim_t` / volume / phase, on the RIPPLE_BG theme.
      Done: selftest passes; `scenes.py` stays 449 lines; offscreen both faces render the ripple scene
      (564x557) to non-empty PNGs that change frame-to-frame, thread-stable.
- [x] **Soundscape preset save/recall** (`store` soundscapes + `vesper/soundscape_presets`): save a
      named, light **sound-only** mix (ambience + level, effect + level, master volume, spatial &
      auto-rotate flags) and recall it in one tap — separate from the full Presets system.
      `store.save/list/get/delete_soundscape` (soundscapes.json); `capture(win)`/`apply(win, mix)`
      reuse the normal setters and **skip voices no longer in the registry**. Surfaced in the
      Relax/Sleep soundscape card (a saved-mixes combo + Save current… / Delete). Honest: it just
      stores names + levels. Done: selftest passes; store round-trip unit-tested (save/list/get/
      delete); offscreen both faces — save a mix, change it, recall restores ambience/level/rotate,
      unknown voice tolerated, thread-stable.
- [x] **Gentle Meditate orb enrichment** (`vesper/scenes.OrbScene`): two subtle, serene touches
      behind the breath orb — a faint **phase-hue ambient vignette** that tints the dark field and
      breathes with the orb's volume, and a soft, flattened **floor-reflection bloom** beneath it (as
      if it rests on stillness). Low-contrast, driven by the existing `anim_t` / volume / phase; the
      guide dot, exhale rings, coherence halo and progress arcs are untouched. Done: selftest passes;
      `scenes.py` stays 466 lines; offscreen both faces render the orb scene (564x557) to non-empty
      PNGs that change frame-to-frame, thread-stable.
- [x] **Per-mode voice/ambience memory** (`store` mode_prefs + `apply_mode`): each mode now remembers
      the inhale voice (and ambience) you last chose in it and restores it on return, instead of
      always snapping back to the preset. Explicit user changes via `app.set_voice_a`/`set_ambience`
      are recorded per `current_mode` (a `_applying_mode` guard ignores the preset's own calls);
      `apply_mode` overrides the preset with the remembered, registry-checked value (ambience skipped
      during the Sleep storyteller). `store.mode_prefs/get_mode_pref/set_mode_pref` (mode_prefs.json).
      A fresh user behaves exactly as before. Done: selftest passes; store round-trip + behaviour
      unit-tested; offscreen both faces — a customised Meditate voice survives a switch away and back,
      an untouched mode keeps its preset, applying a mode records nothing, thread-stable.
- [x] **Quiet-hours auto-volume cap** (`clocktheme.quiet_cap` + engine `vol_cap`): late at night the
      output volume is gently capped so a 2am session isn't jarring. Pure `quiet_cap(hour)` (1.0 by
      day, easing to a ~0.6 floor in the small hours, never >1.0, never mutes); the engine grows a
      `vol_cap` **upper bound** applied in `set_master_volume` (`set_volume_cap` re-clamps live), so
      the user's chosen volume is preserved while the *output* ceiling drops -- and it composes with
      (never fights) the Sleep wind-down / sleep-timer fades, which only ever lower further. `window`
      updates the cap each tick from the clock; **Sound > Quiet hours (auto-soften late)** toggle,
      default on, persisted. Done: selftest passes; the curve is unit-tested; offscreen both faces —
      at 2am the engine target is capped to 0.6 with `user_volume` still 0.8, off/by-day it equals
      0.8, thread-stable.
- [x] **Session-history export** (`breathsim/history_export.py`): export your practice log as a
      portable **CSV** (one row per day: date, minutes, sits) with a summary block (total sessions/
      minutes, current & best streak, avg breaths-per-min, mood shift) or a friendly **text** report
      (reusing `store.streak`/`insights`/`mood_summary` so figures match the Stats dialog). Pure +
      testable; **File > Export Practice History (CSV)…** picks .csv or .txt and mirrors the existing
      export dialogs (save dialog, status report, never crash). Honest: it just writes your logged
      data. Done: selftest passes; the builder is unit-tested (empty -> header + zero summary / note,
      populated -> correct daily rows + summary + bpm); offscreen both faces — two logged sits write a
      non-empty .csv (header + total_sessions,2) and .txt, thread-stable.
- [x] **Blackout sleep view** (`window.toggle_blackout` + shortcut/menu): a near-dark sleep screen —
      hides the panel/menu/status and dims the window right down (opacity ~0.05, **never 0**) while
      the sound + controller keep running, so the room stays dark. Reversible by **B**, **Esc**, a
      **tap** (mousePressEvent), or the toggle; **View > Blackout (sleep)** + the "?" cheatsheet.
      Reuses the Zen-style chrome hiding and the existing `_win_op` opacity path (clamped after the
      intro-fade/sleep-dim so they don't conflict). Honest: a visual dim, audio unaffected. Done:
      selftest passes; offscreen both faces — toggle on hides chrome and drops opacity to ~0.05 with
      the session still running, toggle/Esc/tap restore (~0.98), thread-stable.
- [x] **Breathing-coach count cue** (`breathsim/coach.py`): an optional on-screen cue that names the
      phase and counts through it — "Breathe in 3", "Hold 2", "Breathe out 2", "Rest" — synced to the
      live pattern, to help a beginner follow the rhythm. Pure `cue(phase, phase_elapsed, phase_len)`
      (1-based count, capped at the phase length, "" for zero-length phases). `window` feeds it into
      the scene subtitle when enabled (and not during the Sleep storyteller). **View > Breathing count
      cue** toggle, default off, persisted. Honest: it just narrates the pattern timing. Done: selftest
      passes; `cue` unit-tested (counts/caps/zero-length); offscreen both faces — a cue string appears
      when on and is absent when off, thread-stable.
- [x] **"Fall asleep" one-tap preset** (`app.start_fall_asleep`): one action sets up the honest best
      combination for drifting off — Sleep mode + a slow long-exhale pattern (Calming 4-6) + the
      wind-down + a ~40-min sleep-timer + (if available) the storyteller — then starts, composing
      EXISTING features (no new audio). A **Fall asleep** button on the Sleep wind-down card + a
      **Sessions > Fall asleep (one tap)** item. Idempotent and reversible (Reset / switching modes
      returns to normal). Honest: it just configures sleep features. Done: selftest passes; offscreen
      both faces — leaves the app in Sleep + Calming 4-6 + wind-down armed + a sleep-timer set +
      running with no blocking dialog, and switching modes clears the wind-down, thread-stable.
- [x] **"Resume where you left off" launch hint** (`vesper/resumehint.py` + window + store): on launch
      a calm status-bar line names your last session — "Last time: Sleep with \"The Alhambra\"" or
      "Welcome back to Meditate" — so picking up is one glance away. Pure `resume_hint(settings)` reads
      the saved `mode` (and, for Sleep, the persisted `last_scene`) and returns the phrase, or None when
      there's nothing meaningful (no mode / blank / non-dict). `store.save_settings` is now a
      read-modify-write **merge** (a partial patch like `{"last_scene": ...}` never clobbers other
      keys); the window persists `last_scene` on close and when a story starts. The hint folds into the
      existing launch-suggestion line (`window.__init__`), shown via the idle status bar until the first
      Start and never as a dialog; an in-progress course still wins the line. Honest: just a reminder of
      your last session, no claims/nagging. Done: selftest passes; `resume_hint` unit-tested
      (None/blank/non-dict; mode-only -> "Welcome back to <mode>"; Sleep+scene names it; empty/Off/None
      scene + non-Sleep mode handled; whitespace trimmed) and `save_settings` merge round-trip tested
      (partial patch keeps prior keys); offscreen both faces — a seeded prior settings file shows the
      hint idle, it's retired after Start, and close persists every key incl `last_scene`, thread-stable.
- [x] **Lecture-branch "surprise me within this branch" picker** (`breathsim/branchpick.py` + window +
      menu): you can now pick a random bedtime lecture from ONE theme, gently avoiding repeats. Pure
      `pick_in_branch(category, recent, rng)` composes `lectures.names(category)` with the existing
      `tonight.pick` (prefers a name not in `recent`, falls back when all are recent, deterministic with
      a seeded rng, None for an empty/unknown branch). `window.surprise_in_branch(category)` mirrors
      `tonights_pick`: it picks, records via `store.push_recent_pick`, switches to Sleep, arms the story
      scene, and begins. A **Sessions > Surprise me in branch > <branch>** submenu lists every category.
      Honest: just a random pick within a theme, no claims. Done: selftest passes; `branchpick`
      unit-tested (unknown/empty -> None; real branch returns a member; all-but-one recent -> the
      non-recent one; all recent -> still valid; seeded rng deterministic; single-name via tonight.pick);
      offscreen both faces — `surprise_in_branch("Famous Bridges")` arms a valid in-branch scene + records
      it + enters Sleep, recent-avoidance holds, the menu rebuilds with the branch submenu, an unknown
      branch is a safe no-op, thread-stable.
- [x] **Gentle "longest streak" line in Stats** (`breathsim/insights.py`): the Stats dialog now gently
      celebrates your best run of consecutive practice days, e.g. "Your longest streak: 6 days", with a
      kind "- and you are on it now" nod when the current streak equals the best (and > 1). Pure
      `streak_line(hist, today)` reads `store.streak` (current, best), returns None when best < 2 (a
      lone day isn't a streak), pluralises day/days, and is surfaced via `insights.lines()` near the
      week-over-week line. Specifically about the *best* run, so it doesn't duplicate the heatmap's
      current-streak number. Honest: just a record of consecutive days, no pressure/claims. Done:
      selftest passes; `streak_line` unit-tested (empty/lone-day -> None; past 2-day run -> the line;
      current==best>1 -> the "on it now" nod; best>current -> no nod; pluralisation; lines() includes it
      exactly once; new user -> no lines); offscreen both faces — a seeded 3-day run shows the line in
      the Stats insights widget and a lone day shows nothing, thread-stable.
- [x] **Gentle Stats "this month" total** (`breathsim/insights.py`): the Stats dialog now shows a calm
      tally of the current calendar month, e.g. "This month: 7 sits, 84 min", right after the all-time
      total. Pure `this_month(hist, today)` sums sits + minutes over the per-day log entries falling in
      `today`'s month (ignoring prior/next months and malformed date keys), pluralises sit/sits, rounds
      minutes, and returns None for an empty month so a new user sees nothing. Surfaced via
      `insights.lines()` so it renders in the Stats insights area. Honest: just a tally of this month,
      no goals/claims. Done: selftest passes; `this_month` unit-tested (empty/prior-only -> None;
      this-month summed with out-of-month + malformed keys excluded; "1 sit" singular; minute rounding;
      minutes-only; lines() placement right after the total; new user -> no lines); offscreen both
      faces — the line appears in the Stats insights widget after a few seeded sits and is absent for a
      new user, thread-stable.
- [x] **Stats "best time of day" nudge** (`breathsim/besttime.py` + insights): the Stats dialog now
      gently names when you tend to practise, e.g. "You most often practise around 9-10 pm". Pure
      `best_time_phrase(hours, min_total=5)` reads the practice-history hour histogram, finds the modal
      hour, grows it to an adjacent window when a neighbour is also well-used, and formats it in 12-hour
      am/pm wording (with noon/midnight + meridian-crossing handled); returns None when too sparse
      (total < min_total or no clear mode), so a new user sees nothing. `insights.lines()` shows it in
      place of the coarse "in the evening" line when a clear mode exists, so it renders in the Stats
      dialog's insights area. Honest: it's only an observation of when you practise, no advice/claims.
      Done: selftest passes; `besttime` unit-tested (sparse->None, single modal hour, adjacent grouping
      left/right, noon/midnight + 11pm-12am crossing, junk-tolerant, min_total override, and the
      insights upgrade/suppression); offscreen both faces — with a seeded clear mode the line appears in
      the Stats insights widget and is absent when history is sparse, thread-stable.
- [x] **Breathe-with-me intro countdown** (`breathsim/intro.py` + window): on a fresh start, a brief
      "settle in" lead-in plays over the first breath so the very first inhale isn't abrupt. Pure
      `intro.schedule(cycle_seconds)` lays a few calm lines ("Settle in." -> "We'll begin together.")
      across ~one breath cycle (clamped to a readable 8-12 s); `line_at(sched, t)` / `duration(sched)`
      drive it. `window._arm_intro(fresh)` builds it only on a fresh start (and not when the Sleep
      storyteller is about to speak — its narration is its own lead-in); `_intro_text()` surfaces the
      current line in the status bar AND the scene subtitle, then auto-clears so normal status resumes.
      Skippable (a click skips it; pause/reset clears it) and toggleable — **View > Settle-in lead-in**,
      default on, persisted (`intro_lead_in`). Honest: purely on-screen text — no audio, no timing
      change, no claims. Done: selftest passes; `schedule`/`line_at`/`duration` unit-tested (clamping,
      order, contiguity, expiry, empty/None/custom lines); offscreen both faces — the lead-in arms on a
      fresh non-story start and shows "Settle in." in status + subtitle, expires and clears on its own,
      a click skips it, the setting off never arms, and a Sleep storyteller suppresses it, thread-stable.
- [x] **Per-lecture resume** (`lectures.units` start_section + `breathsim/resume.py` + store): a long
      lecture you didn't finish gently resumes near where you left off. `lectures.units(name, ...,
      start_section=0)` (default unchanged) skips earlier sections and stamps each unit with its
      `section`; `window._on_story_unit` records the narrated section to `store.lecture_progress`
      (throttled, cleared on finish), and `_start_story` uses pure `resume.start_section(entry, total,
      today)` to resume only when you got a fair way in (past ~section 2), not basically finished, and
      recently (<=14 days) — else it starts fresh. Honest: it just remembers a rough spot. Done:
      selftest passes (units default + story lengths unchanged); start_section/resume/store unit-tested
      (skip, clamp, too-early/finished/stale -> fresh); offscreen both faces record progress, clear on
      finish, and resume at the saved section, thread-stable.
- [x] **First-run onboarding** (`vesper/onboarding.py`): a gentle, skippable 4-step welcome shown
      once on first launch (persisted `onboarded` flag), re-openable from **Help > Welcome /
      Getting Started**. Modeless (uses `show()`, never a blocking `exec()`) and `maybe_show` never
      auto-pops in an offscreen/headless run, so tests and offline renders stay quiet. Done:
      orients to what Vesper is + the mode bar + play + the menus; selftest passes; offscreen both
      faces — no auto-pop on build, re-open + flag-persist verified, thread-stable (1->2).

### Researched batch — storyteller
- [x] **Best voices + British-female default** (user-requested): the default narration voice is
      now **Kokoro `bf_emma` (British female)** - reordered `kokoro_tts.RELAXING` (British females
      first) and the macOS `say` fallback (UK females first; `_say_best` prefers a UK female), and
      default the spoken-cue voice to a UK female too. The Sleep "Narration voice" picker now shows
      **friendly labels with accent/gender and a ★ on the most realistic** (e.g. "★ Emma -
      British female"), best-first. Research (offline TTS): **Kokoro** is the right shipping engine
      - 300 MB, faster-than-real-time on CPU (~45 ms first chunk vs XTTS ~320 ms), Apache, #1 on
      TTS Arena, true British voices; **Fish Speech** (12-16 GB GPU) and **XTTS/Coqui** (2-8 GB
      VRAM, ~1.8 GB, sub-real-time on CPU) are higher-ceiling for cloning/emotion but break the
      offline/laptop/graceful-degrade guarantees - documented as an optional future engine below.
- [x] **Optional high-fidelity neural engine** — XTTS-v2 wired as an opt-in engine
      (`xtts_tts.py` + `xtts_worker.py`, persistent subprocess in a separate venv;
      `narration` lists its voices, routes per-voice, degrades to Kokoro/`say`).
      Faster-than-real-time on MPS; non-commercial CPML; see `docs/XTTS.md`. Done.
- [x] **Calm visuals (reduce motion)** (accessibility + sleep efficacy, off by default): a global
      View-menu toggle for motion-sensitive users and for lowering pre-sleep visual stimulation.
      Implemented at the single `viz` chokepoint: `VizWidget.update_state` feeds scenes a virtual
      decorative clock that runs at 15% when on (so star drift / twinkle / motes / flicker / ripples
      all ease at once, no per-scene edits), while the breath-driven orb + guide dot (volume /
      cycle_frac) stay live; `paintEvent` also drops the busy weather overlay. Monotonic across a
      session reset. Wired via `window.set_calm_visuals` (-> `viz.set_calm` + persist), `_calm_visuals`
      default, `win_settings` round-trip, and a View toggle in the accessibility cluster. Verified:
      `tools/test_calm_visuals.py` (clock off=real / on=15%, breath terms untouched, weather gated,
      monotonic) + offscreen GUI smoke (menu present, handler->viz, persists, threads stable) +
      selftest + drive_check; all 20 offline tests green.
- [x] **Optional spoken name**: greet/settle the listener by name (off by default). New
      `vesper/greeting.py` (pure + tested): `sanitize_name` (NFKD ASCII-fold → letters/space/`-`/`'`
      only, 24-char cap, `''` = off), `greeting_line(name, hour)` (one soft, time-aware line —
      morning/afternoon/evening/night, `None` without a name), and `prepend(line, units)` (a lazy
      generator that yields a `kind:"greeting"` unit, then the story stream). Wired into
      `win_story._start_story` so the storyteller speaks the greeting **once** at a fresh session
      start (guarded by `_greeted_session`, reset in `toggle_transport`; never repeated on a
      mid-session voice/scene change), plus `app_actions.set_listener_name`/`ask_listener_name`, a
      Sessions menu action ("Greet me by name…"), and settings round-trip. The name is the user's
      own, kept on-device, sanitised before it is ever spoken/shown. Verified: `tools/test_greeting.py`
      (sanitize/greeting_line/prepend) + offscreen GUI smoke (sets + persists the name, greeting
      injected once then not repeated, none when empty, menu present, threads stable across 45 ticks)
      + selftest + drive_check; all 19 offline tests green.
- [ ] **Narration language**: expose Kokoro's languages/voices where available.

## Stories (ongoing — every ~3rd round)
- [x] **New branch — Great Libraries** (4): The Library of Ashurbanipal · The House of Wisdom · The
      Monastic Scriptorium · The Libraries of Timbuktu — added `lectures_{ashurbanipal,houseofwisdom,
      scriptorium,timbuktu}.py` (7x[13,12,13,12,12,13,13] lines, fact-free section 1, accurate history —
      Nineveh's cuneiform clay tablets baked by the fire that destroyed the city; Baghdad's translators,
      al-Khwarizmi, paper, the 1258 ruin with the "ink-black Tigris" framed AS uncertain story; monks
      preparing vellum + quill + months of copying + marginalia; Timbuktu's Sankore scholars and family
      manuscript collections, the "mythical place" idea framed AS misconception), ASCII, every section
      sleep-closing; ambiences Distant Thunder / Gentle Rain / Rain on a Roof / Night Crickets. NOTE:
      "The Library of Alexandria" already exists (Histories), so **Timbuktu was substituted** to avoid a
      duplicate; also reverted a subagent's stray add of Scriptorium into "The Quiet Crafts" (kept it at
      its original 4). New branch in `_CATALOG` → **181 lectures / 34 branches**; story DB rebuilt
      (15,513 lines / 246,044 words). Done: selftest (181/34); lint — each lecture
      7x[13,12,13,12,12,13,13], section 1 fact-free, all 7 sections sleep-close, ASCII-only, ambience
      resolves to a real GROUP_NATURE voice, no NAME/module collisions, Quiet Crafts back to 4; offscreen
      both faces — all four dispatch through `stories.story_units` (all 7 sections stream) and a Sleep
      session narrates one, thread-stable.
- [x] **New branch — Lighthouses of the World** (4): The Pharos of Alexandria · Eddystone · The Fresnel
      Lens · Keepers of the Light — added `lectures_{pharos,eddystone,fresnel,keepers}.py`
      (7x[13,12,13,12,12,13,13] lines, fact-free section 1, accurate history/engineering/optics — the
      ancient wonder + its tiers + the "pharos" root, burning-mirror tales framed AS legend; the
      Eddystone rock through Winstanley/Rudyard/Smeaton's interlocking-granite oak-shaped tower/Douglass;
      Fresnel's stepped ring-prism lens gathering one flame into a beam; the keepers' nightly watch +
      the Flannan Isles vanishing framed AS unsolved mystery + automation), ASCII, every section
      sleep-closing; ambiences Ocean Waves / Distant Thunder / Gentle Rain / Whale Song. Distinct NAMEs
      from the existing "The Story of the Lighthouse". New branch in `_CATALOG` → **177 lectures / 33
      branches**; story DB rebuilt (15,161 lines / 240,329 words). Done: selftest (177/33); lint — each
      lecture 7x[13,12,13,12,12,13,13], section 1 fact-free, all 7 sections sleep-close, ASCII-only,
      ambience resolves to a real GROUP_NATURE voice, no NAME/module collisions; offscreen both faces —
      all four dispatch through `stories.story_units` (all 7 sections stream) and a Sleep session
      narrates one, thread-stable.
- [x] **New branch — Tea & Coffee of the World** (4): Green Tea · Coffee · Mate · Masala Chai — added
      `lectures_{greentea,coffeebean,mate,chai}.py` (7x[13,12,13,12,12,13,13] lines, fact-free section
      1, accurate botany/history/ritual — one Camellia plant + steaming/pan-firing + matcha + chanoyu;
      Coffea cherries + the Kaldi goatherd legend framed AS legend + coffee houses + roasting/brewing;
      Ilex paraguariensis + the Guarani + the gourd, bombilla and sharing circle; spiced black tea
      simmered with milk + the chai wallah + Assam/Darjeeling), ASCII, every section sleep-closing, and
      **no health/medical claims** (no caffeine/alertness/benefit claims). Ambiences Wind in Pines /
      Cafe Murmur / Forest Wind / Rain on a Roof. Distinct NAMEs + modules from the existing "The Story
      of Tea" / "The Story of Coffee" (new module `lectures_coffeebean` avoids the `lectures_coffee`
      clash). New branch in `_CATALOG` → **173 lectures / 32 branches**; story DB rebuilt (14,809 lines
      / 234,702 words). Done: selftest (173/32); lint — each lecture 7x[13,12,13,12,12,13,13], section
      1 fact-free, all 7 sections sleep-close, ASCII-only, ambience resolves to a real GROUP_NATURE
      voice, no NAME/module collisions, and a health-claim scan finds nothing unframed (the one
      "wakefulness" token sits inside an explicitly legend-framed line); offscreen both faces — all four
      dispatch through `stories.story_units` (all 7 sections stream) and a Sleep session narrates one,
      thread-stable.
- [x] **New branch — The Night Sky Across Cultures** (4): The Pleiades · Milky Way Myths · The Southern
      Cross · Lunar Calendars — added `lectures_{pleiades,milkywaymyths,southerncross,lunarcalendars}.py`
      (7x[13,12,13,12,12,13,13] lines, fact-free section 1, accurate astronomy + cross-cultural lore
      with each culture's myth framed AS its story — the seven sisters / Subaru / Matariki; the galaxy
      seen edge-on, Galileo, the Silver River + Weaver Girl, the Emu in dark dust; Crux + finding south
      with no south star + Polynesian wayfinding + the Coalsack; the ~29.5-day month, lunar vs lunisolar
      calendars + the Metonic cycle), ASCII, every section sleep-closing; ambiences Wind in Pines /
      Night Crickets / Ocean Waves / Campfire. Distinct NAMEs from the existing "The Milky Way" / "The
      Constellations". New branch in `_CATALOG` → **169 lectures / 31 branches**; story DB rebuilt
      (14,457 lines / 229,433 words). Done: selftest (169/31); lint — each lecture
      7x[13,12,13,12,12,13,13], section 1 fact-free (no names/dates/numbers), all 7 sections
      sleep-close, ASCII-only, ambience resolves to a real GROUP_NATURE voice, no NAME/module
      collisions; offscreen both faces — all four dispatch through `stories.story_units` (all 7
      sections stream) and a Sleep session narrates one, thread-stable.
- [x] **New branch — Famous Gardens** (4): Versailles · Ryoan-ji · Kew Gardens · The Alhambra — added
      `lectures_{versailles,ryoanji,kew,alhambra}.py` (7x[13,12,13,12,12,13,13] lines, fact-free
      section 1, accurate history/design — Le Notre's geometry + the Grand Canal + the Machine de Marly;
      the karesansui dry garden, fifteen stones with one always hidden, meaning left open; Kew's 1759
      founding + the 1844-48 Palm House + the herbarium + the Millennium Seed Bank; the Nasrid
      paradise-garden, the Acequia Real, the Court of the Myrtles + the Court of the Lions + the
      Generalife — symbolism framed as the tradition's intent), ASCII, every section sleep-closing;
      ambiences Mountain Stream / Wind in Pines / Gentle Rain / Mountain Stream. New branch in
      `_CATALOG` → **165 lectures / 30 branches**; story DB rebuilt (14,105 lines / 224,058 words).
      Done: selftest (165/30); lint — each lecture 7x[13,12,13,12,12,13,13], section 1 fact-free (no
      names/dates/numbers), all 7 sections sleep-close, ASCII-only, ambience resolves to a real
      GROUP_NATURE voice, no NAME/module collisions (distinct from the existing "The History of
      Gardens"); offscreen both faces — all four dispatch through `stories.story_units` (all 7 sections
      stream) and a Sleep session narrates one, thread-stable.
- [x] **New branch — Famous Bridges** (4): Golden Gate · Ponte Vecchio · Tower Bridge · Brooklyn
      Bridge — added `lectures_{goldengate,pontevecchio,towerbridge,brooklynbridge}.py` (7x[13,12,13,
      12,12,13,13] lines, fact-free section 1, accurate history/engineering — the strait named in 1846
      + International Orange + the Halfway to Hell net; the Arno arch rebuilt 1345 + Medici goldsmiths
      1593 + the Vasari Corridor; the 1894 bascules + hydraulic accumulators + Horace Jones / John
      Wolfe Barry; the Roeblings + caisson disease + Emily Warren Roebling + the 1883 opening, legends
      framed AS legend), ASCII, every section sleep-closing; ambiences Ocean Waves / Mountain Stream /
      Gentle Rain / Forest Wind. New branch in `_CATALOG` → **161 lectures / 29 branches**; selftest
      passes. Done: selftest (161/29); lint — each lecture 7x[13,12,13,12,12,13,13], section 1
      fact-free (no names/dates/numbers), all 7 sections sleep-close, ASCII-only, ambience resolves to
      a real GROUP_NATURE voice, no NAME/module collisions; offscreen both faces — all four dispatch
      through `stories.story_units` (all 7 sections stream) and a Sleep session narrates one,
      thread-stable.
- [x] **New branch — Musical Instruments** (4): the Piano · the Harp · the Flute · the Drum — added
      `lectures_{piano,harp,flute,drum}.py` (7x12-13 lines, fact-free section 1, accurate
      acoustics/history (Cristofori's pianoforte, 40,000-year bone flutes, Boehm, talking drums),
      ASCII, sleep-closing; Gentle Rain / Wind Chimes / Wind in Pines / Campfire). Distinct from the
      existing "Music and Sound" / "The Story of the Violin". New branch in `_CATALOG` → **157
      lectures / 28 branches**; DB rebuilt (13,401 lines / 212,552 words); selftest passes. Done:
      validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Spices & Herbs** (4): Cinnamon · Saffron · Black Pepper · Vanilla — added
      `lectures_{cinnamon,saffron,pepper,vanilla}.py` (7x12-13 lines, fact-free section 1, accurate
      botany/trade history (Herodotus's bird tale framed as legend; Edmond Albius & hand-pollination;
      narwhal... no — saffron's hand-picked threads), ASCII, sleep-closing; Forest Wind / Wind Chimes
      / Soft Rainstorm / Gentle Rain). Distinct from the existing "The Spice Road". New branch in
      `_CATALOG` → **153 lectures / 27 branches**; DB rebuilt (13,047 lines / 206,664 words); selftest
      passes. Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Legendary Beasts** (4): the Dragon · the Unicorn · the Mermaid · the Griffin —
      added `lectures_{dragon,unicorn,mermaid,griffin}.py` (7x12-13 lines, fact-free section 1,
      folklore framed honestly AS legend with real roots — narwhal tusks -> unicorn horns, manatees ->
      mermaids, Protoceratops fossils -> griffins, dino bones -> dragons — ASCII, sleep-closing;
      Distant Thunder / Forest Wind / Ocean Waves / Wind in Pines). Distinct from the existing
      Phoenix/Selkie lectures. New branch in `_CATALOG` → **149 lectures / 26 branches**; DB rebuilt
      (12,698 lines / 200,782 words); selftest passes. Done: validated 7x12-13 + ASCII + no collisions.
- [x] **New branch — Ancient Roads & Walls** (4): the Great Wall · the Appian Way · Hadrian's Wall ·
      the Inca Roads — added `lectures_{greatwall,appianway,hadrianswall,incaroads}.py` (7x12-13
      lines, fact-free section 1, accurate history (myths corrected — the wall isn't visible from the
      Moon; Inca culture + Vindolanda tablets noted respectfully), ASCII, sleep-closing; Wind in
      Pines / Night Crickets / Forest Wind / Mountain Stream). Distinct from the existing Silk/Spice
      Road lectures. New branch in `_CATALOG` → **145 lectures / 25 branches**; DB rebuilt (12,348
      lines / 194,754 words); selftest passes. Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Volcanoes & Islands** (4): Iceland · the Hawaiian Islands · Krakatoa · the
      Galapagos — added `lectures_{iceland,hawaii,krakatoa,galapagos}.py` (7x12-13 lines, fact-free
      section 1, accurate geology/ecology/history — Krakatoa's 1883 eruption told gently, leaning into
      renewal; Polynesian voyaging + Darwin noted respectfully — ASCII, sleep-closing; Mountain Stream
      / Ocean Waves / Distant Thunder / Night Crickets). Distinct from the existing "Volcanoes and the
      Deep Earth". New branch in `_CATALOG` → **141 lectures / 24 branches**; DB rebuilt (11,999 lines
      / 188,664 words); selftest passes. Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Great Train Journeys** (4): the Trans-Siberian · the Orient Express · the
      Darjeeling Railway · the Ghan — added
      `lectures_{transsiberian,orientexpress,darjeeling,ghan}.py` (7x12-13 lines, fact-free section 1,
      accurate geography/history (rhythm-of-the-rails theme; Afghan cameleers + Aboriginal land noted
      respectfully), ASCII, sleep-closing; Wind in Pines / Gentle Rain / Mountain Stream / Night
      Crickets). Distinct from the existing general "The Railway". New branch in `_CATALOG` → **137
      lectures / 23 branches**; DB rebuilt (11,648 lines / 182,733 words); selftest passes. Done:
      validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Wonders of the Ancient World** (4): the Great Pyramid · the Hanging Gardens ·
      the Colossus of Rhodes · the Temple of Artemis — added
      `lectures_{pyramid,babylon,colossus,artemis}.py` (7x12-13 lines, fact-free section 1, accurate
      history with legends framed honestly (the Hanging Gardens' very existence is uncertain; the
      Colossus did not straddle the harbour), ASCII, sleep-closing; Fan (White Noise) / Mountain
      Stream / Ocean Waves / Wind Chimes). Complements the existing Pharos lighthouse + Library of
      Alexandria lectures. New branch in `_CATALOG` → **133 lectures / 22 branches**; DB rebuilt
      (11,294 lines / 176,512 words); selftest passes. Done: validated 7x12-13 + ASCII + no collisions.
- [x] **New branch — Great Lakes & Inland Seas** (4): Lake Baikal · the Caspian Sea · the Dead Sea ·
      Lake Titicaca — added `lectures_{baikal,caspian,deadsea,titicaca}.py` (7x12-13 lines, fact-free
      section 1, accurate geography/ecology/history (Inca tradition framed respectfully), ASCII,
      sleep-closing; Mountain Stream / Ocean Waves / Brown Noise / Wind Chimes), new branch in
      `_CATALOG` → **129 lectures / 21 branches**; DB rebuilt (10,943 lines / 170,641 words); selftest
      passes. Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Deserts of the World** (4): the Sahara · the Gobi · the Atacama · the Namib —
      added `lectures_{sahara,gobi,atacama,namib}.py` (7x12-13 lines, fact-free section 1, accurate
      geography/ecology/history, ASCII, sleep-closing; Fan (White Noise) / Brown Noise / Wind Chimes
      / Ocean Waves), new branch in `_CATALOG` → **125 lectures / 20 branches**; DB rebuilt (10,591
      lines / 164,750 words); selftest passes. Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Great Forests** (4): the Taiga · the Black Forest · the Daintree · the Cloud
      Forest — added `lectures_{taiga,blackforest,daintree,cloudforest}.py` (7x12-13 lines, fact-free
      section 1, accurate ecology/history/culture (Aboriginal custodianship + Grimm folklore framed
      respectfully), ASCII, sleep-closing; Forest Wind / Gentle Rain / Soft Rainstorm / Mountain
      Stream), new branch in `_CATALOG` → **121 lectures / 19 branches**; DB rebuilt (10,239 lines /
      158,738 words); selftest passes. Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Birds of Myth** (4): the Crane · the Raven · the Swan · the Owl — added
      `lectures_{crane,raven,swan,owl}.py` (7x12-13 lines, fact-free section 1, accurate natural
      history + folklore framed honestly as symbolism, ASCII, sleep-closing; Mountain Stream /
      Forest Wind / Gentle Rain / Night Crickets), new branch in `_CATALOG` → **117 lectures / 18
      branches**; DB rebuilt (9,891 lines / 152,836 words); selftest passes. Done: validated
      7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Great Mountains** (4): Everest · Mount Fuji · Kilimanjaro · the Matterhorn —
      added `lectures_{everest,fuji,kilimanjaro,matterhorn}.py` (7x12-13 lines, fact-free section 1,
      accurate geology/history/culture (sacred names + beliefs framed respectfully), ASCII,
      sleep-closing; Brown Noise / Wind Chimes / Night Crickets / Mountain Stream), new branch in
      `_CATALOG` → **113 lectures / 17 branches**; DB rebuilt (9,540 lines / 146,876 words); selftest
      passes. Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Great Rivers** (4): The Nile · The Amazon · The Ganges · The Yangtze — added
      `lectures_{nile,amazon,ganges,yangtze}.py` (7x12-13 lines, fact-free section 1, accurate
      geography/history/culture with beliefs framed respectfully as tradition, ASCII, sleep-closing;
      Night Crickets / Soft Rainstorm / Singing Bowl / Mountain Stream), new branch in `_CATALOG`
      → **109 lectures / 16 branches**; DB rebuilt (9,195 lines / 140,997 words); selftest passes.
      Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Mythic Places** (4): Atlantis · Shangri-La · El Dorado · Avalon — added
      `lectures_{atlantis,shangrila,eldorado,avalon}.py` (7x12-13 lines, fact-free section 1, each
      legend framed honestly AS a legend + the real history of the belief/search, ASCII, sleep-
      closing; Ocean Waves / Mountain Stream / Forest Wind / Gentle Rain), new branch in `_CATALOG`
      → **105 lectures / 15 branches**; DB rebuilt (8,846 lines / 135,019 words); selftest passes.
      Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Trees of the World** (4): The Oak · Bamboo · The Baobab · Cherry Blossom —
      added `lectures_{oak,bamboo,baobab,cherryblossom}.py` (7x12-13 lines, fact-free section 1,
      accurate botany/history, ASCII, sleep-closing; Forest Wind / Soft Rainstorm / Night Crickets /
      Gentle Rain), new branch in `_CATALOG` → **101 lectures / 14 branches**; DB rebuilt (8,495
      lines / 128,801 words); selftest passes. Done: validated 7x12-13 + ASCII + no NAME collisions.
- [x] **New branch — Gems & Stones** (4): Amber · Pearl · Jade · Diamond — added
      `lectures_{amber,pearl,jade,diamond}.py` (7x12-13 lines, accurate science/history, ASCII,
      sleep-closing; Forest Wind / Ocean Waves / Singing Bowl / Brown Noise), new branch in
      `_CATALOG` → **97 lectures / 13 branches**; DB rebuilt (8,141 lines); selftest passes.
- [x] **New branch — The Elements** (4): Fire · Water · Air · Earth — added
      `lectures_{fire,waterelement,air,earth}.py` (7x12-13 lines, accurate science, ASCII,
      sleep-closing; Campfire / Mountain Stream / Forest Wind / Brown Noise). The "Water" module is
      `lectures_waterelement` to avoid clobbering the existing `lectures_water` ("A River to the
      Sea"). New branch in `_CATALOG` → **93 lectures / 12 branches**; DB rebuilt (7,797 lines);
      selftest passes.
- [x] More **Histories** (4): Honey · The Lighthouse · The Violin · Perfume — added
      `lectures_{honey,lighthouse,violin,perfume}.py` (7×~12 lines, accurate, ASCII,
      sleep-closing), registered in the Histories branch → **61 lectures / 8 branches**;
      DB rebuilt (5,096 lines); selftest passes.
- [x] **The Living World** (3): Moths & Fireflies · The Sloth · Coral Reefs — added
      `lectures_{moths,sloth,coral}.py` (7×12 lines, accurate, ASCII, sleep-closing),
      registered in the Living World branch → **64 lectures / 8 branches**; DB rebuilt
      (5,348 lines); selftest passes.
- [x] **Earth & Sea** (3): Clouds & Weather · Caves & the Underground · The Tides — added
      `lectures_{clouds,caves,tides}.py` (7×12 lines, accurate, ASCII, sleep-closing),
      registered in the Earth & Sea branch → **68 lectures / 8 branches**; DB rebuilt
      (5,688 lines); selftest passes.
- [x] **Ideas & Wonders** (3): Infinity · Symmetry · The Calendar — added
      `lectures_{infinity,symmetry,calendar}.py` (7×12 lines, accurate, ASCII,
      sleep-closing), registered in the Ideas & Wonders branch → **71 lectures /
      8 branches**; DB rebuilt (5,942 lines); selftest passes.
- [x] **The Cosmos** (3): Comets · Nebulae · Saturn's Rings — added
      `lectures_{comets,nebulae,saturnsrings}.py` (7×12-13 lines, accurate, ASCII,
      sleep-closing; ambiences Brown Noise / Singing Bowl / Wind Chimes), registered in
      the Cosmos branch → **74 lectures / 8 branches**; DB rebuilt (6,196 lines); selftest
      passes.
- [x] **The Cosmos** (+3): The Sun · Galaxies · Meteor Showers — added
      `lectures_{sun,galaxies,meteors}.py` (7×12 lines, accurate astronomy, ASCII,
      sleep-closing; Brown Noise / Pink Noise / Wind Chimes), Cosmos branch now 14 →
      **89 lectures / 11 branches**; DB rebuilt (7,459 lines / 111,678 words); selftest passes.
- [x] **New branch — Voyages & Journeys** (4): The Compass · The Caravan · The Railway ·
      The Hot-Air Balloon — added `lectures_{compass,caravan,railway,balloon}.py` (7x12-13
      lines, accurate, ASCII, sleep-closing), new branch in `_CATALOG` → **78 lectures /
      9 branches**; DB rebuilt (6,533 lines); selftest passes.
- [x] **New branch — The Quiet Crafts** (4): Bookbinding · The Blacksmith · Basketry ·
      Stained Glass — added `lectures_{bookbinding,blacksmith,basketry,stainedglass}.py`
      (7x12-13 lines, accurate craft history, ASCII, sleep-closing), new branch in `_CATALOG`
      → **82 lectures / 10 branches**; DB rebuilt (6,871 lines); selftest passes.
- [x] **New branch — Small Wonders** (4): Dew · Dust in Sunlight · Seeds · Snowflakes — added
      `lectures_{dew,dust,seeds,snowflakes}.py` (7x12-13 lines, accurate, ASCII, sleep-closing),
      new branch in `_CATALOG` → **86 lectures / 11 branches**; DB rebuilt (7,207 lines);
      selftest passes.

## Done
- Clock-aware theming: gentle time-of-day warmth/dim + a time-fitting launch mode (View toggle).
- New lecture branch Gems & Stones (Amber · Pearl · Jade · Diamond) → 97 lectures / 13 branches.
- Particle weather overlay: optional snow / leaves / bubbles / fireflies over any scene (View menu).
- Mood check-in: optional 1-tap before/after mood, kind trend in Stats, Sound-menu toggle.
- New lecture branch The Elements (Fire · Water · Air · Earth) → 93 lectures / 12 branches.
- Stats: gentle practice streak + 13-week calendar heatmap of minutes (store per-day log).
- Best voices: British-female default (Kokoro bf_emma); UK-female say fallback; ★-marked best
  voices + friendly accent/gender labels in the narration picker; researched Kokoro vs Fish/XTTS.
- 5 more ambiences (Rain on a Tent · Wind in Pines · Fan · Womb Heartbeat · Whale Song) -> 147.
- Breathing mandala scene: radially-symmetric rings that breathe + counter-rotate (View > Scene).
- Poetry (`poetry.py`): 8 original soothing nocturnes recited slowly as a Sleep "Poetry"
  storyteller option (more poems can be added over future rounds).
- The Cosmos +3 (The Sun · Galaxies · Meteor Showers) → 89 lectures / 11 branches.
- Environmental FX synth (`synth_fx.py`): Train (Steam/Diesel), Ship/Harbour, Thunderstorm,
  Ocean Buoy Bell - completes the instrument suite (31 synthesised voices across 4 modules).
- Winds & Organs synth (`synth_wind.py`): 7 sustained voices - Pipe Organ, Harmonium/Shruti,
  Reed Organ, Wooden Flute + Train Whistle / Fog Horn / Ship Horn; ambience picker + Sound menu.
- Drums synth (`synth_drum.py`): 7 membrane drums (frame/taiko/tabla/djembe/log/woodblock/
  bodhran) struck on a tempo; in the effects picker + Sound menu.
- Bells & Gongs synth (`synth_bell.py`): 12 struck instruments (bells/bowls/gong/triangle/
  tingsha/tubular + a sung bowl) - struck-resonator engine; in the soundscape + Sound menu.
- Aurora scene: slow shimmering northern-lights curtains over a starry sky (View > Scene).
- New lecture branch Small Wonders (Dew · Dust in Sunlight · Seeds · Snowflakes) -> 86 / 11.
- Rain-on-window scene: drops + rivulets on glass over a warm blurred lamp glow (View > Scene).
- Natural-sound breath voices (`voices_breath_nature.py`): Tide & Pebbles, Deep Surf, Spring
  Rain, Pine Wind, Ember Glow, Cosmic Wind, Snowfall Hush - airflow-driven, distinct in/out;
  usable as the inhale voice AND the exhale voice for any combination. 112 voices.
- Sleep Hypnosis (`hypnosis.py`): induction -> deepening countdown -> suggestions -> drift,
  as a Sleep storyteller option.
- Fireplace scene: warm flickering flame + embers + breathing hearth glow (View > Scene).
- Sunrise / Wake mode: gradual dawn simulation (brighten + volume rise + breath quicken +
  dawn chorus), the inverse of the Sleep wind-down; from the Sessions menu.
- New lecture branch The Quiet Crafts (Bookbinding · Blacksmith · Basketry · Stained Glass)
  -> 82 lectures / 10 branches.
- Cosmic music +2 (Aurora Tones · Saturn Ring Shimmer) -> 10 Cosmic Music voices.
- Sound > Cosmic Music menu: all 8 generative music voices one click away.
- Cosmic music data sonification: "The Planets" (real orbital-ratio scale) + real pulsar beat.
- New lecture branch Voyages & Journeys (Compass · Caravan · Railway · Balloon) → 78 / 9.
- Breath-synced cosmic music: pads gently swell/brighten on the inhale, settle on the exhale.
- Cosmic music +4 (Solar Wind · Nebula Bloom · Pulsar Pulse · Gravity Well) + ringdown
  pitch-glide + pulsar beat → 7 Cosmic Music voices.
- Cosmic generative music (`cosmic.py` + `reverb.py`): Music of the Spheres · Starlight
  Choir · Deep Space — endless just-intonation pads + drone + reverb, in the soundscape.
- The Cosmos +3 (Comets · Nebulae · Saturn's Rings) → 74 lectures / 8 branches.
- Cognitive Shuffle sleep-onset aid (`shuffle.py`): random neutral nouns, Sleep "Shuffle".
- NSDR / Yoga Nidra (12 min) guided program: 8-stage body-rotation + breath, rest-close.
- Ideas & Wonders +3 (Infinity · Symmetry · The Calendar) → 71 lectures.
- Sing pitch scoring (% in tune) + in-tune glow + 3 exercises; Meditate guidance card.
- GPU face MSAA (4x multisample FBO + resolve) — smooth head silhouette.
- Earth & Sea +3 (Clouds & Weather · Caves & the Underground · The Tides) → 68 lectures.
- Face naturalism: micro-saccades, settling-sigh + swallow, wind-down damping, head-cock.
- Cat: richer face (markings/breathing/expressions) + Purr ambience + "The Cat" lecture
  + Cat voice group (breath/sigh/meow/purr) + runtime cat/3D toggle.
- Soundscape: richer text→ambience cues + crossfade ducking + follow-story toggle.
- The Living World +3 (Moths & Fireflies · The Sloth · Coral Reefs) → 64 lectures.
- 5 new procedural ambiences (Campfire · Singing Bowl · Wind Chimes · Night Crickets
  · Rain on a Roof) via new `kind="texture"` generators; calibrated.
- Enriched all 4 ambient scenes (motes/rings/coherence · clouds/shooting star ·
  moonlit sea · tone-reactive ripple) via shared `scene_fx.py`.
- Histories +4 (Honey · Lighthouse · Violin · Perfume) → 61 lectures / 8 branches.
- Hourglass session timer (corner, flip-to-reset) + eyelash lid-edge fix (interactive).
- Myth & Legend branch (4) · The Senses (3) → 57 lectures / 8 branches.
- Self-contained project (vendored core) + SQLite stories DB + Story Library.
- Per-window themed backdrops + Underwater/Embers backgrounds.
