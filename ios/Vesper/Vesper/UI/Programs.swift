//  Programs.swift
//  Vesper — guided multi-stage breathing programs (the iOS port of programs.py).
//  A program steps through stages on the breath clock, changing the pace and
//  speaking a short instruction at each step. Pure data; the runner lives in
//  SessionViewModel.

import Foundation

struct ProgramStage {
    let minutes: Double
    let say: String
    let pattern: String   // a Patterns.byName key
}

struct GuidedProgram: Identifiable {
    let name: String
    let summary: String
    let stages: [ProgramStage]
    var id: String { name }
    var totalMinutes: Int { Int(stages.reduce(0) { $0 + $1.minutes }.rounded()) }
}

enum Programs {
    static let none = "None"
    static var names: [String] { [none] + all.map(\.name) }
    static func byName(_ n: String) -> GuidedProgram? { all.first { $0.name == n } }

    static let all: [GuidedProgram] = [
        GuidedProgram(name: "Calm & Unwind", summary: "Ease from steady breathing into a resonant calm.", stages: [
            ProgramStage(minutes: 2, say: "Let's begin. Breathe naturally, and let your shoulders soften.", pattern: "Equal 4-4 (Sama Vritti)"),
            ProgramStage(minutes: 4, say: "Now lengthen the exhale. Breathe in for four, and out for six.", pattern: "Calming 4-6 (Long Exhale)"),
            ProgramStage(minutes: 4, say: "Settle into a resonant pace. Five and a half in, five and a half out.", pattern: "Coherent 5.5 (Resonance)"),
        ]),
        GuidedProgram(name: "Energize", summary: "Wake the body with a longer inhale, then settle.", stages: [
            ProgramStage(minutes: 1, say: "We'll wake the body up. Start with an even, steady breath.", pattern: "Equal 4-4 (Sama Vritti)"),
            ProgramStage(minutes: 3, say: "Now a long inhale and a quick release. Draw energy in.", pattern: "Energising 6-2"),
            ProgramStage(minutes: 2, say: "Return to a calm, even breath. Feel alert and clear.", pattern: "Equal 4-4 (Sama Vritti)"),
        ]),
        GuidedProgram(name: "4-7-8 Wind-Down", summary: "Settle, then Dr Weil's relaxing breath.", stages: [
            ProgramStage(minutes: 2, say: "Settle in. Breathe gently, and let the day go.", pattern: "Calming 4-6 (Long Exhale)"),
            ProgramStage(minutes: 4, say: "Now the relaxing breath. In for four, hold for seven, out for eight.", pattern: "4-7-8 Relaxing"),
        ]),
        GuidedProgram(name: "Box Breathing", summary: "Steady focus with an even, square breath.", stages: [
            ProgramStage(minutes: 1, say: "We'll breathe in a square. Begin with an easy, even breath.", pattern: "Equal 4-4 (Sama Vritti)"),
            ProgramStage(minutes: 4, say: "Now box breathing. In, hold, out, hold — each for four counts.", pattern: "Box Breathing 4-4-4-4"),
        ]),
        GuidedProgram(name: "Physiological Sigh", summary: "A quick three-minute reset.", stages: [
            ProgramStage(minutes: 3, say: "A quick reset. Two breaths in through the nose, then a long sigh out.", pattern: "Physiological Sigh"),
        ]),
    ]
}
