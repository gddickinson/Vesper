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
    /// If > 0, a pure sine at this Hz (isochronic/solfeggio) replaces the noise
    /// bed; the swell LFO (swellRate/swellDepth) becomes the entrainment pulse.
    let tone: Float
    /// If true, a slowly-evolving generative chord pad replaces the noise bed
    /// (detuned sine partials + per-tone LFOs + a drifting root + an LP sweep).
    let pad: Bool

    init(name: String, colour: NoiseColour, filter: BiquadKind, freq: Float, q: Float,
         sweepRate: Float, sweepDepth: Float, swellRate: Float, swellDepth: Float,
         crackle: Float, gain: Float, tone: Float = 0, pad: Bool = false) {
        self.name = name; self.colour = colour; self.filter = filter; self.freq = freq
        self.q = q; self.sweepRate = sweepRate; self.sweepDepth = sweepDepth
        self.swellRate = swellRate; self.swellDepth = swellDepth; self.crackle = crackle
        self.gain = gain; self.tone = tone; self.pad = pad
    }

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
        // — more nature beds —
        AmbienceVoice(name: "Distant Surf", colour: .brown, filter: .lowpass, freq: 480, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.07, swellDepth: 0.85,
                      crackle: 0, gain: 0.7),
        AmbienceVoice(name: "Rain on Roof", colour: .pink, filter: .lowpass, freq: 2600, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.2, swellDepth: 0.15,
                      crackle: 0.6, gain: 0.4),
        AmbienceVoice(name: "Forest Wind", colour: .brown, filter: .bandpass, freq: 520, q: 0.8,
                      sweepRate: 0.05, sweepDepth: 300, swellRate: 0.08, swellDepth: 0.5,
                      crackle: 0, gain: 0.75),
        AmbienceVoice(name: "Summer Night", colour: .white, filter: .bandpass, freq: 4800, q: 8,
                      sweepRate: 0, sweepDepth: 0, swellRate: 1.8, swellDepth: 0.85,
                      crackle: 0, gain: 0.16),
        AmbienceVoice(name: "Cafe Murmur", colour: .pink, filter: .lowpass, freq: 900, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.3, swellDepth: 0.25,
                      crackle: 0, gain: 0.3),
        AmbienceVoice(name: "Fan / Air", colour: .pink, filter: .lowpass, freq: 1400, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0, swellDepth: 0,
                      crackle: 0, gain: 0.45),
        AmbienceVoice(name: "Waterfall", colour: .white, filter: .lowpass, freq: 1700, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.05, swellDepth: 0.1,
                      crackle: 0, gain: 0.4),
        AmbienceVoice(name: "Heavy Rain", colour: .white, filter: .lowpass, freq: 3200, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.18, swellDepth: 0.22,
                      crackle: 0.4, gain: 0.42),
        // — gentle entrainment / solfeggio tones (low level) —
        AmbienceVoice(name: "Theta Pulse (6 Hz)", colour: .pink, filter: .lowpass, freq: 210, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 6, swellDepth: 1.0,
                      crackle: 0, gain: 0.10, tone: 210),
        AmbienceVoice(name: "Delta Pulse (2.5 Hz)", colour: .pink, filter: .lowpass, freq: 130, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 2.5, swellDepth: 1.0,
                      crackle: 0, gain: 0.10, tone: 130),
        AmbienceVoice(name: "Solfeggio 528 Hz", colour: .pink, filter: .lowpass, freq: 528, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.25, swellDepth: 0.3,
                      crackle: 0, gain: 0.08, tone: 528),
        AmbienceVoice(name: "Solfeggio 432 Hz", colour: .pink, filter: .lowpass, freq: 432, q: 0.7,
                      sweepRate: 0, sweepDepth: 0, swellRate: 0.22, swellDepth: 0.3,
                      crackle: 0, gain: 0.08, tone: 432),
        // — soft pink noise with a ~0.8 Hz swell: open-loop acoustic stimulation
        //   shown to support slow-wave (deep) sleep (pink chosen for comfort) —
        AmbienceVoice(name: "Deep Sleep (Pink Noise)", colour: .pink, filter: .lowpass,
                      freq: 1600, q: 0.7, sweepRate: 0, sweepDepth: 0,
                      swellRate: 0.8, swellDepth: 0.35, crackle: 0, gain: 0.34),
        // — generative evolving pad —
        AmbienceVoice(name: "Dreamfield (Generative)", colour: .pink, filter: .lowpass,
                      freq: 1200, q: 0.7, sweepRate: 0, sweepDepth: 0,
                      swellRate: 0, swellDepth: 0, crackle: 0, gain: 0.55, pad: true),
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
    private var tonePhase: Float = 0
    private var smFreq: Float

    // generative pad state (carried across callbacks → click-free)
    private var padOscPhase = [Float](repeating: 0, count: 10)  // 5 tones × 2 partials
    private var padAmpPhase  = [Float](repeating: 0, count: 5)
    private var padRoot: Float = 110
    private var padTargetIdx = 0
    private var padTimer: Float = 0
    private var padCutPhase: Float = 0
    /// Pentatonic roots (A2 C3 D3 E3 G3) and a soft minor-9 voicing (semitone mults).
    private let padRoots: [Float] = [110.0, 130.81, 146.83, 164.81, 196.0]
    private let padMult:  [Float] = [1.0, 1.18921, 1.49831, 1.78180, 2.24492]

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
        if voice.pad { renderPad(buf, frames: frames); return }
        let dt = 1.0 / sr
        let targetLevel = max(0, min(1, level))
        for i in 0..<frames {
            // amplitude swell (ocean / crickets) — or the entrainment pulse for tones
            var amp: Float = 1
            if voice.swellDepth > 0 {
                swellPhase += voice.swellRate * dt
                let lfo = 0.5 + 0.5 * sin(2 * .pi * swellPhase)
                amp = (1 - voice.swellDepth) + voice.swellDepth * lfo
            }

            var s: Float
            if voice.tone > 0 {
                // pure isochronic / solfeggio tone
                tonePhase += voice.tone * dt
                if tonePhase >= 1 { tonePhase -= 1 }
                s = sin(2 * .pi * tonePhase)
            } else {
                // swept centre (wind)
                if voice.sweepDepth > 0 {
                    sweepPhase += voice.sweepRate * dt
                    let c = voice.freq + voice.sweepDepth * sin(2 * .pi * sweepPhase)
                    smFreq += 0.02 * (c - smFreq)
                    if (i & 63) == 0 { band.update(kind: voice.filter, freq: smFreq, q: voice.q) }
                }
                s = band.process(noise())
                // sparse crackle (fire)
                if voice.crackle > 0 {
                    if pops.next() > (1 - voice.crackle * 0.0009) { crackleEnv = 0.9 }
                    crackleEnv *= 0.9985
                    s += crackleEnv * pops.next() * 1.4
                }
            }

            smLevel += 0.002 * (targetLevel - smLevel)
            buf[i] += softClip(s * amp * voice.gain * smLevel)
        }
    }

    /// Generative evolving pad: a soft minor-9 chord of detuned sine partials over
    /// a slowly drifting pentatonic root, each tone breathing on its own slow LFO,
    /// summed through a gently swept low-pass. Stateful → click-free, never repeats.
    private func renderPad(_ buf: UnsafeMutablePointer<Float>, frames: Int) {
        let dt = 1.0 / sr
        let targetLevel = max(0, min(1, level))
        let detune: Float = 0.004
        for i in 0..<frames {
            // drift the root through the pentatonic every ~22s (gliding, no clicks)
            padTimer += dt
            if padTimer > 22 { padTimer = 0; padTargetIdx = (padTargetIdx + 2) % padRoots.count }
            padRoot += 0.00004 * (padRoots[padTargetIdx] - padRoot)
            // slow low-pass sweep for timbral movement
            padCutPhase += 0.025 * dt
            let cut = 900 + 600 * sin(2 * .pi * padCutPhase)
            if (i & 63) == 0 { band.update(kind: .lowpass, freq: max(140, cut), q: 0.7) }

            var s: Float = 0
            for ti in 0..<5 {
                let f = padRoot * padMult[ti]
                padAmpPhase[ti] += (0.015 + 0.011 * Float(ti)) * dt
                let toneAmp = 0.45 + 0.55 * (0.5 + 0.5 * sin(2 * .pi * padAmpPhase[ti]))
                for k in 0..<2 {
                    let idx = ti * 2 + k
                    let pf = f * (1 + (k == 0 ? -detune : detune))
                    padOscPhase[idx] += pf * dt
                    if padOscPhase[idx] >= 1 { padOscPhase[idx] -= 1 }
                    s += sin(2 * .pi * padOscPhase[idx]) * 0.07 * toneAmp
                }
            }
            s = band.process(s)
            smLevel += 0.002 * (targetLevel - smLevel)
            buf[i] += softClip(s * voice.gain * smLevel)
        }
    }
}
