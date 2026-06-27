# Turn on Kokoro neural narration with sherpa-onnx

This switches Vesper's narration from the system voices to **Kokoro** — the same
high-quality, fully-offline neural voices the desktop app uses. ~30 minutes of
Xcode work, no code beyond dropping in one file.

## What the app already does for you

Everything *around* the model is built and shipping:
- the **voice catalog** (`KokoroCatalog`),
- **path resolution** that finds a bundled `kokoro` model folder (or a downloaded one),
- the **playback engine** (`NeuralNarrator` — streams PCM with breath-length gaps),
- **picker + routing**: when a Kokoro model is present the voices appear in the
  Sleep ▸ **Voice** list, and narration/preview route through the neural engine
  the moment a backend is registered.

So you only need to: **(1)** add the sherpa-onnx engine + a Kokoro model, and
**(2)** drop in one `KokoroOnnxBackend.swift` that registers itself.

## Step 1 — Get the sherpa-onnx iOS frameworks

Repo: <https://github.com/k2-fsa/sherpa-onnx> · releases:
<https://github.com/k2-fsa/sherpa-onnx/releases>

- **Easiest — prebuilt:** grab the iOS asset (e.g. `sherpa-onnx-<ver>-ios.tar.bz2`,
  or the `*.xcframework` assets). It contains `sherpa-onnx.xcframework` **and**
  `onnxruntime.xcframework`.
- **Or build it:** `git clone … && ./build-ios.sh` → `build-ios/*.xcframework`.

## Step 2 — Get a Kokoro model bundle

From sherpa-onnx's released TTS models, download a Kokoro one (English
`kokoro-en-v0_19`, or multilingual `kokoro-multi-lang-v1_0`):

```bash
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-en-v0_19.tar.bz2
tar xf kokoro-en-v0_19.tar.bz2          # → folder with model.onnx, voices.bin, tokens.txt, espeak-ng-data/
mv kokoro-en-v0_19 kokoro               # the app looks for a folder named exactly "kokoro"
```

## Step 3 — Add everything to the Xcode project

1. **Frameworks** — drag `sherpa-onnx.xcframework` + `onnxruntime.xcframework` into
   the project (Copy items if needed; add to the Vesper target). Target ▸ General ▸
   *Frameworks, Libraries, and Embedded Content* → set both to **Embed & Sign**.
2. **Swift helper** — copy sherpa-onnx's `swift-api-examples/SherpaOnnx.swift`
   into `Vesper/Audio/Neural/` (it wraps the C API in Swift — `SherpaOnnxOfflineTtsWrapper`, the `sherpaOnnxOffline*Config(...)` builders, etc.).
3. **Bridging header** — create `Vesper/Vesper-Bridging-Header.h`:
   ```objc
   #import "c-api.h"   // sherpa-onnx C API (from the xcframework headers)
   ```
   Build Settings ▸ *Objective-C Bridging Header* = `Vesper/Vesper-Bridging-Header.h`
   (mirror sherpa-onnx's own iOS example's bridging header).
4. **Model bundle** — drag the **`kokoro`** folder in and choose **"Create folder
   references"** (a *blue* folder, not a yellow group), added to the Vesper target.
   This bundles `model.onnx`, `voices.bin`, `tokens.txt`, `espeak-ng-data/`.
   `KokoroModel.bundledDir` finds it automatically. (Adds ~80–330 MB — prefer the
   int8/quantized model to keep it small.)

## Step 4 — Drop in the backend

Copy [`KokoroOnnxBackend.swift.template`](KokoroOnnxBackend.swift.template) into
`Vesper/Audio/Neural/KokoroOnnxBackend.swift`. It implements `NeuralTTSBackend`
against `SherpaOnnxOfflineTtsWrapper`, reading the resolved Kokoro paths.

## Step 5 — Register it at launch

In `VesperApp.swift`:

```swift
@main
struct VesperApp: App {
    init() { NeuralTTS.backend = KokoroOnnxBackend() }   // nil-safe if files absent
    var body: some Scene { WindowGroup { RootView() } }
}
```

## Step 6 — Build & run

Build to your device. In **Sleep ▸ Voice** the Kokoro voices now appear
("Heart · US ♀ · Neural", "George · UK ♂ · Neural", …). Pick one and tap
**Preview** — desktop-grade, fully-offline narration.

## Troubleshooting

- **Compile errors in the backend** — the `sherpaOnnxOffline*` helper signatures
  come from the `SherpaOnnx.swift` you copied; match the backend to that file's
  current field names (the API evolves between sherpa-onnx versions).
- **No neural voices in the picker** — the folder reference must be named exactly
  `kokoro`, be a *blue* folder, be in the target, and contain `model.onnx`.
- **Crash on first synth** — check the bridging header path, that both
  xcframeworks are Embed & Sign, and that `espeak-ng-data/` is bundled.
- **App too large / want on-demand** — instead of bundling, extend
  `KokoroDownloader` to download + unpack the model `.tar.bz2` at runtime (needs a
  bzip2/tar lib such as libarchive); the rest already supports the downloaded path.
- **Speaker mapping** — `KokoroCatalog.all` order should match the speaker indices
  in `voices.bin`; reorder the catalog if a voice sounds wrong.
