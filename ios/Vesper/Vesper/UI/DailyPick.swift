//  DailyPick.swift
//  Vesper — a gentle "Today" suggestion that rotates each day, so there's always
//  one calm thing to try without deciding. Deterministic from the date (no
//  randomness, no network), so it's the same all day and changes at midnight.

import Foundation

struct DailyPick {
    let title: String
    let subtitle: String
    let mode: Mode
    let pattern: String

    static let all: [DailyPick] = [
        DailyPick(title: "Coherent breathing", subtitle: "Five and a half in, five and a half out.",
                  mode: .meditate, pattern: "Coherent 5.5 (Resonance)"),
        DailyPick(title: "Box breathing", subtitle: "Square the breath: in, hold, out, hold.",
                  mode: .breathwork, pattern: "Box Breathing 4-4-4-4"),
        DailyPick(title: "A long, slow exhale", subtitle: "Let the out-breath lead.",
                  mode: .relax, pattern: "Calming 4-6 (Long Exhale)"),
        DailyPick(title: "4-7-8 for sleep", subtitle: "Popularised by Dr Andrew Weil.",
                  mode: .sleep, pattern: "4-7-8 Relaxing"),
        DailyPick(title: "The physiological sigh", subtitle: "A quick pause and reset.",
                  mode: .breathwork, pattern: "Physiological Sigh"),
        DailyPick(title: "Equal breathing", subtitle: "Even in, even out — steadying.",
                  mode: .meditate, pattern: "Equal 4-4 (Sama Vritti)"),
        DailyPick(title: "Extended exhale", subtitle: "Seven in, eleven out.",
                  mode: .relax, pattern: "Extended 7-11"),
        DailyPick(title: "Ujjayi ocean breath", subtitle: "Slow, oceanic, steadying.",
                  mode: .meditate, pattern: "Ujjayi Slow 6-6"),
    ]

    /// The same pick all day; rotates at local midnight.
    static var today: DailyPick {
        let day = Calendar.current.ordinality(of: .day, in: .year, for: Date()) ?? 1
        return all[(day - 1) % all.count]
    }
}
