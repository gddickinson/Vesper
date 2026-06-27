//  Patterns.swift
//  Vesper — the preset breath-pattern library (port of patterns.PRESETS).
//
//  Add a pattern → append a BreathPattern here. Nothing else needs to change.

import Foundation

enum Patterns {
    static let all: [BreathPattern] = [
        BreathPattern("Coherent 5.5 (Resonance)", 5.5, 0, 5.5, 0,
            "Equal 5.5s in/out (~5.5 breaths/min). Calms the nervous system; the classic resonance-frequency pace."),
        BreathPattern("Box Breathing 4-4-4-4", 4, 4, 4, 4,
            "Equal inhale, hold, exhale, hold. Focus and calm; used by Navy SEALs and clinicians."),
        BreathPattern("4-7-8 Relaxing", 4, 7, 8, 0,
            "Dr Weil's relaxing breath. A long exhale soothes; great for winding down and sleep."),
        BreathPattern("Calming 4-6 (Long Exhale)", 4, 0, 6, 0,
            "Exhale longer than inhale to engage the parasympathetic 'rest and digest' response."),
        BreathPattern("Equal 4-4 (Sama Vritti)", 4, 0, 4, 0,
            "Even inhale and exhale. Simple, steadying, good for beginners."),
        BreathPattern("Deep Box 6-6-6-6", 6, 6, 6, 6,
            "Slower square breathing for deeper relaxation and breath control."),
        BreathPattern("Triangle 4-4-4", 4, 4, 4, 0,
            "Inhale, hold, exhale in equal counts. A gentle step up from equal breathing."),
        BreathPattern("Ujjayi Slow 6-6", 6, 0, 6, 0,
            "Slow ocean-breath pace for yoga and meditation."),
        BreathPattern("Calm 4.5-6.5", 4.5, 0, 6.5, 0,
            "A gentle longer-exhale pace that sits close to resonance breathing."),
        BreathPattern("Quick Calm 3-5", 3, 0, 5, 0,
            "A faster cycle with a longer exhale for on-the-spot calming."),
        BreathPattern("Extended 7-11", 7, 0, 11, 0,
            "Very slow 7-in / 11-out. Deeply relaxing once you are warm."),
        BreathPattern("Sigh Release 2-7", 2, 0, 7, 0,
            "A short inhale and a long sighing exhale to release tension."),
        BreathPattern("Physiological Sigh", 2.5, 1, 6, 0,
            "The fastest known calmer: a full inhale, a brief top-up catch, then a long slow exhale."),
        BreathPattern("Energising 6-2", 6, 0, 2, 0,
            "A long inhale and a quick exhale to feel alert and awake."),
        BreathPattern("Tummo (Vase) 5-6-6", 5, 6, 6, 0,
            "A deep inhale, a held vase breath, and a long exhale for inner-fire practice."),
        BreathPattern("Sitali (Cooling) 5-1-6", 5, 1, 6, 0,
            "A slow cooling inhale and a soft exhale."),
    ]

    static let `default` = all[0]

    static func byName(_ name: String) -> BreathPattern? {
        all.first { $0.name == name }
    }
}
