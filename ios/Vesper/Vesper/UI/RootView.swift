//  RootView.swift
//  Vesper — the main screen: a mode bar, the breathing orb, and a compact set
//  of controls. The mode bar is the primary navigation, exactly as on desktop.

import SwiftUI

struct RootView: View {
    @StateObject private var vm = SessionViewModel()
    @StateObject private var neural = KokoroDownloader()
    @Environment(\.scenePhase) private var scenePhase
    @State private var showStats = false
    @State private var showVoicePicker = false
    @State private var showSettings = false
    @State private var showPatternBuilder = false
    @State private var showReader = false
    @State private var showDiary = false
    @AppStorage("cbtiWakeMinutes") private var wakeMinutes = 390   // 6:30 AM
    @AppStorage("windDownReminder") private var windDownOn = false

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

            // Sleep wind-down: the whole screen eases darker as you drift off.
            Color.black.opacity(vm.dimLevel)
                .ignoresSafeArea()
                .allowsHitTesting(false)
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
        .overlay(alignment: .topLeading) {
            Button { showSettings = true } label: {
                Image(systemName: "gearshape.fill")
                    .font(.system(size: 15)).foregroundStyle(Theme.muted)
                    .padding(14)
            }
            .accessibilityLabel("Settings")
        }
        .sheet(isPresented: $showStats) { StatsView() }
        .sheet(isPresented: $showVoicePicker) { VoicePickerSheet(vm: vm) }
        .sheet(isPresented: $showSettings) { SettingsSheet(vm: vm) }
        .sheet(isPresented: $showPatternBuilder) { PatternBuilderSheet(vm: vm) }
        .sheet(isPresented: $showReader) { ReaderSheet(vm: vm) }
        .sheet(isPresented: $showDiary) { SleepDiarySheet() }
        .sheet(isPresented: $vm.askMood) { MoodSheet(vm: vm) }
        .fullScreenCover(isPresented: $vm.showOnboarding) { OnboardingView(vm: vm) }
        .onAppear { vm.applyPendingIntent(); MotionManager.shared.start() }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active { vm.applyPendingIntent() }
        }
    }

    private var header: some View {
        VStack(spacing: 3) {
            Text("Vesper").font(.system(size: 22, weight: .semibold, design: .rounded))
                .foregroundStyle(Theme.text)
            Text("breathe · rest · drift off").font(.system(size: 11, weight: .regular))
                .foregroundStyle(Theme.faint)
            if PracticeLog.streak >= 1 {
                Text("🔥 \(PracticeLog.streak)-day streak")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(Theme.accentWarm)
            }
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
            BackdropView(kind: vm.resolvedBackdrop)
            if showsCompanion {
                CharacterView(character: vm.companionName, state: vm.breath,
                              animT: vm.animT, mouth: vm.mouth, drowsy: vm.companionDrowsy)
            } else {
                OrbView(state: vm.breath, progress: vm.progress, animT: vm.animT)
                VStack(spacing: 6) {
                    if vm.leadIn > 0 {
                        Text("BREATHE WITH ME")
                            .font(.system(size: 13, weight: .semibold)).tracking(3)
                            .foregroundStyle(Theme.text.opacity(0.8))
                        Text("\(Int(ceil(vm.leadIn)))")
                            .font(.system(size: 40, weight: .thin, design: .rounded))
                            .foregroundStyle(Theme.accent)
                    } else {
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
            Button { vm.applyDailyPick() } label: {
                HStack(spacing: 10) {
                    Image(systemName: "sparkles").font(.system(size: 16))
                        .foregroundStyle(Theme.accentWarm)
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Today · \(DailyPick.today.title)")
                            .font(.system(size: 13, weight: .medium)).foregroundStyle(Theme.text)
                        Text(DailyPick.today.subtitle)
                            .font(.system(size: 11)).foregroundStyle(Theme.faint)
                    }
                    Spacer()
                    Image(systemName: "chevron.right").font(.system(size: 11)).foregroundStyle(Theme.muted)
                }
                .padding(14)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Theme.bgCard)
                .overlay(RoundedRectangle(cornerRadius: 14)
                    .stroke(Theme.accentWarm.opacity(0.4), lineWidth: 1))
                .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .buttonStyle(.plain)
            card {
                pickerRow("Pattern", selection: $vm.patternName, options: vm.allPatternNames)
                Text(vm.pattern.info).font(.system(size: 11)).foregroundStyle(Theme.faint)
                    .fixedSize(horizontal: false, vertical: true)
                HStack {
                    Text("\(vm.pattern.summary)  ·  \(String(format: "%.1f", vm.pattern.breathsPerMinute)) breaths/min")
                        .font(.system(size: 11, weight: .medium)).foregroundStyle(Theme.muted)
                    Spacer()
                    Button { showPatternBuilder = true } label: {
                        Label("New", systemImage: "plus.circle")
                            .font(.system(size: 11, weight: .medium)).foregroundStyle(Theme.accent)
                    }
                }
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
            if vm.mode == .meditate {
                card {
                    HStack {
                        Text("Interval bell").font(.system(size: 13)).foregroundStyle(Theme.text)
                        Spacer()
                        Picker("", selection: $vm.bellMinutes) {
                            Text("Off").tag(0.0)
                            ForEach([1.0, 2, 3, 5, 10], id: \.self) { m in
                                Text("\(Int(m)) min").tag(m)
                            }
                        }.tint(Theme.accent)
                    }
                    Text("A soft bell at a steady interval to gently mark the time.")
                        .font(.system(size: 11)).foregroundStyle(Theme.faint)
                }
                card {
                    HStack {
                        Text("Paced breathing").font(.system(size: 13)).foregroundStyle(Theme.text)
                        Spacer()
                        Toggle("", isOn: Binding(get: { vm.pacedBpm > 0 },
                                                 set: { vm.pacedBpm = $0 ? 5.5 : 0 }))
                            .labelsHidden().tint(Theme.accent)
                    }
                    if vm.pacedBpm > 0 {
                        Text(String(format: "%.1f breaths/min", vm.pacedBpm))
                            .font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.accent)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        Slider(value: $vm.pacedBpm, in: 4.0...8.0, step: 0.5).tint(Theme.accent)
                        Text("Resonance breathing — equal in and out. ~6/min is the HRV sweet spot.")
                            .font(.system(size: 11)).foregroundStyle(Theme.faint)
                    }
                }
                coherenceCard
            }
            if vm.mode == .breathwork {
                card {
                    HStack {
                        Text("Guided program").font(.system(size: 13)).foregroundStyle(Theme.text)
                        Spacer()
                        Picker("", selection: $vm.programName) {
                            ForEach(Programs.names, id: \.self) { Text($0).tag($0) }
                        }.tint(Theme.accent)
                    }
                    if let p = Programs.byName(vm.programName) {
                        Text("\(p.summary)  ·  \(p.totalMinutes) min, \(p.stages.count) stages")
                            .font(.system(size: 11)).foregroundStyle(Theme.faint)
                            .fixedSize(horizontal: false, vertical: true)
                    } else {
                        Text("A multi-stage session that paces you and talks you through each step.")
                            .font(.system(size: 11)).foregroundStyle(Theme.faint)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            if vm.mode.narrates {
                cbtiCard
                card {
                    pickerRow("Companion", selection: $vm.companionName,
                              options: ["Orb"] + Characters.names)
                    pickerRow("Guided", selection: $vm.sleepAid, options: SleepAids.names)
                    if vm.sleepAid == SleepAids.storyName {
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
                    } else {
                        Text("A guided session, narrated slowly as you drift off.")
                            .font(.system(size: 11)).foregroundStyle(Theme.faint)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    Toggle("Narrate", isOn: $vm.narrate)
                        .font(.system(size: 13)).foregroundStyle(Theme.text)
                        .tint(Theme.accent)
                    Button { showVoicePicker = true } label: {
                        HStack {
                            Text("Voice").font(.system(size: 13)).foregroundStyle(Theme.text)
                            Spacer()
                            Text(vm.currentVoiceLabel)
                                .font(.system(size: 13)).foregroundStyle(Theme.accent)
                                .lineLimit(1).truncationMode(.tail)
                            Image(systemName: "chevron.right")
                                .font(.system(size: 11)).foregroundStyle(Theme.muted)
                        }
                        .contentShape(Rectangle())
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
                generateCard
                readerCard
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
                Spacer()
                if KokoroModel.bundled {
                    Text("BUILT-IN").font(.system(size: 8, weight: .bold))
                        .foregroundStyle(Theme.bg)
                        .padding(.horizontal, 5).padding(.vertical, 2)
                        .background(Theme.accent).clipShape(Capsule())
                }
            }
            Text("Kokoro — the most natural, fully-offline narration (the same neural voices as the desktop app).")
                .font(.system(size: 11)).foregroundStyle(Theme.faint)
                .fixedSize(horizontal: false, vertical: true)
            if KokoroModel.bundled {
                // The high-quality model ships inside the app — nothing to manage.
                Text(NeuralTTS.backend != nil
                     ? "High-quality model built in ✓ — choose a Neural voice in the Voice list above."
                     : "High-quality model built in ✓ — neural engine not enabled in this build.")
                    .font(.system(size: 10)).foregroundStyle(Theme.accent)
                    .fixedSize(horizontal: false, vertical: true)
                if KokoroModel.downloaded {
                    // A leftover downloaded copy exists — let the user reclaim its space.
                    Button { neural.deleteModel() } label: {
                        Text("Remove extra downloaded copy")
                            .font(.system(size: 11)).foregroundStyle(Theme.muted)
                    }
                }
            } else {
                // No bundled model — fall back to the on-demand download path.
                switch neural.state {
                case .idle:
                    Button { neural.start() } label: {
                        Label("Download voice model", systemImage: "arrow.down.circle")
                            .font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.accent)
                    }
                case .downloading:
                    ProgressView(value: neural.progress).tint(Theme.accent)
                    Text("Downloading… \(Int(neural.progress * 100))%")
                        .font(.system(size: 10)).foregroundStyle(Theme.muted)
                case .ready:
                    Text("Neural voices ready ✓ — pick one in the Voice list.")
                        .font(.system(size: 10)).foregroundStyle(Theme.accent)
                    Button { neural.deleteModel() } label: {
                        Text("Delete downloaded model")
                            .font(.system(size: 11)).foregroundStyle(Theme.muted)
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
    }

    @ViewBuilder private var coherenceCard: some View {
        card {
            HStack {
                Text("Heart coherence").font(.system(size: 13, weight: .medium))
                    .foregroundStyle(Theme.text)
                Spacer()
                Image(systemName: "heart.fill").font(.system(size: 12))
                    .foregroundStyle(CoherenceRing.color(vm.coherence))
            }
            HStack(spacing: 14) {
                ZStack {
                    CoherenceRing(value: vm.coherence).frame(width: 60, height: 60)
                    Text("\(Int((vm.coherence * 100).rounded()))%")
                        .font(.system(size: 14, weight: .semibold, design: .rounded))
                        .foregroundStyle(Theme.text)
                }
                VStack(alignment: .leading, spacing: 3) {
                    Text(vm.running ? coherenceLabel(vm.coherence) : "Start a session to begin")
                        .font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.muted)
                    Button {
                        vm.pacedBpm = (vm.coherenceBpm * 2).rounded() / 2   // snap to 0.5
                    } label: {
                        Text("Match suggested pace · \(String(format: "%.1f", vm.coherenceBpm))/min")
                            .font(.system(size: 11, weight: .medium)).foregroundStyle(Theme.accent)
                    }
                }
                Spacer()
            }
            Text("Breathe slowly and evenly; the ring greens as your heart rhythm steadies. Uses Apple Health heart rate when enabled in Settings, otherwise a live demo.")
                .font(.system(size: 10)).foregroundStyle(Theme.faint)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private func coherenceLabel(_ v: Double) -> String {
        switch v {
        case ..<0.34: return "Finding your rhythm…"
        case ..<0.67: return "Steadying — keep going"
        default:      return "Beautifully coherent"
        }
    }

    @ViewBuilder private var cbtiCard: some View {
        let plan = CBTI.plan(wakeMinutes: wakeMinutes)
        card {
            HStack {
                Text("Sleep program (CBT-I)").font(.system(size: 13, weight: .medium))
                    .foregroundStyle(Theme.text)
                Spacer()
                Image(systemName: "bed.double.fill").font(.system(size: 12))
                    .foregroundStyle(Theme.accent)
            }
            // wake-time anchor (the circadian anchor)
            DatePicker("Wake time", selection: Binding(
                get: { CBTI.dateFrom(wakeMinutes) },
                set: { wakeMinutes = CBTI.minutesFrom($0) }),
                displayedComponents: .hourAndMinute)
                .font(.system(size: 13)).tint(Theme.accent)

            if plan.ready {
                HStack {
                    metric("\(plan.avgEfficiencyPct)%", "efficiency")
                    Divider().frame(height: 30).overlay(Theme.border)
                    metric("\(plan.avgSleepMins / 60)h \(plan.avgSleepMins % 60)m", "slept")
                    Divider().frame(height: 30).overlay(Theme.border)
                    metric("\(plan.nights)", "nights")
                }
                Text("Your sleep window:  \(plan.window)")
                    .font(.system(size: 13, weight: .semibold)).foregroundStyle(Theme.accent)
                Text("Earliest to bed tonight: \(CBTI.clock(plan.bedtimeMinutes)) — not before you feel sleepy.")
                    .font(.system(size: 11)).foregroundStyle(Theme.muted)
                    .fixedSize(horizontal: false, vertical: true)
            } else {
                Text(plan.titration)
                    .font(.system(size: 12)).foregroundStyle(Theme.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if plan.ready {
                Text(plan.titration)
                    .font(.system(size: 11)).foregroundStyle(Theme.faint)
                    .fixedSize(horizontal: false, vertical: true)
            }
            // sleep regularity (steady timing predicts health better than duration)
            if let reg = CBTI.regularity() {
                HStack(spacing: 6) {
                    Text("Sleep regularity").font(.system(size: 12)).foregroundStyle(Theme.muted)
                    Spacer()
                    Text("\(reg)/100").font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(CoherenceRing.color(Double(reg) / 100))
                }
                Text("A steady wake time is the strongest signal for your body clock.")
                    .font(.system(size: 10)).foregroundStyle(Theme.faint)
                    .fixedSize(horizontal: false, vertical: true)
            }
            // wind-down reminder (a consistent pre-sleep buffer)
            let bedR = plan.ready ? plan.bedtimeMinutes : ((wakeMinutes - 480 + 1440) % 1440)
            let wdTime = (bedR - 30 + 1440) % 1440
            Toggle(isOn: Binding(get: { windDownOn }, set: { on in
                windDownOn = on
                if on { Reminders.enableWindDown(hour: wdTime / 60, minute: wdTime % 60) }
                else { Reminders.disableWindDown() }
            })) {
                VStack(alignment: .leading, spacing: 1) {
                    Text("Wind-down reminder").font(.system(size: 13)).foregroundStyle(Theme.text)
                    if windDownOn {
                        Text("Nightly nudge at \(CBTI.clock(wdTime))")
                            .font(.system(size: 10)).foregroundStyle(Theme.faint)
                    }
                }
            }
            .tint(Theme.accent)
            Button { showDiary = true } label: {
                Label("Log last night", systemImage: "square.and.pencil")
                    .font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.accent)
            }
            DisclosureGroup {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(CBTI.rules, id: \.self) { rule in
                        HStack(alignment: .top, spacing: 6) {
                            Text("·").foregroundStyle(Theme.accent)
                            Text(rule).font(.system(size: 11)).foregroundStyle(Theme.faint)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }.padding(.top, 4)
            } label: {
                Text("Sleep rules").font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Theme.muted)
            }
            .tint(Theme.muted)
            Text("💡 \(CBTI.tip(for: Date()))")
                .font(.system(size: 10)).foregroundStyle(Theme.faint)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private func metric(_ value: String, _ label: String) -> some View {
        VStack(spacing: 1) {
            Text(value).font(.system(size: 15, weight: .semibold, design: .rounded))
                .foregroundStyle(Theme.text)
            Text(label).font(.system(size: 10)).foregroundStyle(Theme.faint)
        }
        .frame(maxWidth: .infinity)
    }

    @ViewBuilder private var generateCard: some View {
        card {
            HStack {
                Text("AI bedtime story").font(.system(size: 13, weight: .medium))
                    .foregroundStyle(Theme.text)
                Spacer()
                Image(systemName: "sparkles").font(.system(size: 13))
                    .foregroundStyle(Theme.accentWarm)
            }
            Text("Compose a brand-new, calming story on-device and have it read to you as you fall asleep.")
                .font(.system(size: 11)).foregroundStyle(Theme.faint)
                .fixedSize(horizontal: false, vertical: true)
            if vm.generating {
                HStack(spacing: 8) {
                    ProgressView().controlSize(.small)
                    Text("Composing tonight's story…")
                        .font(.system(size: 12)).foregroundStyle(Theme.muted)
                }
            } else {
                Button { Task { await vm.generateAndNarrateBedtime() } } label: {
                    Label("Generate tonight's story", systemImage: "wand.and.stars")
                        .font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.accent)
                }
            }
            if !GenerativeContent.isAvailable {
                Text("Needs Apple Intelligence (iPhone 15 Pro and later, iOS 26). Without it, a written story is read instead.")
                    .font(.system(size: 10)).foregroundStyle(Theme.faint)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    @ViewBuilder private var readerCard: some View {
        card {
            HStack {
                Text("Read aloud").font(.system(size: 13, weight: .medium))
                    .foregroundStyle(Theme.text)
                Spacer()
                Image(systemName: "book.fill").font(.system(size: 13))
                    .foregroundStyle(Theme.accentWarm)
            }
            Text("Have a short text — a fable or one you paste in — read to you as you fall asleep, in the narration voice above.")
                .font(.system(size: 11)).foregroundStyle(Theme.faint)
                .fixedSize(horizontal: false, vertical: true)
            if vm.reading {
                if !vm.readingCaption.isEmpty {
                    Text(vm.readingCaption)
                        .font(.system(size: 11)).foregroundStyle(Theme.muted)
                        .lineLimit(2)
                }
                Button(role: .destructive) { vm.stopReading() } label: {
                    Label("Stop reading", systemImage: "stop.fill")
                        .font(.system(size: 12, weight: .medium))
                }
            } else {
                Button { showReader = true } label: {
                    Label("Read a text…", systemImage: "text.book.closed")
                        .font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.accent)
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
