//  BreathVoice.swift
//  Vesper — parametric breath-sound voices.
//
//  Each voice is a small set of synthesis parameters: a noise colour and a
//  band-pass centre for the in-breath and the out-breath, plus brightness and
//  gain. The BreathSynth turns these into a click-free, breath-paced sound. This
//  is the iOS analogue of the desktop "Breath / Nature" voice family; add a
//  voice by appending to `BreathVoice.all`.

import Foundation

enum NoiseColour { case white, pink, brown }

struct BreathVoice: Identifiable, Hashable {
    let name: String
    let colour: NoiseColour
    /// Band-pass centres (Hz) for the in-breath and out-breath — the out-breath
    /// usually sits a touch lower/darker, as real breath does.
    let inFreq: Float
    let outFreq: Float
    let q: Float
    /// Low-pass brightness cap (Hz); lower = softer/darker.
    let brightness: Float
    /// Calibrated output gain (peak-safe).
    let gain: Float
    let info: String

    var id: String { name }

    static func hash(into h: inout Hasher, _ v: BreathVoice) { h.combine(v.name) }
    func hash(into hasher: inout Hasher) { hasher.combine(name) }
    static func == (a: BreathVoice, b: BreathVoice) -> Bool { a.name == b.name }
}

extension BreathVoice {
    static let all: [BreathVoice] = [
        BreathVoice(name: "Ocean Breath (Ujjayi)", colour: .pink,
                    inFreq: 520, outFreq: 380, q: 1.4, brightness: 2600,
                    gain: 0.85,
                    info: "A soft oceanic hush — the classic ujjayi breath."),
        BreathVoice(name: "Soft Nose Breath", colour: .pink,
                    inFreq: 900, outFreq: 700, q: 2.2, brightness: 3400,
                    gain: 0.8,
                    info: "Quiet, intimate nasal breathing."),
        BreathVoice(name: "Gentle Wind", colour: .brown,
                    inFreq: 300, outFreq: 240, q: 0.9, brightness: 1800,
                    gain: 0.95,
                    info: "A low, rounded wind-like breath."),
        BreathVoice(name: "Deep Calm", colour: .brown,
                    inFreq: 220, outFreq: 180, q: 1.1, brightness: 1400,
                    gain: 1.0,
                    info: "Very low and warm; for winding down."),
        BreathVoice(name: "Airy Sigh", colour: .white,
                    inFreq: 1200, outFreq: 760, q: 1.0, brightness: 4200,
                    gain: 0.7,
                    info: "Brighter, breathier release — pairs with long exhales."),
    ]

    static let `default` = all[0]

    static func byName(_ name: String) -> BreathVoice? {
        all.first { $0.name == name }
    }
}
