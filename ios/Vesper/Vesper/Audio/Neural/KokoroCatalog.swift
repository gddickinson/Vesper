//  KokoroCatalog.swift
//  Vesper — the Kokoro neural-TTS voice catalog + on-device model locations.
//
//  Kokoro is the same high-quality neural voice family the desktop app uses
//  (~50 natural voices, fully offline). On iOS the model is downloaded once into
//  Application Support and run on-device by a NeuralTTSBackend (see
//  docs/KOKORO_IOS.md). This file is pure data + paths — no ML dependency — so it
//  always compiles; the inference backend is plugged in separately.

import Foundation

struct KokoroVoice: Identifiable, Hashable {
    let id: String          // Kokoro voice key, e.g. "af_heart"
    let name: String        // display, e.g. "Heart"
    let accent: String      // "US" / "UK"
    let female: Bool

    var label: String { "\(name) · \(accent) \(female ? "♀" : "♂") · Neural" }
}

enum KokoroCatalog {
    /// A curated set of the Kokoro v1.0 voices (af = US female, am = US male,
    /// bf = UK female, bm = UK male). More can be added freely — they all ship
    /// inside the one voices file.
    static let all: [KokoroVoice] = [
        KokoroVoice(id: "af_heart",    name: "Heart",    accent: "US", female: true),
        KokoroVoice(id: "af_bella",    name: "Bella",    accent: "US", female: true),
        KokoroVoice(id: "af_nicole",   name: "Nicole",   accent: "US", female: true),
        KokoroVoice(id: "af_sarah",    name: "Sarah",    accent: "US", female: true),
        KokoroVoice(id: "af_sky",      name: "Sky",      accent: "US", female: true),
        KokoroVoice(id: "af_aoede",    name: "Aoede",    accent: "US", female: true),
        KokoroVoice(id: "af_kore",     name: "Kore",     accent: "US", female: true),
        KokoroVoice(id: "af_nova",     name: "Nova",     accent: "US", female: true),
        KokoroVoice(id: "am_adam",     name: "Adam",     accent: "US", female: false),
        KokoroVoice(id: "am_michael",  name: "Michael",  accent: "US", female: false),
        KokoroVoice(id: "am_fenrir",   name: "Fenrir",   accent: "US", female: false),
        KokoroVoice(id: "am_puck",     name: "Puck",     accent: "US", female: false),
        KokoroVoice(id: "am_onyx",     name: "Onyx",     accent: "US", female: false),
        KokoroVoice(id: "bf_emma",     name: "Emma",     accent: "UK", female: true),
        KokoroVoice(id: "bf_isabella", name: "Isabella", accent: "UK", female: true),
        KokoroVoice(id: "bf_alice",    name: "Alice",    accent: "UK", female: true),
        KokoroVoice(id: "bf_lily",     name: "Lily",     accent: "UK", female: true),
        KokoroVoice(id: "bm_george",   name: "George",   accent: "UK", female: false),
        KokoroVoice(id: "bm_daniel",   name: "Daniel",   accent: "UK", female: false),
        KokoroVoice(id: "bm_lewis",    name: "Lewis",    accent: "UK", female: false),
        KokoroVoice(id: "bm_fable",    name: "Fable",    accent: "UK", female: false),
    ]

    static func byID(_ id: String) -> KokoroVoice? { all.first { $0.id == id } }

    // Voice picker ids are prefixed so the engine can tell neural from system.
    static let pickerPrefix = "kokoro:"
    static func pickerID(_ v: KokoroVoice) -> String { pickerPrefix + v.id }
    static func voiceID(fromPicker id: String) -> String? {
        id.hasPrefix(pickerPrefix) ? String(id.dropFirst(pickerPrefix.count)) : nil
    }
}

/// Where the downloaded Kokoro model + voices live, and whether they're present.
enum KokoroModel {
    /// Default download sources (the public kokoro-onnx release assets). The
    /// int8 model is ~80 MB; the voices file ~26 MB.
    static let modelURL = URL(string: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx")!
    static let voicesURL = URL(string: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin")!

    static var dir: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory,
                                            in: .userDomainMask)[0]
        let d = base.appendingPathComponent("VesperNeural", isDirectory: true)
        try? FileManager.default.createDirectory(at: d, withIntermediateDirectories: true)
        return d
    }
    // Download destinations (used by KokoroDownloader).
    static var modelPath: URL { dir.appendingPathComponent("kokoro.onnx") }
    static var voicesPath: URL { dir.appendingPathComponent("voices.bin") }

    private static func exists(_ u: URL) -> Bool { FileManager.default.fileExists(atPath: u.path) }
    static var downloaded: Bool { exists(modelPath) && exists(voicesPath) }

    /// A Kokoro model folder bundled into the app (drag the unpacked sherpa-onnx
    /// `kokoro-…` folder in as a *folder reference* named `kokoro`). See
    /// docs/KOKORO_SHERPA_WALKTHROUGH.md.
    static var bundledDir: URL? { Bundle.main.url(forResource: "kokoro", withExtension: nil) }
    static var bundled: Bool { bundledDir.map { exists($0.appendingPathComponent("model.onnx")) } ?? false }

    /// Is a usable Kokoro model present (bundled or downloaded)?
    static var isDownloaded: Bool { bundled || downloaded }

    // Paths the inference backend should read — prefer the bundled folder, which
    // also carries the tokens + espeak-ng-data that sherpa-onnx needs.
    static var resolvedModel: URL { bundledDir?.appendingPathComponent("model.onnx") ?? modelPath }
    static var resolvedVoices: URL { bundledDir?.appendingPathComponent("voices.bin") ?? voicesPath }
    static var resolvedTokens: URL? { bundledDir?.appendingPathComponent("tokens.txt") }
    static var resolvedDataDir: URL? { bundledDir?.appendingPathComponent("espeak-ng-data") }

    /// Comma-joined English lexicons (the multilingual model needs these for
    /// good g2p; empty for models that only use espeak-ng-data).
    static var resolvedLexicon: String {
        guard let d = bundledDir else { return "" }
        return ["lexicon-us-en.txt", "lexicon-gb-en.txt"]
            .map { d.appendingPathComponent($0) }
            .filter { exists($0) }
            .map { $0.path }
            .joined(separator: ",")
    }

    static func removeDownload() {
        try? FileManager.default.removeItem(at: modelPath)
        try? FileManager.default.removeItem(at: voicesPath)
    }
}
