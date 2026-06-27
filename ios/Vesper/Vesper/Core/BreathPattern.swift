//  BreathPattern.swift
//  Vesper — breath pattern model + cycle-envelope math.
//
//  A faithful Swift port of breathsim/patterns.py. A pattern is four phase
//  durations (inhale → hold_full → exhale → hold_empty). From a time position
//  inside the cycle we derive `volume` (lung fullness, drives the visual) and
//  `airflow` (|d(volume)/dt|, drives breath-sound loudness — peaks mid-breath,
//  silent during holds), exactly as the desktop app does.

import Foundation

enum BreathPhase: String {
    case inhale, holdFull, exhale, holdEmpty

    /// On-screen label.
    var label: String {
        switch self {
        case .inhale: return "Breathe In"
        case .holdFull, .holdEmpty: return "Hold"
        case .exhale: return "Breathe Out"
        }
    }

    /// Friendlier wording for spoken cues (the empty hold says "Rest").
    var speech: String {
        switch self {
        case .inhale: return "Breathe in"
        case .holdFull: return "Hold"
        case .exhale: return "Breathe out"
        case .holdEmpty: return "Rest"
        }
    }
}

/// Four-phase breathing pattern; durations in seconds.
struct BreathPattern: Identifiable, Hashable {
    let name: String
    let inhale: Double
    let holdFull: Double
    let exhale: Double
    let holdEmpty: Double
    let info: String

    var id: String { name }

    init(_ name: String, _ inhale: Double, _ holdFull: Double,
         _ exhale: Double, _ holdEmpty: Double, _ info: String = "") {
        self.name = name
        self.inhale = inhale
        self.holdFull = holdFull
        self.exhale = exhale
        self.holdEmpty = holdEmpty
        self.info = info
    }

    var cycle: Double { max(0.001, inhale + holdFull + exhale + holdEmpty) }

    var phases: [(BreathPhase, Double)] {
        [(.inhale, inhale), (.holdFull, holdFull),
         (.exhale, exhale), (.holdEmpty, holdEmpty)]
    }

    /// e.g. "4-7-8-0"
    var summary: String {
        phases.map { String(format: "%g", $0.1) }.joined(separator: "-")
    }

    /// Breaths per minute for the equal-ish patterns (display only).
    var breathsPerMinute: Double { 60.0 / cycle }
}

/// Snapshot of the breath cycle at one instant.
struct BreathState {
    var phase: BreathPhase = .inhale
    var progress: Double = 0      // 0..1 within the current phase
    var remaining: Double = 0     // seconds left in the current phase
    var volume: Double = 0        // lung fullness 0..1 (visual size)
    var airflow: Double = 0       // 0..1 turbulent-airflow loudness
    var cycleIndex: Int = 0       // completed cycles
    var cycleFrac: Double = 0     // 0..1 position through the whole cycle
    var label: String = "Breathe In"
}

enum BreathMath {
    /// Smooth 0 → 1 ramp (raised cosine).
    @inline(__always) static func raisedCos(_ p: Double) -> Double {
        0.5 - 0.5 * cos(.pi * p)
    }

    @inline(__always) static func volume(_ phase: BreathPhase, _ p: Double) -> Double {
        switch phase {
        case .inhale: return raisedCos(p)
        case .holdFull: return 1.0
        case .exhale: return raisedCos(1.0 - p)
        case .holdEmpty: return 0.0
        }
    }

    /// |d/dt| of a raised-cosine volume is a sine bump: 0 at the turn-arounds,
    /// peak mid-phase. Holds have no airflow → silence.
    @inline(__always) static func airflow(_ phase: BreathPhase, _ p: Double) -> Double {
        switch phase {
        case .inhale, .exhale: return sin(.pi * p)
        default: return 0.0
        }
    }

    /// The breath state of `pattern` at time `t` seconds (port of `state_at`).
    static func state(_ pattern: BreathPattern, at t: Double) -> BreathState {
        let cycle = pattern.cycle
        let tt = max(0.0, t)
        let cycleIndex = Int(tt / cycle)
        let pos = tt - Double(cycleIndex) * cycle

        var acc = 0.0
        var chosen: (BreathPhase, Double, Double)? = nil
        var lastNonzero: (BreathPhase, Double, Double)? = nil
        for (phase, dur) in pattern.phases {
            if dur <= 0 { continue }
            lastNonzero = (phase, dur, acc)
            if pos < acc + dur { chosen = (phase, dur, acc); break }
            acc += dur
        }
        let pick = chosen ?? lastNonzero ?? (.inhale, cycle, 0.0)
        let (phase, dur, start) = pick
        var p = dur > 0 ? (pos - start) / dur : 0.0
        p = min(max(p, 0.0), 1.0)

        return BreathState(
            phase: phase,
            progress: p,
            remaining: dur * (1.0 - p),
            volume: volume(phase, p),
            airflow: airflow(phase, p),
            cycleIndex: cycleIndex,
            cycleFrac: min(1.0, max(0.0, pos / cycle)),
            label: phase.label
        )
    }
}
