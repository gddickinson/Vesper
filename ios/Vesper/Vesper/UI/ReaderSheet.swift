//  ReaderSheet.swift
//  Vesper — the bedtime Reader. Pick a short text (a bundled fable or one you
//  paste in) and have it read aloud in the chosen narration voice, sentence by
//  sentence, resuming where you left off. With "Fade to sleep" it slows and
//  softens toward silence — the desktop's read-a-novel-to-sleep feature.

import SwiftUI

struct ReaderSheet: View {
    @ObservedObject var vm: SessionViewModel
    @Environment(\.dismiss) private var dismiss

    @AppStorage("readerSleepFade") private var sleepFade = true
    @AppStorage("readerResume") private var resume = true
    @State private var showAdd = false
    @State private var refresh = 0          // bump to re-read Books.all after edits

    var body: some View {
        NavigationStack {
            Form {
                if vm.reading {
                    Section("Reading now") {
                        Text(vm.readingCaption.isEmpty ? "…" : vm.readingCaption)
                            .font(.system(size: 13)).foregroundStyle(.secondary)
                        Button(role: .destructive) { vm.stopReading() } label: {
                            Label("Stop reading", systemImage: "stop.fill")
                        }
                    }
                }

                Section("Options") {
                    Toggle("Fade to sleep", isOn: $sleepFade)
                    Toggle("Resume where I left off", isOn: $resume)
                    Text(sleepFade
                         ? "Slows and softens the reading over time, so you drift off."
                         : "Reads at a steady, gentle pace.")
                        .font(.system(size: 11)).foregroundStyle(.secondary)
                }

                Section("Texts") {
                    let _ = refresh
                    ForEach(Books.all) { t in
                        Button { startReading(t) } label: { row(t) }
                            .buttonStyle(.plain)
                    }
                    .onDelete(perform: deleteUser)
                    Button { showAdd = true } label: {
                        Label("Paste a text…", systemImage: "plus.circle")
                    }
                    .tint(Theme.accent)
                }
            }
            .navigationTitle("Read aloud")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
            .tint(Theme.accent)
            .sheet(isPresented: $showAdd) {
                AddTextSheet { title, content in
                    Books.add(title: title, content: content)
                    refresh += 1
                }
            }
        }
        .preferredColorScheme(.dark)
    }

    private func row(_ t: ReadText) -> some View {
        let at = Books.resume(t.title)
        let total = Books.sentences(t.content).count
        return HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(t.title).font(.system(size: 14, weight: .medium))
                    .foregroundStyle(Theme.text)
                if resume && at > 0 && at < total {
                    Text("Resume · sentence \(at + 1) of \(total)")
                        .font(.system(size: 11)).foregroundStyle(Theme.accent)
                } else {
                    Text("\(total) sentences")
                        .font(.system(size: 11)).foregroundStyle(.secondary)
                }
            }
            Spacer()
            Image(systemName: "play.circle.fill")
                .font(.system(size: 20)).foregroundStyle(Theme.accent)
        }
        .contentShape(Rectangle())
    }

    private func startReading(_ t: ReadText) {
        let from = resume ? Books.resume(t.title) : 0
        vm.readText(title: t.title, content: t.content, fromIndex: from, sleepFade: sleepFade)
        dismiss()
    }

    private func deleteUser(_ offsets: IndexSet) {
        let all = Books.all
        for i in offsets where i < all.count {
            let t = all[i]
            if !Books.samples.contains(where: { $0.title == t.title }) {
                Books.deleteUser(t.title)
            }
        }
        refresh += 1
    }
}

/// A small paste-a-text form (title + body).
private struct AddTextSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var content = ""
    let onSave: (String, String) -> Void

    var body: some View {
        NavigationStack {
            Form {
                Section("Title") { TextField("e.g. A letter, a chapter…", text: $title) }
                Section("Text") {
                    TextEditor(text: $content).frame(minHeight: 220)
                        .font(.system(size: 14))
                }
            }
            .navigationTitle("Paste a text")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        let nm = title.trimmingCharacters(in: .whitespacesAndNewlines)
                        let body = content.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard !nm.isEmpty, !body.isEmpty else { return }
                        onSave(nm, body)
                        dismiss()
                    }
                    .disabled(title.trimmingCharacters(in: .whitespaces).isEmpty
                              || content.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .tint(Theme.accent)
        }
        .preferredColorScheme(.dark)
    }
}
