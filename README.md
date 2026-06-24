<h1 align="center">Vesper</h1>

<p align="center"><b>A breath-paced meditation &amp; sleep companion.</b><br>
A glowing avatar breathes with you, lip-syncs a procedural bedtime storyteller, and is
wrapped in fully procedural breath, voice, chant and nature sound — no audio assets
required.</p>

<p align="center">
  <img src="docs/images/window_sleep.png" width="820" alt="Vesper in Sleep mode — the avatar, a bedtime story, and the hourglass timer">
</p>

Vesper paces your breath with a soft animated visualization and real-time synthesised
sound. It spans six activities — **Meditate · Breathwork · Chant · Sing · Relax · Sleep** —
each with its own purpose-built control panel, visual scene and soundscape. At its centre
is a talking-head **avatar** (a 3D head, or one of **15 hand-drawn cartoon characters**)
that breathes, blinks, gazes around, emotes, and narrates a library of **185 soothing
sleep-lectures** that gently follow the words on screen.

It's a **self-contained** project: the entire audio / breath / voice / story engine is
vendored at [`breathsim/`](breathsim/) (no sibling dependency); the PySide6 front-end
lives in [`vesper/`](vesper/). Everything **degrades gracefully** — no GPU, no audio
device, no neural voices, no 3D head — there's always a calm fallback.

---

## Highlights

- **A living avatar** — the faceView ICT head rendered on the GPU (moderngl), with a soft
  software fallback. It nods with the breath, blinks, wanders its gaze, lip-syncs the
  narrator and shifts expression with the mood of the words. A **cyberpunk face-style**
  system (starry eyes, Tron/circuit grids that follow the head, translucent / dot-matrix
  renders) can react to the story, breath and chant. Or switch to the **2D cast**.
- **15 cartoon characters + costumes** — Cat, Penguin, Dog, Owl, Fox, Chicken, Bunny,
  Bear, Panda, Frog, Duckling, Hedgehog, **Robot**, Woman and Man, each with breathing,
  blinks, tail-swishes and "hair-on-end" startles, **12 costumes**, and its own narrator
  **voice + personality**. The bedtime storyteller can even pick a fitting character per
  scene (a cosy bear for a hibernation tale, a wise owl for the night sky).
- **Fully procedural sound** — **148 voices** synthesised in real time from noise, filters
  and a vocal-tract (formant) model: realistic breath timbres, human voice, vocal
  exercises, pranayama, singing, a playful **Cat** voice family, and nature **ambiences**
  (ocean, rain, forest, a crackling campfire, a struck singing bowl, wind chimes, night
  crickets…) plus synthesised **bells & gongs, drums, winds & organs, environmental FX**
  and a **cosmic generative-music** engine sonifying real planetary + pulsar data. Nothing
  to download.
- **The bedtime storyteller** — **185 authored sleep-lectures across 35 branches** (the
  Cosmos, Earth &amp; Sea, the Living World, the Human Body, Histories, Materials &amp;
  Making, Ideas &amp; Wonders, Myth &amp; Legend, and many more), plus procedural bedtime
  stories, poetry nocturnes and a cognitive-shuffle sleep aid. Spoken by neural **Kokoro**
  TTS (or macOS `say`), slowing and quietening as you drift off — and the **soundscape,
  the backdrop and the character all gently follow the words**.
- **Realistic chanting** — **66 mantras, chants &amp; songs** (Om Mani Padme Hum, Aum,
  Om Tare Tuttare, Nam Myoho Renge Kyo, Gregorian plainchant, vocalises, affirmations)
  sung as articulated syllables with real consonants, over a tonic drone with a reciting
  tone and an on-screen sing-along.
- **A sense of space** — an optional master **reverb** (room → hall → cathedral) that
  makes chant and song sound like they're in a real room.
- **Evidence-based calm** — resonance breathing near **~6 breaths/min**, longer exhales,
  **4-7-8 / box / physiological-sigh** patterns; guided **Body-Scan &amp; PMR**, **NSDR /
  Yoga Nidra**, a one-tap **Physiological-Sigh reset**; a warm, low-blue **Sleep
  wind-down** that dims the screen on a melatonin-friendly curve; pink / brown noise.
- **Per-mode visual scenes** — a breathing **orb** (motes, exhale rings, a coherence halo
  near 6 bpm), a starry **night**, a moonlit **sea**, tone-reactive **ripples**, an
  on-screen **pitch trainer**, and themed animated **backdrops** (stars, embers, rain,
  forest, a quiet city…) that crossfade to match the story.
- **Real tools** — pitch trainer, mindfulness bell, breath-hold (retention) timer, mala /
  japa counter, an **hourglass session timer** you flip to reset, a full **Voice Editor**
  (live wave + spectrum), **Pattern Editor**, **Presets Manager**, a layer **Mixer**,
  **11 guided programs**, multi-night **courses**, practice **Stats** (streaks, calendar,
  insights), and offline **WAV export**.

## Modes

