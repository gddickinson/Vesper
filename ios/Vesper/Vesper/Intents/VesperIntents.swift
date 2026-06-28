//  VesperIntents.swift
//  Vesper — App Intents + App Shortcuts so you can start a session by voice
//  ("Hey Siri, start a session with Vesper"), from Spotlight, the Shortcuts app,
//  or a Shortcuts automation (e.g. at bedtime). Zero setup, fully offline.
//
//  The intent hands a request to the app via UserDefaults; the running app picks
//  it up in `SessionViewModel.applyPendingIntent()` on foreground/launch.

import AppIntents
import Foundation

enum IntentMode: String, AppEnum {
    case meditate, breathwork, relax, sleep

    static var typeDisplayRepresentation: TypeDisplayRepresentation = "Mode"
    static var caseDisplayRepresentations: [IntentMode: DisplayRepresentation] = [
        .meditate: "Meditate",
        .breathwork: "Breathwork",
        .relax: "Relax",
        .sleep: "Sleep",
    ]
}

struct StartVesperSession: AppIntent {
    static var title: LocalizedStringResource = "Start a Session"
    static var description = IntentDescription("Begin a Vesper breathing, relaxation, or sleep session.")
    static var openAppWhenRun: Bool = true

    @Parameter(title: "Mode")
    var mode: IntentMode?

    func perform() async throws -> some IntentResult {
        let d = UserDefaults.standard
        if let mode { d.set(mode.rawValue, forKey: "pendingMode") }
        d.set(true, forKey: "pendingAutoStart")
        return .result()
    }
}

struct VesperShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: StartVesperSession(),
            phrases: [
                "Start a session with \(.applicationName)",
                "Begin \(.applicationName)",
                "Breathe with \(.applicationName)",
                "Start \(.applicationName)",
            ],
            shortTitle: "Start Session",
            systemImageName: "wind"
        )
    }
}
