# Vesper iOS — session log

## R1 — native Swift iOS app: foundation + core vertical slice
User asked to "build a native swift iOS app version". Stood up a fresh **SwiftUI +
AVAudioEngine** app under `ios/Vesper/` (not a wrapper) that re-implements Vesper's
heart natively so it runs on-device, offline, and keeps audio playing with the
screen locked (the reason a sleep app must be native).

Shipped this slice:
- **Core timing** ported faithfully from `breathsim/patterns.py` +
  `controller.py`: `BreathPattern` + `BreathMath.state(at:)` (raised-cosine
  `volume`, sine-bump `airflow`, holds silent) and `BreathClock`, a pausable
  monotonic clock (CACurrentMediaTime) that is the **single timing authority** —
  read lock-free from the real-time audio thread, so sound and visuals stay in
  lock-step. 16 patterns.
- **Procedural breath audio**: `DSP.swift` (white/pink/brown noise, RBJ biquad,
  one-pole, soft-clip — port of `dsp.py`), `BreathVoice` (5 voices) + `BreathSynth`
  (stateful noise → swept band-pass → brightness LP, airflow-shaped, ramped per
  block, click-free), driven by an `AVAudioSourceNode` in `AudioEngine.swift` with
  a `.playback` session + `UIBackgroundModes = audio`.
- **Narration**: `Narrator.swift` (AVSpeechSynthesizer, premium/enhanced voice,
  captions, background-capable) reading a starter set of 4 sleep-lectures.
- **Visuals**: `OrbView` (SwiftUI Canvas — layered glow, guide ring, cycle dot,
  progress arc, phase-tinted hue), `Theme` (night palette), `RootView` (mode bar
  + orb + controls + transport), `SessionViewModel` (state hub, 60fps tick,
  UserDefaults persistence), `VesperApp` (@main).
- **Project**: hand-authored `Vesper.xcodeproj` using a `PBXFileSystemSynchronized
  RootGroup` (objectVersion 77) so all sources auto-include; shared scheme; asset
  catalog (accent + app-icon placeholder); bundle id `com.vesper.ios`, iOS 17,
  iPhone+iPad, Swift 5 language mode.

Every file < 500 lines, one concept per file.

**Verification.** The whole app **type-checks against the iOS 26.5 SDK with 0
errors** (`xcrun --sdk iphoneos swiftc -typecheck -target arm64-apple-ios17.0` over
all sources; 2 benign Sendable warnings on AVSpeechSynthesizer/AVAudioEngine, which
are warnings-only in Swift 5 mode). Fixed along the way: `AudioBuffer.mDataByteLength`
→ compute bytes from `frameCount`; `AVSpeechSynthesisVoice.Quality` →
`AVSpeechSynthesisVoiceQuality`; `Patterns.default` (not `BreathPattern.default`).

**Toolchain note.** `xcodebuild` on this machine can't yet emit the `.app`: it
fails to load `IDESimulatorFoundation` because the shared `/Library/Developer`
components are stale vs Xcode 26.6 (`Symbol not found … DVTDownloads`). One-time fix:
`sudo xcodebuild -runFirstLaunch` (needs admin); the Xcode GUI build is unaffected.
No simulator runtime is installed, so a headless run also needs a runtime download.

Next: bundle the full lecture/book library as JSON; port the 36 cartoon characters
from `QPainter` to SwiftUI `Canvas`; nature ambiences; Stats/streaks; Now-Playing.

## R2 — content + ambiences + characters + ship-polish (all four user picks)
User chose to do all of: bundle full content, port characters, nature ambiences,
ship-polish. Shipped in four committed phases, each verified by a real
`xcodebuild` build (the user repaired the toolchain with `sudo xcodebuild
-runFirstLaunch`, so device-class builds run; **note** `swiftc -typecheck` misses
definite-initialization — only the full build caught a real DI error in
`SessionViewModel.init`, since fixed):

- **Content**: `ios/tools/export_content.py` dumps the desktop lectures to
  `Content/lectures.json` (337 across 73 branches, 2.4 MB); `LectureStore` loads
  it from the bundle (built-in fallback if absent); Sleep gets a branch→lecture
  grouped picker + a "Surprise me".
- **Ambiences**: `AmbienceSynth` — one parametric engine (noise colour → optional
  swept filter → swell LFO + sparse crackle) → 8 beds (rain/ocean/wind/fire/
  stream/crickets/pink/brown), mixed as a continuous second layer in the source
  node with a final soft-clip; per-mode defaults; Nature-sound picker + level.
- **Characters**: `CharacterKit` (aura/head/eyes/blush/nose/mouth/whiskers/ears) +
  12 `CharacterDrawer`s (Cat…Lion) on a SwiftUI Canvas; `CharacterView`; Sleep
  shows one as a breathing **companion** that lip-syncs the narration. QA'd by
  on-simulator screenshots (Cat/Owl/Fox/Lion all recognizable).
- **Polish**: a procedural **app icon** (`ios/tools/make_icon.py`), lock-screen
  **Now Playing** (`MPNowPlayingInfoCenter` + remote play/pause), and a
  **PracticeLog**/`StatsView` (sits · minutes · day streak). Also cleared the
  `AVSpeechSynthesizer` Sendable warning with `nonisolated(unsafe)`.

Every file < 500 lines. Final state: `** BUILD SUCCEEDED **`, 0 errors / 0 warnings.

## R3 — complete the character cast to all 36
The remaining 24 characters (Chicken, Duckling, Sheep, Pig, Cow, Tiger, Elephant,
Giraffe, Rhino, Monkey, Deer, Hedgehog, Rat, Koala, Red Panda, Snowman, Luna,
Robot, Bot, Alien, Martian, Woman, Man, Skull) drafted by six parallel subagents
(each read `CharacterKit` + a template, wrote one `Characters<group>.swift`), then
integrated into `Characters.all` in the desktop order (now **36**), built, and
QA'd via an on-simulator 24-cell contact sheet (all recognizable: red-comb
chicken, wool-ring sheep, striped tiger, trunk+ears elephant, antlered deer, spiky
hedgehog, spoon-nose koala, red-cap snowman, sleepy moon, masked red panda,
glowing-eye robot, almond-eyed alien, cyclops martian, socket-and-teeth skull…).
`** BUILD SUCCEEDED **`, 0 errors / 0 warnings.
