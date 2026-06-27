//  BreathClock.swift
//  Vesper — the single breath-time authority.
//
//  Mirrors breathsim/controller.py: a pausable, monotonic session clock. BOTH
//  the audio render thread and the SwiftUI animation read `now()` from this one
//  clock, so sound and visuals stay in lock-step (the desktop app's rule: one
//  clock, never two). Reads are lock-free (a couple of Double loads) and so are
//  safe to call from the real-time audio callback.

import Foundation
import QuartzCore

final class BreathClock {
    /// Total elapsed seconds the clock had accrued before the current run began.
    private var accumulated: Double = 0
    /// Host time (seconds) at which the current run started; nil while paused.
    private var runStart: Double?

    private var pattern: BreathPattern

    init(pattern: BreathPattern) {
        self.pattern = pattern
    }

    /// Monotonic host time in seconds.
    @inline(__always) private func host() -> Double { CACurrentMediaTime() }

    var isRunning: Bool { runStart != nil }

    func start() {
        if runStart == nil { runStart = host() }
    }

    func pause() {
        if let s = runStart {
            accumulated += host() - s
            runStart = nil
        }
    }

    func toggle() { isRunning ? pause() : start() }

    /// Restart the session from zero (keeps running state).
    func reset() {
        accumulated = 0
        runStart = isRunning ? host() : nil
    }

    /// Elapsed breath-time in seconds (advances only while running).
    @inline(__always) func now() -> Double {
        if let s = runStart { return accumulated + (host() - s) }
        return accumulated
    }

    func setPattern(_ p: BreathPattern) { pattern = p }
    var currentPattern: BreathPattern { pattern }

    /// The breath state at the current instant.
    func state() -> BreathState { BreathMath.state(pattern, at: now()) }

    /// The breath state at an explicit time (used by the audio block).
    func state(at t: Double) -> BreathState { BreathMath.state(pattern, at: t) }
}