| Mode | What it's for | Scene |
|------|---------------|-------|
| **Meditate** | Paced / resonance breathing + a mindfulness bell | Orb |
| **Breathwork** | Pranayama techniques, guided rounds, retention timer | Orb |
| **Chant** | Mantras, a reciting tone over a tonic drone, japa counter | Ripple |
| **Sing** | Warm-ups + an on-screen pitch trainer (target vs. your voice) | Pitch trainer |
| **Relax** | A multi-layer nature soundscape mixer | Wave |
| **Sleep** | The bedtime storyteller + wind-down + screen dimming | Night |

The **mode bar** is the primary navigation; a resizable side panel rebuilds into each
mode's purpose-built tools, and a tidy menu bar (File · Modes · Sessions · Pattern · Voice ·
Sound · Face · View · Help) is the global escape hatch for everything else.

## Gallery

<p align="center">
  <img src="docs/images/window_meditate.png" width="820" alt="Meditate mode — the breathing orb with a coherence halo, pace and pattern controls">
</p>

<table>
  <tr>
    <td align="center"><img src="docs/images/scene_orb.png" width="380" alt="Orb scene"><br><sub><b>Orb</b> — Meditate / Breathwork</sub></td>
    <td align="center"><img src="docs/images/scene_night.png" width="380" alt="Night scene"><br><sub><b>Night</b> — Sleep</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/images/scene_wave.png" width="380" alt="Wave scene"><br><sub><b>Wave</b> — Relax</sub></td>
    <td align="center"><img src="docs/images/scene_ripple.png" width="380" alt="Ripple scene"><br><sub><b>Ripple</b> — Chant / Sing</sub></td>
  </tr>
</table>

## Run

```bash
pip install -r requirements.txt      # + see the faceView note below
python run.py                        # launch the app
python selftest.py                   # headless checks (no display/audio needed)
```

`VESPER_FACE=cat python run.py` starts on the 2D character face (also under **Face ▸
Cartoon character face**).

## Dependencies

Pure pip packages (see [`requirements.txt`](requirements.txt)): **PySide6**, **numpy**,
**moderngl**, **sounddevice**, **soundfile**, **scipy**.

Optional extras (each degrades gracefully if absent):

- **faceView** — the 3D head renderer, installed editable from its own project (~1.2 GB,
  so *not* vendored). Without it, the face falls back to the hand-drawn **2D character**
  cast that breathes, blinks and lip-syncs the story.
- **kokoro-onnx** — neural narration voices (`pip install kokoro-onnx` +
  `python -m breathsim.kokoro_tts --download`). Without it, narration uses macOS `say`.
- **XTTS-v2** — *highest-fidelity* offline voices (voice-clone + 58 studio speakers,
  faster-than-real-time on Apple Silicon). Opt-in and **not bundled** (it's large and
  under the non-commercial Coqui CPML): install it yourself with
  `python tools/setup_xtts.py --accept-license`, then pick an "XTTS" narration voice in
  Sleep. The 15 characters speak in XTTS too when it's installed. See
  [`docs/XTTS.md`](docs/XTTS.md).

> Graceful degradation: no GPU → software face; no faceView → the cartoon cast; no audio
> device → visual only; no Kokoro → `say`; no XTTS → Kokoro / `say`.

<p align="center">
  <img src="docs/images/cat.png" width="300" alt="The cartoon-cat fallback face, mid-sentence">
  <br><sub>The cartoon cast — for when faceView isn't installed (or just for fun).</sub>
</p>

## Project layout

- [`vesper/`](vesper/) — the Qt app: window, resizable workspace-driven control panel, the
  3D face + 2D character cast, the visual scenes, the menu bar, dialogs (Voice / Pattern /
  Preset editors, Mixer, Stats, Story Library). See [`INTERFACE.md`](INTERFACE.md) for the
  full module map.
- [`breathsim/`](breathsim/) — the **vendored core**: audio engine, breath controller,
  voices, patterns, modes, narration (Kokoro / `say` / XTTS), reverb, `phrases.py` +
  `vocal.py` (chant synthesis), `stories.py` + the whole **lecture library**
  (`lectures*.py`), `sound_cues.py` (text-matched ambience), `textures.py` /
  `cosmic.py` (procedural sound) and `story_db.py`.
- [`tools/`](tools/) — the opt-in `setup_xtts.py` installer, the voice loudness audit.
- `data/stories.db` — a SQLite record of every story (rebuilt on startup, or
  `python -m breathsim.story_db`). Browse it in-app via **Help ▸ Story Library**.

## How it works

A single `BreathController` is the clock. ~40 times a second the GUI reads the current
breath state and drives either the **face** (head nod + breathing zoom; narration
amplitude → jaw) or the active **scene**, while the audio engine renders click-free stereo
blocks on a separate thread — layering a morphable breath voice, an ambience bed, optional
effects, a chant/song voice and chimes, through an optional reverb space — all paced by the
same breath. The control panel mirrors live state every frame, so the menus, a guided
program and a character swap all stay in sync. Add a voice, a breath pattern, a persona, an
ambience, a guided program, a chant or a sleep-lecture by dropping in one small file; no
engine changes needed.

## License

See [`LICENSE`](LICENSE). The avatar is rendered from the
[ICT-FaceKit](https://github.com/ICT-VGL/ICT-FaceKit). Optional XTTS-v2 voices are under
the non-commercial Coqui Public Model License and are never bundled.
