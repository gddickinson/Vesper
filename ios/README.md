# Vesper for iOS (native Swift)

A native **SwiftUI + AVAudioEngine** build of Vesper for iPhone and iPad — the
companion to the desktop (PySide6) app. It is a fresh native implementation, not
a wrapper: the breath timing, procedural breath audio, and the breathing orb are
re-built in Swift so the app runs fully on-device, offline, and — crucially for a
sleep app — **keeps playing with the screen locked** (the `audio` background mode).

## What works in this first slice

- **Four modes** (Meditate · Breathwork · Relax · Sleep) — the mode bar is the
  primary navigation, as on desktop. Each one-tap configures pattern + breath voice.
- **Breath pacing**: 16 patterns (Coherent 5.5, Box, 4-7-8, Physiological Sigh, …)
  with the exact desktop envelope math (raised-cosine `volume`, sine-bump `airflow`).
- **Procedural breath sound**: a real-time `AVAudioSourceNode` renders filtered
  noise (white/pink/brown → swept band-pass → brightness low-pass) shaped by the
  breath airflow — loud mid-breath, silent during holds. Five breath voices.
- **Breathing orb**: a SwiftUI `Canvas` scene with layered glow, a guide ring, a
  travelling cycle dot, a session-progress arc, and a phase-tinted hue.
- **Spoken sleep-lectures**: `AVSpeechSynthesizer` narrates a starter set of four
  lectures slowly, with on-screen captions, picking a natural (premium/enhanced)
  voice — and it continues with the screen off.
- **Background audio**: `.playback` audio session + `UIBackgroundModes = audio`.
- **Persistence**: last mode / pattern / voice / volumes via `UserDefaults`.

## Architecture (mirrors the desktop core)

```
VesperApp ─ RootView ─ SessionViewModel ─┬─ BreathClock   (the single timing authority)
                                         ├─ AudioEngine   (AVAudioSourceNode → BreathSynth → DSP)
                                         └─ Narrator      (AVSpeechSynthesizer)
        OrbView (Canvas)  reads the same BreathClock state each frame.
```

| File | Role |
|---|---|
| `Core/BreathPattern.swift` | pattern model + `BreathMath.state(at:)` envelope (port of `patterns.py`) |
| `Core/Patterns.swift` | the preset library |
| `Core/BreathClock.swift` | pausable monotonic clock; read lock-free from the audio thread |
| `Audio/DSP.swift` | white/pink/brown noise, RBJ biquad, one-pole, soft-clip (port of `dsp.py`) |
| `Audio/BreathVoice.swift` / `BreathSynth.swift` | breath-voice params + the real-time renderer |
| `Audio/AudioEngine.swift` | `AVAudioEngine` host, session, background audio |
| `Audio/Narrator.swift` | spoken narration + captions |
| `Content/Lectures.swift` | starter sleep-lectures (the full 337 ship later as JSON) |
| `Scenes/OrbView.swift` | the breathing orb (`Canvas`) |
| `UI/Theme.swift` / `RootView.swift` / `SessionViewModel.swift` | palette, screen, state hub |

Every file is kept under 500 lines; one concept per file.

## Build & run

Open `Vesper.xcodeproj` in **Xcode** (26.x), pick an iPhone/iPad simulator or a
device, and press **Run**. Bundle id `com.vesper.ios`; deployment target iOS 17;
no third-party dependencies.

### Verification status

The whole app **type-checks cleanly against the iOS 26.5 SDK** (`swiftc -typecheck`,
0 errors, 2 benign `Sendable` warnings). The command-line `xcodebuild` on this
machine currently can't produce the `.app` because the shared Xcode components are
stale (it fails to load `IDESimulatorFoundation`). Fix it once with:

```
sudo xcodebuild -runFirstLaunch        # installs/repairs the shared components
# then, to run headless in a simulator:
xcodebuild -project Vesper.xcodeproj -scheme Vesper \
  -destination 'platform=iOS Simulator,name=iPhone 16' build
```

Building from the **Xcode GUI** does not hit that CLI-plugin issue.

## Roadmap toward parity

- Bundle the full lecture library + books (JSON) and a book reader.
- The 36 cartoon characters (port the `char_*` `QPainter` drawings to SwiftUI `Canvas`).
- Nature ambience beds, chant/sing modes, the pitch trainer, Stats/streaks.
- A neural on-device TTS option; a Now-Playing lock-screen control.
