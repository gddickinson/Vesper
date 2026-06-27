# Kokoro neural narration on iOS

Vesper can narrate with **Kokoro** — the same high-quality, fully-offline neural
voices the desktop app uses. The app ships everything *around* the model so it
always builds with **no ML dependency**; the on-device inference engine is added
as one separate piece.

## What's already in the app

| File | Role |
|---|---|
| `Audio/Neural/KokoroCatalog.swift` | the voice catalog (Heart, Bella, George, Emma…) + model file locations + `isDownloaded` |
| `Audio/Neural/NeuralTTS.swift` | the `NeuralTTSBackend` plug-point + `KokoroDownloader` (downloads the model + voices into Application Support, with progress) |
| `Audio/Neural/NeuralNarrator.swift` | streams synthesized float-PCM through an `AVAudioPlayerNode`, with breath-length gaps between lines |
| Sleep ▸ **Neural voices (beta)** card | one-tap model download + status |

`NeuralTTS.backend` is `nil` by default, so the app cleanly uses the system /
Personal voices until an engine is registered.

## The two steps to switch it on

### 1. Add an ONNX engine that can run Kokoro

Kokoro needs **phonemes**, so the engine must include a phonemizer. The smoothest
route is **sherpa-onnx** (it bundles onnxruntime + espeak-ng data + the Kokoro
tokenizer and has prebuilt iOS frameworks and a Swift API):

- Repo: <https://github.com/k2-fsa/sherpa-onnx> (see its `swift-api-examples` and
  the iOS TTS example).
- Add it to the project (Xcode ▸ File ▸ Add Package Dependencies… or drop in the
  prebuilt `sherpa-onnx.xcframework`).
- Its Kokoro bundle includes `model.onnx`, `voices.bin`, `tokens.txt`,
  `espeak-ng-data/`, and lexicon files — point `KokoroModel`'s URLs/paths at that
  bundle (or download it with the existing `KokoroDownloader`, extending it to
  fetch the extra files).

(Alternative: `microsoft/onnxruntime-swift-package-manager` + your own espeak-ng
phonemizer — more work, since you supply the g2p.)

### 2. Implement `NeuralTTSBackend` and register it

```swift
import SherpaOnnx   // from the package you added

final class KokoroOnnxBackend: NeuralTTSBackend {
    private let tts: SherpaOnnxOfflineTtsWrapper   // configured with the Kokoro files

    init?() {
        guard KokoroModel.isDownloaded else { return nil }
        var cfg = sherpaOnnxOfflineTtsConfig(/* model, voices, tokens, dataDir … */)
        tts = SherpaOnnxOfflineTtsWrapper(config: &cfg)
    }

    func synthesize(text: String, voiceID: String, speed: Float)
        -> (samples: [Float], sampleRate: Double)? {
        // map voiceID ("af_heart"…) to the Kokoro speaker index
        let sid = KokoroCatalog.all.firstIndex { $0.id == voiceID } ?? 0
        let audio = tts.generate(text: text, sid: Int(sid), speed: speed)
        return (audio.samples, Double(audio.sampleRate))   // Kokoro = 24000 Hz
    }
}

// in VesperApp init (or first launch):
NeuralTTS.backend = KokoroOnnxBackend()
```

Once `NeuralTTS.backend` is set and the model is downloaded:
- add the Kokoro voices to the picker (prefix their ids with `KokoroCatalog.pickerPrefix`),
- in `SessionViewModel.start()`, if the selected id is a neural one
  (`KokoroCatalog.voiceID(fromPicker:)`), drive a `NeuralNarrator` instead of the
  system `Narrator`.

## Why it's staged this way

Bundling a ~300 MB ML runtime + model into the repo isn't practical, and the
phonemizer/runtime choice is best made interactively in Xcode. So the app stays
lean and always-building, the model is fetched on demand, and the engine is a
single drop-in conformance. Everything else (download, playback, voices, UI) is
already done.
