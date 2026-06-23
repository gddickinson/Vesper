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
- [ ] **Sing — pitch trainer**: scoring (% time in tune), an in-tune glow, more
      exercises; **Meditate** — open-monitoring vs focused-attention guidance.

### Researched batch — restful practices (efficacy)
- [ ] **NSDR / Yoga Nidra** guided session: a slow body-rotation + breath script with
      long pauses (a `programs.Program` + narration), ~12 min, closing toward rest.
- [ ] **Cognitive Shuffle** sleep-onset aid: a `stories` generator that speaks random,
      neutral, concrete words with long breath-paced gaps; a Sleep "Shuffle" option.
- [ ] **Body-scan + PMR** guided program: slow timed tense→release cues head-to-toe,
      paced to the breath.
- [ ] **Physiological-sigh reset**: a 2–3 min "Sigh" mini-session (double inhale, long
      exhale) + a matching visual, for a quick down-regulation.

### Researched batch — light & circadian
- [ ] **Sunrise / Wake mode**: a gradual dawn-simulation (warm→bright over N min) with a
      soft rising chime + optional dawn chorus — a gentle wake-up (inverse of wind-down).
- [ ] **Clock-aware theming**: bias palette/brightness by local time (warm+dim at night,
      brighter by day) and suggest a fitting mode on launch.

### Researched batch — new visual scenes
- [ ] **Fireplace scene** (flickering flame + embers; pairs with Campfire) for Relax/Sleep.
- [ ] **Rain-on-window scene**: droplets sliding down glass over a soft blurred glow.
- [ ] **Aurora scene**: slow northern-lights ribbons for Sleep/Relax.
- [ ] **Breathing mandala**: a symmetric sacred-geometry pattern that unfolds/rotates
      with the breath (Meditate/Chant).
- [ ] **Particle weather**: an optional gentle snow / drifting leaves / rising bubbles
      layer per scene (a toggle).

### Researched batch — audio & synthesis
- [ ] **Generative ambient pad**: an evolving, non-repeating drone in a selectable
      scale/key (a `kind="generative"` track) for Relax/Sleep.
- [ ] **More ambiences**: Whale Song · Distant Train · Rain on a Tent · Wind in Pines ·
      Womb Heartbeat · Fan (white-noise machine). Calibrated.
- [ ] **Slow-wave pink pulses**: pink noise gently pulsing at ~0.8 Hz (open-loop,
      honestly framed) for deep-sleep support.
- [ ] **Gong bath / tuned bowl set**: a slow sequence of struck bowls/gongs.
- [ ] **Spatial polish**: subtle auto-pan / width on ambiences for headphone immersion.

### Researched batch — engagement & structure
- [ ] **Streaks + calendar heatmap** in Stats (gentle, non-judgemental) + weekly minutes.
- [ ] **Mood check-in**: a 1-tap before/after mood, tracked over time.
- [ ] **Multi-night courses**: sequenced programs — "7 Nights to Sleep", "21 Days of Calm".
- [ ] **Launch suggestion**: recommend a mode/lecture by time of day + recent history.
- [ ] **First-run onboarding**: a gentle goal pick (sleep / focus / calm) that presets it.

### Researched batch — storyteller
- [ ] **Optional spoken name**: greet/settle the listener by name (off by default).
- [ ] **Narration language**: expose Kokoro's languages/voices where available.

## Stories (ongoing — every ~3rd round)
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
- [ ] **Ideas & Wonders** (3): Infinity · Symmetry · The Calendar.
- [ ] **The Cosmos** (3): Comets · Nebulae · Saturn's Rings.
- [ ] **New branch — Voyages & Journeys** (4): The Compass · The Caravan · The Railway ·
      The Hot-Air Balloon.
- [ ] **New branch — The Quiet Crafts** (4): Bookbinding · The Blacksmith · Basketry ·
      Stained Glass.
- [ ] **New branch — Small Wonders** (4): Dew · Dust in Sunlight · Seeds · Snowflakes.

## Done
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
