//  VoicePickerSheet.swift
//  Vesper — the narration-voice chooser.
//
//  A full, scrollable, sectioned list so every voice is always reachable: the
//  device / Personal / premium voices in one group, the offline Kokoro neural
//  voices in another. Tapping a row selects it AND previews it (like the iOS
//  Settings voice picker), so you can audition before committing. This replaces
//  the old single `.menu` Picker, which opened scrolled to the selected item and
//  could hide the other voices above it.

import SwiftUI

struct VoicePickerSheet: View {
    @ObservedObject var vm: SessionViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section {
                    ForEach(vm.systemVoiceMenu, id: \.id) { row($0) }
                } header: {
                    Text("Device & premium voices")
                } footer: {
                    Text("Add Enhanced/Premium English voices in Settings ▸ Accessibility ▸ Spoken Content ▸ Voices, and your Personal Voice in Settings ▸ Accessibility ▸ Personal Voice.")
                }

                if !vm.neuralVoiceMenu.isEmpty {
                    Section {
                        ForEach(vm.neuralVoiceMenu, id: \.id) { row($0) }
                    } header: {
                        Text("Neural voices · offline")
                    } footer: {
                        Text("Kokoro — the most natural narration, generated on-device.")
                    }
                }
            }
            .navigationTitle("Narration voice")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { vm.previewVoice() } label: {
                        Label("Preview", systemImage: "speaker.wave.2.fill")
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
        .preferredColorScheme(.dark)
        .tint(Theme.accent)
    }

    @ViewBuilder private func row(_ v: (id: String, label: String)) -> some View {
        Button {
            vm.narrationVoiceID = v.id
            vm.previewVoice()
        } label: {
            HStack {
                Text(v.label)
                    .foregroundStyle(.primary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                if vm.narrationVoiceID == v.id {
                    Image(systemName: "checkmark")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(Theme.accent)
                }
            }
            .contentShape(Rectangle())
        }
    }
}
