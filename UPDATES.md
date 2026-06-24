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
- [ ] **Body-scan + PMR** guided program: slow timed tense→release cues head-to-toe,
      paced to the breath.
- [ ] **Physiological-sigh reset**: a 2–3 min "Sigh" mini-session (double inhale, long
      exhale) + a matching visual, for a quick down-regulation.

### Researched batch — light & circadian
- [x] **Sunrise / Wake mode**: `director.start_wake` + `app.start_sunrise` + a Sessions menu
      "Sunrise (gentle wake-up)" - over N min the view brightens (warm dim->clear, inverse of
      the Sleep wash), the volume rises (quiet->full), the breath quickens (Extended 7-11 ->
      Coherent 5.5) and a Forest Wind dawn bed + soft chime fade in. Verified early-dim vs
      late-bright renders (warm 0.40->0.03, cycle 18s->11s), thread-stable, both faces.
- [ ] **Clock-aware theming**: bias palette/brightness by local time (warm+dim at night,
      brighter by day) and suggest a fitting mode on launch.

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
- [ ] **Breathing mandala**: a symmetric sacred-geometry pattern that unfolds/rotates
      with the breath (Meditate/Chant).
- [ ] **Particle weather**: an optional gentle snow / drifting leaves / rising bubbles
      layer per scene (a toggle).

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
- [ ] **Add reverb as a shared send**: offer the new `Reverb` as an optional space on other
      ambiences (bowls, chimes) and the drone.
- [ ] **More ambiences**: Whale Song · Distant Train · Rain on a Tent · Wind in Pines ·
      Womb Heartbeat · Fan (white-noise machine). Calibrated.
- [ ] **Slow-wave pink pulses**: pink noise gently pulsing at ~0.8 Hz (open-loop,
      honestly framed) for deep-sleep support.
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
