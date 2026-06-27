//  BreathSynth.swift
//  Vesper — renders a breath voice into audio blocks, breath-paced.
//
//  Mirrors the desktop NoiseTrack: stateful noise → swept band-pass → brightness
//  low-pass, scaled by the breath `airflow` envelope (loud mid-breath, silent in
//  holds). Airflow and the in/out filter "mix" are linearly ramped across each
//  block, and all filters carry state across blocks, so the sound is click-free.
//  All hot-path methods are allocation-free and real-time safe.

import Foundation

final class BreathSynth {
    private let sr: Float
    private var voice: BreathVoice

    private var pink = PinkNoise()
    private var brown = BrownNoise()
    private var white = WhiteNoise()

    private var band: Biquad
    private var bright = OnePoleLP()

    // Smoothed control values (avoid per-sample filter retune cost / clicks).
    private var smFreq: Float
    private var smAmp: Float = 0

    /// 0…1 master level for the breathing bed (user controllable, ramped).
    var level: Float = 1.0
    private var smLevel: Float = 1.0

    init(sr: Float, voice: BreathVoice) {
        self.sr = sr
        self.voice = voice
        smFreq = voice.outFreq
        band = Biquad(sr: sr, kind: .bandpass, freq: voice.outFreq, q: voice.q)
        bright.setCutoff(voice.brightness, sr: sr)
    }

    func setVoice(_ v: BreathVoice) {
        voice = v
        bright.setCutoff(v.brightness, sr: sr)
        // filters keep state; centre eases over the next blocks via smFreq
    }

    @inline(__always) private func noise() -> Float {
        switch voice.colour {
        case .white: return white.next()
        case .pink:  return pink.next()
        case .brown: return brown.next()
        }
    }

    /// Render `frames` mono samples for the breath whose airflow/phase-mix go
    /// from (a0,m0) at block start to (a1,m1) at block end.
    /// `mix` is 1 for a pure in-breath colour, 0 for a pure out-breath colour.
    func render(into buf: UnsafeMutablePointer<Float>, frames: Int,
                airflow0: Float, airflow1: Float, mix0: Float, mix1: Float) {
        guard frames > 0 else { return }
        let inv = 1.0 / Float(frames)
        let targetLevel = max(0, min(1, level))

        for i in 0..<frames {
            let f = Float(i) * inv
            let airflow = airflow0 + (airflow1 - airflow0) * f
            let mix = mix0 + (mix1 - mix0) * f

            // band-pass centre eases between out- and in-breath colours
            let targetFreq = voice.outFreq + (voice.inFreq - voice.outFreq) * mix
            smFreq += 0.02 * (targetFreq - smFreq)
            if (i & 31) == 0 { band.update(kind: .bandpass, freq: smFreq, q: voice.q) }

            var s = noise()
            s = band.process(s)
            s = bright.process(s)

            // airflow envelope (smoothed a touch so onsets/edges stay soft)
            let env = airflow * airflow            // perceptually gentler ramp
            smAmp += 0.01 * (env - smAmp)
            smLevel += 0.001 * (targetLevel - smLevel)

            buf[i] = softClip(s * smAmp * voice.gain * smLevel)
        }
    }
}
