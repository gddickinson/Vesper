# Turn on Kokoro neural narration — step by step

This switches Vesper's narration to **Kokoro** neural voices (desktop-grade,
fully offline). **The downloads and staging are already done for you** — the
files live in `ios/vendor/` on this Mac. You only do Xcode clicks. ~15 minutes.

> Already verified against **sherpa-onnx v1.13.3** + the **kokoro-int8-multi-lang
> v1.1** model. The app's `KokoroModel`/`NeuralNarrator`/picker/routing are
> wired; the backend file + config are written to match this exact version.

## What's already staged (don't re-download)

| Path on this Mac | What it is |
|---|---|
| `ios/vendor/Frameworks/sherpa-onnx.xcframework` | the engine (static lib) |
| `ios/vendor/Frameworks/onnxruntime.xcframework` | onnxruntime 1.26 |
| `ios/vendor/SherpaOnnx.swift` | the Swift wrapper for the C API |
| `ios/vendor/kokoro/` | the model (model.onnx, voices.bin, tokens.txt, espeak-ng-data/, English lexicons) — 190 MB |
| `ios/docs/Vesper-Bridging-Header.h` | the bridging header to copy in |
| `ios/docs/KokoroOnnxBackend.swift.template` | the backend to copy in |

## Steps (all in Xcode)

Open `ios/Vesper/Vesper.xcodeproj`. In the left panel select the **Vesper** group
(yellow folder) so new files land in the target. Then:

1. **Add the two frameworks.** In Finder open `ios/vendor/Frameworks`. Drag both
   `sherpa-onnx.xcframework` and `onnxruntime.xcframework` into the Xcode project
   navigator → in the sheet, tick **"Copy items if needed"** and the **Vesper**
   target. Then select the project ▸ **Vesper** target ▸ **General** ▸ *Frameworks,
   Libraries, and Embedded Content* → set **both** to **Embed & Sign**.

2. **Add the Swift wrapper.** Drag `ios/vendor/SherpaOnnx.swift` into the
   `Vesper/Audio/Neural` group (Copy items if needed; Vesper target).

3. **Add the bridging header.** Drag `ios/docs/Vesper-Bridging-Header.h` into the
   `Vesper` group (Copy items if needed). Then project ▸ Vesper target ▸ **Build
   Settings** ▸ search *"bridging"* ▸ set **Objective-C Bridging Header** =
   `Vesper/Vesper-Bridging-Header.h`. (If a later build says *"c-api.h not found"*,
   add the framework's headers to **Header Search Paths**:
   `$(BUILT_PRODUCTS_DIR)/../../SourcePackages` isn't needed — instead point it at
   the xcframework's `Headers` dir, recursive.)

4. **Add the backend.** In Finder duplicate `ios/docs/KokoroOnnxBackend.swift.template`,
   rename the copy to `KokoroOnnxBackend.swift` (drop `.template`), and drag it
   into `Vesper/Audio/Neural` (Vesper target).

5. **Add the model.** Drag the **`ios/vendor/kokoro`** folder into the project →
   in the sheet choose **"Create folder references"** (you'll get a **blue**
   folder, not a yellow group), Copy items if needed, Vesper target. This bundles
   the model; `KokoroModel.bundledDir` finds it because it's named `kokoro`.

6. **Register the engine.** Open `Vesper/VesperApp.swift` and add an `init`:
   ```swift
   @main
   struct VesperApp: App {
       init() { NeuralTTS.backend = KokoroOnnxBackend() }
       var body: some Scene { WindowGroup { RootView() } }
   }
   ```

7. **Build & run** to your iPhone. Open **Sleep ▸ Voice** — the Kokoro voices now
   appear ("Heart · US ♀ · Neural", …). Pick one and tap **Preview**.

## Verify / troubleshoot

- **`c-api.h` not found** → the bridging header import is `sherpa-onnx/c-api/c-api.h`;
  if Xcode can't find it, add the xcframework's `Headers` folder to *Header Search
  Paths* (recursive) in Build Settings.
- **Linker errors about onnxruntime** → make sure **both** xcframeworks are
  *Embed & Sign* (step 1).
- **No neural voices in the picker** → the dragged folder must be **blue**
  (folder reference), named exactly `kokoro`, and in the Vesper target; confirm
  `model.onnx` is inside it.
- **A voice's name doesn't match how it sounds** → expected. The `sid` indices in
  this multilingual `voices.bin` don't perfectly line up with `KokoroCatalog`'s
  English names. The audio is real neural Kokoro; just pick the voice you like by
  ear. To fix labels, reorder `KokoroCatalog.all` to match the model's speaker
  order. (I can help map them once you tell me which sounds like what.)
- **App is large (~190 MB)** → that's the bundled model. Fine for device installs;
  for App Store later, switch to on-demand download (extend `KokoroDownloader` to
  fetch + unpack the `.tar.bz2`).

## If you ever need to re-fetch the staged files

```bash
cd ios/vendor
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.13.3/sherpa-onnx-v1.13.3-ios.tar.bz2
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-int8-multi-lang-v1_1.tar.bz2
curl -LO https://raw.githubusercontent.com/k2-fsa/sherpa-onnx/master/swift-api-examples/SherpaOnnx.swift
# then unpack and arrange as the table above
```
