//  DSP.swift
//  Vesper — small stateful DSP primitives (port of breathsim/dsp.py).
//
//  Filters and noise generators are STATEFUL and carry state across render
//  callbacks, so blocks join click-free — the same rule the desktop engine
//  follows. Everything here is allocation-free in its hot path and safe to run
//  on the real-time audio thread.

import Foundation

/// Deterministic, fast white-noise source (xorshift) → unit-ish amplitude.
struct WhiteNoise {
    private var s: UInt32
    init(seed: UInt32 = 0x9E3779B9) { s = seed == 0 ? 1 : seed }
    @inline(__always) mutating func next() -> Float {
        s ^= s << 13; s ^= s >> 17; s ^= s << 5
        // map to [-1, 1)
        return Float(Int32(bitPattern: s)) / Float(Int32.max)
    }
}

/// Pink noise (−3 dB/oct) via Paul Kellet's economical filter. ~unit RMS.
struct PinkNoise {
    private var white = WhiteNoise(seed: 0x1234567)
    private var b0: Float = 0, b1: Float = 0, b2: Float = 0
    private var b3: Float = 0, b4: Float = 0, b5: Float = 0, b6: Float = 0
    init(seed: UInt32 = 0x1234567) { white = WhiteNoise(seed: seed) }
    @inline(__always) mutating func next() -> Float {
        let w = white.next()
        b0 = 0.99886 * b0 + w * 0.0555179
        b1 = 0.99332 * b1 + w * 0.0750759
        b2 = 0.96900 * b2 + w * 0.1538520
        b3 = 0.86650 * b3 + w * 0.3104856
        b4 = 0.55000 * b4 + w * 0.5329522
        b5 = -0.7616 * b5 - w * 0.0168980
        let pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362
        b6 = w * 0.115926
        return pink * 0.11   // normalise toward unit RMS
    }
}

/// Brown / red noise (−6 dB/oct): leaky-integrated white.
struct BrownNoise {
    private var white = WhiteNoise(seed: 0x55AA55AA)
    private var last: Float = 0
    init(seed: UInt32 = 0x55AA55AA) { white = WhiteNoise(seed: seed) }
    @inline(__always) mutating func next() -> Float {
        last = (last + 0.02 * white.next()) / 1.02
        return last * 3.5
    }
}

/// One-pole low-pass — cheap smoothing / brightness control.
struct OnePoleLP {
    private var z: Float = 0
    private var a: Float = 0.5
    /// `cutoff` in Hz at `sr`.
    mutating func setCutoff(_ cutoff: Float, sr: Float) {
        let c = max(1, min(cutoff, sr * 0.49))
        a = Float(1 - exp(-2.0 * Double.pi * Double(c) / Double(sr)))
    }
    @inline(__always) mutating func process(_ x: Float) -> Float {
        z += a * (x - z); return z
    }
    mutating func reset() { z = 0 }
}

enum BiquadKind { case lowpass, highpass, bandpass }

/// RBJ cookbook biquad (Direct Form I), stateful. Re-tunable mid-stream via
/// `update` for swept filters (kept click-free by smooth parameter moves).
struct Biquad {
    private var b0: Float = 1, b1: Float = 0, b2: Float = 0
    private var a1: Float = 0, a2: Float = 0
    private var x1: Float = 0, x2: Float = 0, y1: Float = 0, y2: Float = 0
    private let sr: Float

    init(sr: Float, kind: BiquadKind = .lowpass, freq: Float = 1000, q: Float = 0.707) {
        self.sr = sr
        update(kind: kind, freq: freq, q: q)
    }

    mutating func update(kind: BiquadKind, freq: Float, q: Float) {
        let f = max(20, min(freq, sr * 0.49))
        let w0 = 2 * Float.pi * f / sr
        let cw = cos(w0), sw = sin(w0)
        let alpha = sw / (2 * max(0.0001, q))
        var nb0: Float = 1, nb1: Float = 0, nb2: Float = 0
        let a0: Float
        switch kind {
        case .lowpass:
            nb0 = (1 - cw) / 2; nb1 = 1 - cw; nb2 = (1 - cw) / 2
        case .highpass:
            nb0 = (1 + cw) / 2; nb1 = -(1 + cw); nb2 = (1 + cw) / 2
        case .bandpass:
            nb0 = alpha; nb1 = 0; nb2 = -alpha
        }
        a0 = 1 + alpha
        let na1: Float = -2 * cw
        let na2: Float = 1 - alpha
        b0 = nb0 / a0; b1 = nb1 / a0; b2 = nb2 / a0
        a1 = na1 / a0; a2 = na2 / a0
    }

    @inline(__always) mutating func process(_ x: Float) -> Float {
        let y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2 = x1; x1 = x; y2 = y1; y1 = y
        return y
    }

    mutating func resetState() { x1 = 0; x2 = 0; y1 = 0; y2 = 0 }
}

/// Gentle saturating limiter to keep the bus inside [-1, 1] without hard clicks.
@inline(__always) func softClip(_ x: Float) -> Float {
    if x > 1.2 { return 1 }
    if x < -1.2 { return -1 }
    return x - (x * x * x) / 3.6
}
