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
- [ ] **Face naturalism**: micro-saccades, a rare settling-sigh, occasional swallow,
      flatter affect as the session winds down, a slight head-tilt on curious lines.
- [ ] **GPU face**: antialias the silhouette (MSAA) so the head edge is smooth over
      the backgrounds.
- [ ] **Sing — pitch trainer**: scoring (% time in tune), an in-tune glow, more
      exercises; **Meditate** — open-monitoring vs focused-attention guidance.

## Stories (ongoing — every ~3rd round)
- [x] More **Histories** (4): Honey · The Lighthouse · The Violin · Perfume — added
      `lectures_{honey,lighthouse,violin,perfume}.py` (7×~12 lines, accurate, ASCII,
      sleep-closing), registered in the Histories branch → **61 lectures / 8 branches**;
      DB rebuilt (5,096 lines); selftest passes.
- [x] **The Living World** (3): Moths & Fireflies · The Sloth · Coral Reefs — added
      `lectures_{moths,sloth,coral}.py` (7×12 lines, accurate, ASCII, sleep-closing),
      registered in the Living World branch → **64 lectures / 8 branches**; DB rebuilt
      (5,348 lines); selftest passes.
- [ ] **Earth & Sea** (3): Clouds & Weather · Caves & the Underground · The Tides.
- [ ] **Ideas & Wonders** (3): Infinity · Symmetry · The Calendar.

## Done
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
