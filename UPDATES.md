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
- [ ] **Optional high-fidelity neural engine**: behind the same optional-dependency pattern as
      `kokoro_tts` (degrade gracefully), allow an opt-in heavier engine (XTTS-v2 / Fish Speech) for
      users with a GPU - voice cloning + emotion. NOT bundled (size/GPU); a documented add-on.
- [ ] **Optional spoken name**: greet/settle the listener by name (off by default).
- [ ] **Narration language**: expose Kokoro's languages/voices where available.

## Stories (ongoing — every ~3rd round)
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
