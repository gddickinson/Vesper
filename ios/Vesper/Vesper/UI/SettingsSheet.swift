//  SettingsSheet.swift
//  Vesper — cross-cutting preferences that don't belong to a single mode:
//  guidance cues, reflection, and re-opening the welcome.

import SwiftUI

struct SettingsSheet: View {
    @ObservedObject var vm: SessionViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Toggle("Haptic breathing cues", isOn: $vm.haptics)
                    Toggle("Settle-in countdown", isOn: $vm.settleIn)
                } header: {
                    Text("Guidance")
                } footer: {
                    Text("A gentle tap on each breath phase, and a short \u{201C}breathe with me\u{201D} lead-in when a session begins (Meditate, Breathwork, Relax).")
                }

                Section {
                    Toggle("Mood check-ins", isOn: $vm.moodEnabled)
                } header: {
                    Text("Reflection")
                } footer: {
                    Text("A one-tap check after a session, tracked in your practice stats so you can see how sitting changes how you feel.")
                }

                Section {
                    Toggle("Daily reminder", isOn: $vm.reminderOn)
                    if vm.reminderOn {
                        DatePicker("Time", selection: $vm.reminderTime,
                                   displayedComponents: .hourAndMinute)
                    }
                } header: {
                    Text("Reminders")
                } footer: {
                    Text("A gentle nudge to take a moment each day. Manage notification permission anytime in iOS Settings.")
                }

                if HealthStore.isSupported {
                    Section {
                        Toggle("Sync to Apple Health", isOn: $vm.syncHealth)
                    } header: {
                        Text("Health")
                    } footer: {
                        Text("Logs Mindful Minutes when a session ends (and, on iOS 18, your post-session mood as a State of Mind). You'll be asked to allow this the first time.")
                    }
                }

                Section {
                    Picker("Background scene", selection: $vm.backdrop) {
                        ForEach(SessionViewModel.sceneNames, id: \.self) { Text($0).tag($0) }
                    }
                } header: {
                    Text("Appearance")
                } footer: {
                    Text("\u{201C}Auto\u{201D} picks a scene to match the mode (a night sky for Sleep, aurora for Relax).")
                }

                Section("About") {
                    Button("Show welcome screen") { vm.showWelcomeAgain(); dismiss() }
                    HStack {
                        Text("Vesper").foregroundStyle(.secondary)
                        Spacer()
                        Text("breathe · rest · drift off").foregroundStyle(.secondary)
                    }
                    .font(.system(size: 12))
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
            .tint(Theme.accent)
        }
        .preferredColorScheme(.dark)
    }
}
