//  Haptics.swift
//  Vesper — gentle breath-phase haptics.
//
//  An iOS-native guidance cue the desktop can't do: a soft tap as each phase
//  begins, so you can follow the breath with your eyes closed. Used in
//  Meditate / Breathwork; stays silent in Sleep (a buzz would disrupt drifting
//  off). No-op on a device without a Taptic Engine (and on the Simulator).

import UIKit

enum Haptics {
    private static let soft = UIImpactFeedbackGenerator(style: .soft)
    private static let light = UIImpactFeedbackGenerator(style: .light)

    /// Warm the Taptic Engine so the next tap fires without latency.
    static func prepare() { soft.prepare(); light.prepare() }

    /// A gentle tap marking the start of a breath phase.
    static func phase(_ phase: BreathPhase) {
        switch phase {
        case .inhale: soft.impactOccurred(intensity: 0.9)   // the rise: a fuller tap
        case .exhale: soft.impactOccurred(intensity: 0.6)   // the fall: softer
        case .holdFull, .holdEmpty: light.impactOccurred(intensity: 0.4)  // a hush
        }
        prepare()
    }

    /// A soft two-tap marking a completed timed session.
    static func done() {
        soft.impactOccurred(intensity: 0.7)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.18) {
            soft.impactOccurred(intensity: 0.5)
        }
    }
}
