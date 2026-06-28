//  PatternBuilderSheet.swift
//  Vesper — design your own breath pattern: four phase sliders + a name. Saved
//  to your custom list and selected immediately.

import SwiftUI

struct PatternBuilderSheet: View {
    @ObservedObject var vm: SessionViewModel
    @Environment(\.dismiss) private var dismiss

    @State private var name = "My Pattern"
    @State private var inhale = 4.0
    @State private var holdFull = 0.0
    @State private var exhale = 6.0
    @State private var holdEmpty = 0.0

    private var cycle: Double { inhale + holdFull + exhale + holdEmpty }

    var body: some View {
        NavigationStack {
            Form {
                Section("Name") {
                    TextField("Pattern name", text: $name)
                }
                Section("Phases (seconds)") {
                    phaseRow("Inhale", $inhale)
                    phaseRow("Hold (full)", $holdFull)
                    phaseRow("Exhale", $exhale)
                    phaseRow("Hold (empty)", $holdEmpty)
                }
                Section {
                    Text(cycle >= 1
                         ? String(format: "%g-%g-%g-%g  ·  %.1f breaths/min",
                                  inhale, holdFull, exhale, holdEmpty, 60 / cycle)
                         : "Set at least one second of breathing.")
                        .font(.system(size: 12)).foregroundStyle(.secondary)
                }
                if !CustomPatterns.names.isEmpty {
                    Section("Your patterns") {
                        ForEach(CustomPatterns.names, id: \.self) { n in
                            HStack {
                                Text(n)
                                Spacer()
                                Button(role: .destructive) {
                                    vm.deleteCustomPattern(n)
                                } label: { Image(systemName: "trash") }
                                .buttonStyle(.borderless)
                            }
                        }
                    }
                }
            }
            .navigationTitle("New Pattern")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        let nm = name.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard !nm.isEmpty, cycle >= 1 else { return }
                        vm.saveCustomPattern(name: nm, inhale: inhale, holdFull: holdFull,
                                             exhale: exhale, holdEmpty: holdEmpty)
                        dismiss()
                    }
                    .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty || cycle < 1)
                }
            }
            .tint(Theme.accent)
        }
        .preferredColorScheme(.dark)
    }

    private func phaseRow(_ label: String, _ value: Binding<Double>) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text(label)
                Spacer()
                Text(String(format: "%.1f s", value.wrappedValue)).foregroundStyle(.secondary)
            }
            Slider(value: value, in: 0...12, step: 0.5).tint(Theme.accent)
        }
    }
}
