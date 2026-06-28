//  Coherence.swift
//  Vesper — a pure, testable heart-rate-variability "coherence" model. Feed it
//  instantaneous heart-rate samples over time; it resamples the tachogram onto a
//  uniform grid and measures how much of the HRV power sits in the slow
//  "breathing band" (~0.04–0.15 Hz, peak ~0.1 Hz / 6 breaths-per-minute). A high
//  fraction = a steady, coherent heart rhythm (the resonance-breathing goal).
//  No UIKit, deterministic, allocation-light. See [[vesper-ios-feature-roadmap]].

import Foundation

final class CoherenceModel {
    private var times = [Double]()
    private var hrs = [Double]()
    private let cap = 400
    private let window = 50.0        // seconds analysed
    private let fs = 2.0             // tachogram resample rate (Hz)

    /// 0…1 coherence score (smoothed) and the breaths/min that currently
    /// dominates the breathing band (the adaptive resonance-pace suggestion).
    private(set) var coherence = 0.0
    private(set) var suggestedBpm = 6.0

    func reset() {
        times.removeAll(keepingCapacity: true)
        hrs.removeAll(keepingCapacity: true)
        coherence = 0; suggestedBpm = 6
    }

    /// Add one instantaneous heart-rate sample (bpm) at monotonic time `t` (s).
    func add(hr: Double, at t: Double) {
        guard hr.isFinite, hr > 20, hr < 220 else { return }
        times.append(t); hrs.append(hr)
        if times.count > cap {
            times.removeFirst(times.count - cap)
            hrs.removeFirst(hrs.count - cap)
        }
    }

    /// Recompute the score (call ~1×/s). Needs ≥12 s of data, else 0.
    func update() {
        guard let last = times.last, let first = times.first else { coherence = 0; return }
        let win = Swift.min(window, last - first)
        guard win >= 12 else { coherence = 0; return }
        let n = Int(win * fs)
        guard n >= 16 else { coherence = 0; return }

        // resample onto a uniform grid via linear interpolation
        let start = last - win
        var grid = [Double](repeating: 0, count: n)
        var j = 0
        for i in 0..<n {
            let t = start + Double(i) / fs
            while j + 1 < times.count && times[j + 1] < t { j += 1 }
            if t <= times[0] { grid[i] = hrs[0] }
            else if t >= times[times.count - 1] { grid[i] = hrs[hrs.count - 1] }
            else {
                let t0 = times[j], t1 = times[j + 1]
                let frac = t1 > t0 ? (t - t0) / (t1 - t0) : 0
                grid[i] = hrs[j] + (hrs[j + 1] - hrs[j]) * frac
            }
        }

        // detrend (remove mean) + Hann window
        let mean = grid.reduce(0, +) / Double(n)
        for i in 0..<n {
            let w = 0.5 - 0.5 * cos(2 * .pi * Double(i) / Double(n - 1))
            grid[i] = (grid[i] - mean) * w
        }

        // power across the breathing-relevant frequencies (Goertzel)
        var total = 0.0, band = 0.0, bestP = 0.0, bestF = 0.1
        var f = 0.05
        while f <= 0.40 {
            let p = Self.goertzel(grid, fs: fs, freq: f)
            total += p
            if f >= 0.04 && f <= 0.15 {
                band += p
                if p > bestP { bestP = p; bestF = f }
            }
            f += 1.0 / 60.0
        }
        let frac = total > 1e-9 ? band / total : 0
        let coh = max(0, min(1, (frac - 0.15) / 0.6))
        coherence += 0.35 * (coh - coherence)                 // smooth the ring
        let bpm = max(4.5, min(7.5, bestF * 60))
        suggestedBpm += 0.3 * (bpm - suggestedBpm)
    }

    /// Goertzel power of `x` at `freq` (Hz), given sample rate `fs`.
    static func goertzel(_ x: [Double], fs: Double, freq: Double) -> Double {
        let w = 2 * Double.pi * freq / fs
        let coeff = 2 * cos(w)
        var s1 = 0.0, s2 = 0.0
        for v in x { let s0 = v + coeff * s1 - s2; s2 = s1; s1 = s0 }
        return s1 * s1 + s2 * s2 - coeff * s1 * s2
    }
}
