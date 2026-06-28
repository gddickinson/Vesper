//  GenerativeContent.swift
//  Vesper — optional on-device generated bedtime content via Apple's Foundation
//  Models framework (iOS 26+, Apple Intelligence). Everything model-specific is
//  doubly guarded (`#if canImport(FoundationModels)` + `if #available(iOS 26)`),
//  so this compiles on the iOS 17 deployment target and, on any device/simulator
//  without the on-device model, simply returns nil — the caller then falls back
//  to a written story. Fully offline, private, no backend. See
//  [[vesper-ios-feature-roadmap]].

import Foundation
#if canImport(FoundationModels)
import FoundationModels
#endif

enum GenerativeContent {
    /// A few calming, plotless themes to seed a fresh story each time.
    static let themes: [String] = [
        "a quiet snowfall over a sleeping village",
        "a warm tide drawing back from the sand at dusk",
        "drifting clouds crossing a slow moon",
        "a candlelit room where soft rain taps the window",
        "a still forest pond under starlight",
        "a gentle river winding through summer meadows",
        "paper lanterns floating down a calm canal",
        "a warm wind moving slowly through tall grass",
    ]

    /// True only when the on-device model is present and ready right now.
    static var isAvailable: Bool {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            if case .available = SystemLanguageModel.default.availability { return true }
        }
        #endif
        return false
    }

    /// Ask the on-device model for ~8 short, soothing, plotless bedtime sentences
    /// about `theme`. Returns nil if the model is unavailable or anything fails.
    static func generateBedtime(theme: String) async -> [String]? {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            guard case .available = SystemLanguageModel.default.availability else { return nil }
            do {
                let instructions = """
                You are a gentle bedtime narrator. Write in calm, simple, present-tense prose. \
                There is no plot, no conflict, and no danger — only soft, sensory, drifting images \
                that help a tired listener fall asleep. Keep sentences short and soothing.
                """
                let session = LanguageModelSession(instructions: instructions)
                let prompt = "Write eight short, soothing bedtime sentences about \(theme). " +
                             "Plain text, one gentle image per sentence, no numbering or headings."
                let response = try await session.respond(to: prompt)
                let lines = Books.sentences(response.content)
                return lines.isEmpty ? nil : lines
            } catch {
                return nil
            }
        }
        #endif
        return nil
    }
}
