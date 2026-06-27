//  RootView.swift
//  Vesper — the main screen: a mode bar, the breathing orb, and a compact set
//  of controls. The mode bar is the primary navigation, exactly as on desktop.

import SwiftUI

struct RootView: View {
    @StateObject private var vm = SessionViewModel()
    @StateObject private var neural = KokoroDownloader()
    @State private var showStats = false

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            VStack(spacing: 14) {
                header
                modeBar
                orbArea
                ScrollView { controls.padding(.horizontal, 16) }
                transport
            }
            .padding(.vertical, 10)
        }
        .preferredColorScheme(.dark)
        .tint(Theme.accent)
        .overlay(alignment: .topTrailing) {
            Button { showStats = true } label: {
                Image(systemName: "chart.bar.fill")
                    .font(.system(size: 15)).foregroundStyle(Theme.muted)
                    .padding(14)
            }
            .accessibilityLabel("Practice stats")
        }
        .sheet(isPresented: $showStats) { StatsView() }
    }

    private var header: some View {
        VStack(spacing: 2) {
            Text("Vesper").font(.system(size: 22, weight: .semibold, design: .rounded))
                .foregroundStyle(Theme.text)
            Text("breathe · rest · drift off").font(.system(size: 11, weight: .regular))
                .foregroundStyle(Theme.faint)
        }
    }

    private var modeBar: some View {
        HStack(spacing: 8) {
            ForEach(Mode.allCases) { m in
                Button { vm.mode = m } label: {
                    VStack(spacing: 4) {
                        Image(systemName: m.symbol).font(.system(size: 17))
                        Text(m.title).font(.system(size: 11, weight: .medium))
                    }
                    .frame(maxWidth: .infinity).padding(.vertical, 9)
                    .background(vm.mode == m ? Theme.bgCard : Color.clear)
                    .overlay(RoundedRectangle(cornerRadius: 12)
                        .stroke(vm.mode == m ? Theme.accent.opacity(0.6) : Theme.border, lineWidth: 1))
                    .foregroundStyle(vm.mode == m ? Theme.accent : Theme.muted)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
            }
        }
        .padding(.horizontal, 12)
    }

    private var showsCompanion: Bool { vm.mode == .sleep && vm.companionName != "Orb" }

    private var orbArea: some View {
        ZStack {
            if showsCompanion {
                CharacterView(character: vm.companionName, state: vm.breath,
                              animT: vm.animT, mouth: vm.mouth)
            } else {
                OrbView(state: vm.breath, progress: vm.progress, animT: vm.animT)
                VStack(spacing: 6) {
                    Text(vm.breath.label.uppercased())
                        .font(.system(size: 15, weight: .semibold)).tracking(3)
                        .foregroundStyle(Theme.text.opacity(0.9))
                    if vm.running {
                        Text(String(format: "%.0f", vm.breath.remaining.rounded(.up)))
                            .font(.system(size: 30, weight: .light, design: .rounded))
                            .foregroundStyle(Theme.text.opacity(0.55))
                    }
                }
            }
            if !vm.caption.isEmpty {
                VStack {
                    Spacer()
                    Text(vm.caption)
                        .font(.system(size: 14, weight: .regular))
                        .multilineTextAlignment(.center)
                        .foregroundStyle(Theme.text.opacity(0.85))
                        .padding(.horizontal, 24).padding(.bottom, 6)
                        .shadow(color: .black.opacity(0.6), radius: 4)
                }
            }
        }
        .frame(maxWidth: .infinity).frame(height: 300)
    }

    @ViewBuilder private var controls: some View {
        VStack(spacing: 12) {
            card {
                pickerRow("Pattern", selection: $vm.patternName,
                          options: Patterns.all.map(\.name))
                Text(vm.pattern.info).font(.system(size: 11)).foregroundStyle(Theme.faint)
                    .fixedSize(horizontal: false, vertical: true)
                Text("\(vm.pattern.summary)  ·  \(String(format: "%.1f", vm.pattern.breathsPerMinute)) breaths/min")
                    .font(.system(size: 11, weight: .medium)).foregroundStyle(Theme.muted)
            }
            card {
                pickerRow("Breath sound", selection: $vm.voiceName,
                          options: BreathVoice.all.map(\.name))
                slider("Breathing", value: $vm.breathLevel)
                slider("Volume", value: $vm.masterVolume)
            }
            card {
                pickerRow("Nature sound", selection: $vm.ambienceName,
                          options: AmbienceVoice.all.map(\.name))
                slider("Ambience", value: $vm.ambienceLevel)
            }
            if vm.mode.narrates {
                card {
                    pickerRow("Companion", selection: $vm.companionName,
                              options: ["Orb"] + Characters.names)
                    pickerRow("Branch", selection: $vm.lectureBranch,
                              options: Lectures.branches)
                    pickerRow("Lecture", selection: $vm.lectureTitle,
                              options: vm.lecturesInBranch.map(\.title))
                    HStack {
                        Button { vm.surpriseLecture() } label: {
                            Label("Surprise me", systemImage: "sparkles")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundStyle(Theme.accent)
                        }
                        Spacer()
                        Text("\(Lectures.all.count) lectures")
                            .font(.system(size: 11)).foregroundStyle(Theme.faint)
                    }
                    Toggle("Narrate", isOn: $vm.narrate)
                        .font(.system(size: 13)).foregroundStyle(Theme.text)
                        .tint(Theme.accent)
                    HStack {
                        Text("Voice").font(.system(size: 13)).foregroundStyle(Theme.text)
                        Spacer()
                        Picker("Voice", selection: $vm.narrationVoiceID) {
                            ForEach(vm.narrationVoices, id: \.id) { Text($0.label).tag($0.id) }
                        }
                        .pickerStyle(.menu).tint(Theme.accent)
                        .frame(maxWidth: 210, alignment: .trailing)
                    }
                    HStack {
                        Button { vm.previewVoice() } label: {
                            Label("Preview", systemImage: "speaker.wave.2.fill")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundStyle(Theme.accent)
                        }
                        Spacer()
                        Button { vm.enablePersonalVoice() } label: {
                            Label("Use my voice", systemImage: "person.wave.2.fill")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundStyle(Theme.accent)
                        }
                    }
                    if vm.personalVoiceAuthorized {
                        Text("Personal Voice enabled — pick it in the Voice list above.")
                            .font(.system(size: 10)).foregroundStyle(Theme.accent)
                    }
                    Text("Tip: for far more natural narration, download an Enhanced or Premium English voice in Settings ▸ Accessibility ▸ Spoken Content ▸ Voices. \"Use my voice\" needs a Personal Voice set up in Settings ▸ Accessibility ▸ Personal Voice (iOS 17+).")
                        .font(.system(size: 10)).foregroundStyle(Theme.faint)
                        .fixedSize(horizontal: false, vertical: true)
                }
                neuralCard
            }
            card {
                HStack {
                    Text("Auto-stop").font(.system(size: 13)).foregroundStyle(Theme.text)
                    Spacer()
                    Picker("", selection: $vm.sessionMinutes) {
                        Text("Off").tag(0.0)
                        ForEach([5.0, 10, 15, 20, 30, 45, 60], id: \.self) { mm in
                            Text("\(Int(mm)) min").tag(mm)
                        }
                    }.tint(Theme.accent)
                }
            }
            if !vm.audioAvailable {
                Text("Audio is unavailable on this device — visuals only.")
                    .font(.system(size: 11)).foregroundStyle(Theme.accentWarm)
            }
        }
        .padding(.bottom, 8)
    }

    private var transport: some View {
        HStack(spacing: 26) {
            Button { vm.reset() } label: {
                Image(systemName: "arrow.counterclockwise")
                    .font(.system(size: 18)).foregroundStyle(Theme.muted)
                    .frame(width: 50, height: 50)
                    .overlay(Circle().stroke(Theme.border, lineWidth: 1))
            }
            Button { vm.togglePlay() } label: {
                Image(systemName: vm.running ? "pause.fill" : "play.fill")
                    .font(.system(size: 26)).foregroundStyle(Theme.bg)
                    .frame(width: 76, height: 76)
                    .background(Circle().fill(Theme.accent))
                    .shadow(color: Theme.accent.opacity(0.4), radius: 12)
            }
            Spacer().frame(width: 50)
        }
        .padding(.bottom, 6)
    }

    @ViewBuilder private var neuralCard: some View {
        card {
            HStack(spacing: 6) {
                Text("Neural voices").font(.system(size: 13, weight: .medium))
                    .foregroundStyle(Theme.text)
                Text("BETA").font(.system(size: 8, weight: .bold)).foregroundStyle(Theme.bg)
                    .padding(.horizontal, 5).padding(.vertical, 2)
                    .background(Theme.accentWarm).clipShape(Capsule())
                Spacer()
            }
            Text("Kokoro — the most natural, fully-offline narration (the same neural voices as the desktop app).")
                .font(.system(size: 11)).foregroundStyle(Theme.faint)
                .fixedSize(horizontal: false, vertical: true)
            switch neural.state {
            case .idle:
                Button { neural.start() } label: {
                    Label("Download voice model (~110 MB)", systemImage: "arrow.down.circle")
                        .font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.accent)
                }
            case .downloading:
                ProgressView(value: neural.progress).tint(Theme.accent)
                Text("Downloading… \(Int(neural.progress * 100))%")
                    .font(.system(size: 10)).foregroundStyle(Theme.muted)
            case .ready:
                Text(NeuralTTS.backend == nil
                     ? "Model ready ✓ — neural voices switch on once the voice engine is enabled (see docs/KOKORO_IOS.md)."
                     : "Neural voices ready ✓ — pick one in the Voice list.")
                    .font(.system(size: 10)).foregroundStyle(Theme.accent)
                Button { neural.deleteModel() } label: {
                    Text("Delete model").font(.system(size: 11)).foregroundStyle(Theme.muted)
                }
            case .failed(let msg):
                Text("Download failed: \(msg)")
                    .font(.system(size: 10)).foregroundStyle(Theme.accentWarm)
                Button { neural.start() } label: {
                    Text("Retry").font(.system(size: 11)).foregroundStyle(Theme.accent)
                }
            }
        }
    }

    // MARK: small building blocks

    @ViewBuilder private func card<Content: View>(@ViewBuilder _ c: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 10) { c() }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.bgCard)
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Theme.border, lineWidth: 1))
            .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private func pickerRow(_ title: String, selection: Binding<String>,
                           options: [String]) -> some View {
        HStack {
            Text(title).font(.system(size: 13)).foregroundStyle(Theme.text)
            Spacer()
            Picker(title, selection: selection) {
                ForEach(options, id: \.self) { Text($0).tag($0) }
            }
            .pickerStyle(.menu).tint(Theme.accent)
            .frame(maxWidth: 200, alignment: .trailing)
        }
    }

    private func slider(_ title: String, value: Binding<Double>) -> some View {
        HStack {
            Text(title).font(.system(size: 12)).foregroundStyle(Theme.muted)
                .frame(width: 78, alignment: .leading)
            Slider(value: value, in: 0...1).tint(Theme.accent)
        }
    }
}

#Preview { RootView() }
