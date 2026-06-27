//  Ambience.swift
//  Vesper — procedural nature ambience beds (the iOS analogue of the desktop
//  GROUP_NATURE voices). One parametric engine covers rain, ocean surf, wind,
//  fire, a stream, crickets and plain masking noise: a noise colour through a
//  (optionally swept) filter, with an amplitude swell LFO and sparse crackle.
//  Continuous (not breath-gated), click-free, allocation-free on the hot path.

import Foundation

struct AmbienceVoice: Identifiable, Hashable {
    let name: String
    let colour: NoiseColour
    let filter: BiquadKind
    let freq: Float
    let q: Float
    /// Filter-centre sweep (wind): LFO rate (Hz) and depth (Hz).
    let sweepRate: Float
    let sweepDepth: Float
    /// Amplitude swell (ocean / crickets): LFO rate (Hz) and depth (0…1).
    let swellRate: Float
    let swellDepth: Float
    /// Sparse crackle density 0…1 (fire).
    let crackle: Float
    let gain: Float

    var id: String { name }
    func hash(into h: inout Hasher) { h.combine(name) }
    static func == (a: AmbienceVoice, b: AmbienceVoice) -> Bool { a.name == b.name }
}

extension AmbienceVoice {
    static let all: [AmbienceVoice] = [
        AmbienceVoice(name: "None", colour: .pink, filter: .lowpass, freq: 800, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0, swellDepth: 0,
                      crackle: 0, gain: 0),
        AmbienceVoice(name: "Rain", colour: .white, filter: .highpass, freq: 1100, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.13, swellDepth: 0.18,
                      crackle: 0, gain: 0.34),
        AmbienceVoice(name: "Ocean Surf", colour: .brown, filter: .lowpass, freq: 700, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.10, swellDepth: 0.75,
                      crackle: 0, gain: 0.85),
        AmbienceVoice(name: "Soft Wind", colour: .brown, filter: .bandpass, freq: 420, q: 0.8,
                      sweepRate: 0.07, sweepDepth: 240, swellRate: 0.09, swellDepth: 0.45,
                      crackle: 0, gain: 0.8),
        AmbienceVoice(name: "Crackling Fire", colour: .brown, filter: .lowpass, freq: 500, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.6, swellDepth: 0.25,
                      crackle: 0.9, gain: 0.7),
        AmbienceVoice(name: "Mountain Stream", colour: .pink, filter: .highpass, freq: 1400, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.5, swellDepth: 0.12,
                      crackle: 0, gain: 0.32),
        AmbienceVoice(name: "Night Crickets", colour: .white, filter: .bandpass, freq: 4600, q: 9,
                      sweepRate: 0, sweepDepth: 0, swellRate: 2.4, swellDepth: 0.92,
                      crackle: 0, gain: 0.22),
        AmbienceVoice(name: "Pink Noise", colour: .pink, filter: .lowpass, freq: 6000, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0, swellDepth: 0,
                      crackle: 0, gain: 0.32),
        AmbienceVoice(name: "Brown Noise", colour: .brown, filter: .lowpass, freq: 1200, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0, swellDepth: 0,
                      crackle: 0, gain: 0.7),
    ]
    static func byName(_ n: String) -> AmbienceVoice? { all.first { $0.name == n } }
}

final class AmbienceSynth {
    private let sr: Float
    private var voice: AmbienceVoice

    private var pink = PinkNoise(seed: 0xBEEF01)
    private var brown = BrownNoise(seed: 0xBEEF02)
    private var white = WhiteNoise(seed: 0xBEEF03)
    private var pops = WhiteNoise(seed: 0xBEEF04)

    private var band: Biquad
    private var sweepPhase: Float = 0
    private var swellPhase: Float = 0
    private var crackleEnv: Float = 0
    private var smFreq: Float

    /// 0…1 user level for the ambience bed (ramped).
    var level: Float = 0.6
    private var smLevel: Float = 0

    init(sr: Float, voice: AmbienceVoice) {
        self.sr = sr
        self.voice = voice
        smFreq = voice.freq
        band = Biquad(sr: sr, kind: voice.filter, freq: voice.freq, q: voice.q)
    }

    func setVoice(_ v: AmbienceVoice) {
        voice = v
        smFreq = v.freq
        band.update(kind: v.filter, freq: v.freq, q: v.q)
    }

    @inline(__always) private func noise() -> Float {
        switch voice.colour {
        case .white: return white.next()
        case .pink:  return pink.next()
        case .brown: return brown.next()
        }
    }

    /// Add `frames` samples of the ambience bed into `buf` (mixes on top).
    func addInto(_ buf: UnsafeMutablePointer<Float>, frames: Int) {
        guard frames > 0, voice.gain > 0 else {
            // still ease the level down so a switch to None fades out
            smLevel += 0.001 * (0 - smLevel)
            return
        }
        let dt = 1.0 / sr
        let targetLevel = max(0, min(1, level))
        for i in 0..<frames {
            // swept centre (wind)
            if voice.sweepDepth > 0 {
                sweepPhase += voice.sweepRate * dt
                let c = voice.freq + voice.sweepDepth * sin(2 * .pi * sweepPhase)
                smFreq += 0.02 * (c - smFreq)
                if (i & 63) == 0 { band.update(kind: voice.filter, freq: smFreq, q: voice.q) }
            }
            var s = band.process(noise())

            // amplitude swell (ocean / crickets)
            var amp: Float = 1
            if voice.swellDepth > 0 {
                swellPhase += voice.swellRate * dt
                let lfo = 0.5 + 0.5 * sin(2 * .pi * swellPhase)
                amp = (1 - voice.swellDepth) + voice.swellDepth * lfo
            }

            // sparse crackle (fire)
            if voice.crackle > 0 {
                if pops.next() > (1 - voice.crackle * 0.0009) {
                    crackleEnv = 0.9
                }
                crackleEnv *= 0.9985
                s += crackleEnv * pops.next() * 1.4
            }

            smLevel += 0.002 * (targetLevel - smLevel)
            buf[i] += softClip(s * amp * voice.gain * smLevel)
        }
    }
}
