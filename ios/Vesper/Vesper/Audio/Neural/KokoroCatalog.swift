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
    let sid: Int            // speaker index inside voices.bin (THE source of truth)
    let name: String        // display, e.g. "Heart"
    let accent: String      // "US" / "UK"
    let female: Bool

    var label: String { "\(name) · \(accent) \(female ? "♀" : "♂") · Neural" }
}

enum KokoroCatalog {
    /// The 28 English voices of the Kokoro v1.0 family, each pinned to its real
    /// speaker id (`sid`) inside `voices.bin`. The `sid` is the alphabetical
    /// index of the voice key across the whole multilingual voices file
    /// (af_* 0–10, am_* 11–19, bf_* 20–23, bm_* 24–27) — this is the order
    /// sherpa-onnx's `kokoro-multi-lang-v1_0` uses, and it is the ONLY thing the
    /// engine reads. Display order below is grouped for the picker; the `sid` is
    /// what selects the actual speaker, so never infer it from list position.
    static let all: [KokoroVoice] = [
        // American female (af_) — sids 0–10
        KokoroVoice(id: "af_heart",    sid: 3,  name: "Heart",    accent: "US", female: true),
        KokoroVoice(id: "af_bella",    sid: 2,  name: "Bella",    accent: "US", female: true),
        KokoroVoice(id: "af_nicole",   sid: 6,  name: "Nicole",   accent: "US", female: true),
        KokoroVoice(id: "af_aoede",    sid: 1,  name: "Aoede",    accent: "US", female: true),
        KokoroVoice(id: "af_kore",     sid: 5,  name: "Kore",     accent: "US", female: true),
        KokoroVoice(id: "af_sarah",    sid: 9,  name: "Sarah",    accent: "US", female: true),
        KokoroVoice(id: "af_nova",     sid: 7,  name: "Nova",     accent: "US", female: true),
        KokoroVoice(id: "af_sky",      sid: 10, name: "Sky",      accent: "US", female: true),
        KokoroVoice(id: "af_alloy",    sid: 0,  name: "Alloy",    accent: "US", female: true),
        KokoroVoice(id: "af_jessica",  sid: 4,  name: "Jessica",  accent: "US", female: true),
        KokoroVoice(id: "af_river",    sid: 8,  name: "River",    accent: "US", female: true),
        // American male (am_) — sids 11–19
        KokoroVoice(id: "am_adam",     sid: 11, name: "Adam",     accent: "US", female: false),
        KokoroVoice(id: "am_michael",  sid: 16, name: "Michael",  accent: "US", female: false),
        KokoroVoice(id: "am_fenrir",   sid: 14, name: "Fenrir",   accent: "US", female: false),
        KokoroVoice(id: "am_puck",     sid: 18, name: "Puck",     accent: "US", female: false),
        KokoroVoice(id: "am_onyx",     sid: 17, name: "Onyx",     accent: "US", female: false),
        KokoroVoice(id: "am_echo",     sid: 12, name: "Echo",     accent: "US", female: false),
        KokoroVoice(id: "am_eric",     sid: 13, name: "Eric",     accent: "US", female: false),
        KokoroVoice(id: "am_liam",     sid: 15, name: "Liam",     accent: "US", female: false),
        KokoroVoice(id: "am_santa",    sid: 19, name: "Santa",    accent: "US", female: false),
        // British female (bf_) — sids 20–23
        KokoroVoice(id: "bf_emma",     sid: 21, name: "Emma",     accent: "UK", female: true),
        KokoroVoice(id: "bf_isabella", sid: 22, name: "Isabella", accent: "UK", female: true),
        KokoroVoice(id: "bf_alice",    sid: 20, name: "Alice",    accent: "UK", female: true),
        KokoroVoice(id: "bf_lily",     sid: 23, name: "Lily",     accent: "UK", female: true),
        // British male (bm_) — sids 24–27
        KokoroVoice(id: "bm_george",   sid: 26, name: "George",   accent: "UK", female: false),
        KokoroVoice(id: "bm_fable",    sid: 25, name: "Fable",    accent: "UK", female: false),
        KokoroVoice(id: "bm_daniel",   sid: 24, name: "Daniel",   accent: "UK", female: false),
        KokoroVoice(id: "bm_lewis",    sid: 27, name: "Lewis",    accent: "UK", female: false),
    ]

    static func byID(_ id: String) -> KokoroVoice? { all.first { $0.id == id } }

    /// The real speaker id for a Kokoro voice key (0 = first US female if unknown).
    static func sid(forID id: String) -> Int { byID(id)?.sid ?? 0 }

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
