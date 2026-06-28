//  SessionViewModel.swift
//  Vesper — the app's single state hub.
//
//  Owns the breath clock (the timing authority), the audio engine (breath bed)
//  and the narrator, and republishes the breath state ~60×/s so SwiftUI can
//  animate the orb. Modes (Meditate / Breathwork / Relax / Sleep) one-tap
//  configure pattern + voice + narration, mirroring the desktop mode bar.

import SwiftUI
import Combine
import UIKit

enum Mode: String, CaseIterable, Identifiable {
    case meditate, breathwork, relax, sleep
    var id: String { rawValue }

    var title: String {
        switch self {
        case .meditate: return "Meditate"
        case .breathwork: return "Breathwork"
        case .relax: return "Relax"
        case .sleep: return "Sleep"
        }
    }
    var symbol: String {
        switch self {
        case .meditate: return "circle.hexagonpath"
        case .breathwork: return "wind"
        case .relax: return "water.waves"
        case .sleep: return "moon.stars.fill"
        }
    }
    var defaultPattern: String {
        switch self {
        case .meditate: return "Coherent 5.5 (Resonance)"
        case .breathwork: return "Box Breathing 4-4-4-4"
        case .relax: return "Calming 4-6 (Long Exhale)"
        case .sleep: return "4-7-8 Relaxing"
        }
    }
    var defaultVoice: String {
        switch self {
        case .meditate: return "Ocean Breath (Ujjayi)"
        case .breathwork: return "Soft Nose Breath"
        case .relax: return "Gentle Wind"
        case .sleep: return "Deep Calm"
        }
    }
    var narrates: Bool { self == .sleep }
    var defaultAmbience: String {
        switch self {
        case .meditate, .breathwork: return "None"
        case .relax: return "Ocean Surf"
        case .sleep: return "Rain"
        }
    }
}

final class SessionViewModel: ObservableObject {
    // Live breath state for the view.
    @Published var breath = BreathState()
    @Published var animT: Double = 0
    @Published var elapsed: Double = 0
    @Published var running = false
    @Published var caption = ""
    @Published var mouth: Double = 0     // 0..1 lip-sync openness for the companion
    @Published var personalVoiceAuthorized = false   // refreshes the voice list

    // User selections (persisted).
    @Published var mode: Mode { didSet { if oldValue != mode { applyMode() } } }
    @Published var patternName: String {
        didSet { if pacedBpm != 0 { pacedBpm = 0 }; clock.setPattern(pattern); save() }
    }
    @Published var voiceName: String { didSet { engine?.setVoice(voice); save() } }
    @Published var ambienceName: String { didSet { engine?.setAmbience(ambience); save() } }
    @Published var ambienceLevel: Double { didSet { engine?.setAmbienceLevel(Float(ambienceLevel)); save() } }
    @Published var breathLevel: Double { didSet { engine?.setBreathLevel(Float(breathLevel)); save() } }
    @Published var masterVolume: Double { didSet { engine?.masterVolume = Float(masterVolume); save() } }
    @Published var narrate: Bool { didSet { save() } }
    /// Narration voice identifier ("" = automatic best installed voice).
    @Published var narrationVoiceID: String { didSet { save() } }
    @Published var lectureBranch: String { didSet { if oldValue != lectureBranch { onBranchChange() } } }
    @Published var lectureTitle: String { didSet { save() } }
    /// "Orb" or a character name — the Sleep avatar.
    @Published var companionName: String { didSet { save() } }
    /// Sleep guided session — "Bedtime story" (a lecture) or a guided sleep aid.
    @Published var sleepAid: String { didSet { save() } }
    /// Optional auto-stop minutes (0 = open-ended). Drives the progress arc.
    @Published var sessionMinutes: Double { didSet { save() } }
    /// Active guided program ("None" = free breathing). Breathwork only.
    @Published var programName: String { didSet { save() } }
    /// Gentle haptic tap on each breath phase (Meditate/Breathwork; off in Sleep).
    @Published var haptics: Bool { didSet { save() } }
    /// A brief "breathe with me" lead-in before the pattern engages (non-Sleep).
    @Published var settleIn: Bool { didSet { save() } }
    /// Post-session mood check-ins.
    @Published var moodEnabled: Bool { didSet { save() } }
    /// Write Mindful Minutes (+ iOS 18 State of Mind) to Apple Health.
    @Published var syncHealth: Bool {
        didSet { if syncHealth && !oldValue { HealthStore.shared.requestAuthorization() }; save() }
    }
    /// Background scene ("Auto" = a per-mode default).
    @Published var backdrop: String { didSet { save() } }
    /// A daily local-notification reminder to practise.
    @Published var reminderOn: Bool { didSet { updateReminder(); save() } }
    @Published var reminderTime: Date { didSet { if reminderOn { updateReminder() }; save() } }
    /// Resonance pace in breaths/min (0 = use the named pattern).
    @Published var pacedBpm: Double {
        didSet { if pacedBpm != oldValue { clock.setPattern(pattern); save() } }
    }
    /// Meditate interval-bell spacing in minutes (0 = off).
    @Published var bellMinutes: Double {
        didSet {
            nextBellAt = (bellMinutes > 0 && running) ? elapsed + bellMinutes * 60
                                                       : .greatestFiniteMagnitude
            save()
        }
    }

    // Transient UI signals (not persisted).
    @Published var leadIn: Double = 0          // seconds left in the settle-in
    @Published var askMood = false             // show the post-session mood sheet
    @Published var showOnboarding = false      // show the first-run welcome
    @Published var patternsRevision = 0        // bumps when custom patterns change
    @Published var reading = false             // a Reader text is being narrated
    @Published var readingCaption = ""         // the sentence currently being read
    @Published var generating = false          // composing an on-device AI story
    @Published var coherence = 0.0             // 0..1 heart-rhythm coherence (Meditate)
    @Published var coherenceBpm = 6.0          // adaptive resonance-pace suggestion

    var audioAvailable: Bool { engine?.isAvailable ?? true }

    private let clock: BreathClock
    private var engine: AudioEngine?
    private let narrator = Narrator()
    private let neuralNarrator = NeuralNarrator()
    private let nowPlaying = NowPlaying()
    private var runStart: Double = 0
    private var runStartDate = Date()              // wall-clock session start (for Health)
    private var timer: Timer?
    private var lastPhase: BreathPhase = .inhale   // for breath-phase haptics
    private let bell = Bell()
    private var nextBellAt: Double = .greatestFiniteMagnitude
    private var programStage = 0
    private var stageEndsAt = 0.0
    private var moodAskedThisRun = false
    private var hasOnboarded: Bool
    private var readingTitle = ""              // title of the Reader text in progress
    private var readingBase = 0                // sentence index the reading started at
    private let coherenceModel = CoherenceModel()   // HRV biofeedback (Meditate)
    private let hrSource = HeartRateSource()
    private var lastHRSample = 0.0
    private var lastCohUpdate = 0.0
    private let d = UserDefaults.standard

    var pattern: BreathPattern {
        if pacedBpm > 0 { return BreathPattern.paced(bpm: pacedBpm) }
        return Patterns.byName(patternName) ?? CustomPatterns.byName(patternName) ?? Patterns.default
    }
    var voice: BreathVoice { BreathVoice.byName(voiceName) ?? .default }
    var ambience: AmbienceVoice { AmbienceVoice.byName(ambienceName) ?? AmbienceVoice.all[0] }
    var lecture: Lecture { Lectures.byTitle(lectureTitle) ?? Lectures.all.first ?? Lectures.fallback[0] }
    var lecturesInBranch: [Lecture] { Lectures.inBranch(lectureBranch) }
    /// Device / Personal / downloaded premium voices (always available).
    var systemVoiceMenu: [(id: String, label: String)] { Narrator.voiceMenu() }

    /// Offline Kokoro neural voices (only when the model is present).
    var neuralVoiceMenu: [(id: String, label: String)] {
        NeuralTTS.modelPresent
            ? KokoroCatalog.all.map { (id: KokoroCatalog.pickerID($0), label: $0.label) }
            : []
    }

    /// Everything, for lookups (e.g. the current selection's label).
    var narrationVoices: [(id: String, label: String)] { systemVoiceMenu + neuralVoiceMenu }

    /// Friendly label for whatever voice is currently selected.
    var currentVoiceLabel: String {
        narrationVoices.first { $0.id == narrationVoiceID }?.label ?? "Automatic (best)"
    }

    func onBranchChange() {
        if let first = lecturesInBranch.first { lectureTitle = first.title }
        save()
    }

    /// Pick a random lecture from anywhere in the library.
    func surpriseLecture() {
        let l = Lectures.random()
        lectureBranch = l.branch
        lectureTitle = l.title
    }

    /// Apply today's suggested mode + breathing pattern.
    func applyDailyPick() {
        let p = DailyPick.today
        if mode != p.mode { mode = p.mode }   // switching resets to mode defaults…
        patternName = p.pattern                // …then apply the suggested pattern
    }

    /// Built-in + custom pattern names for the picker.
    var allPatternNames: [String] {
        _ = patternsRevision                  // re-read when customs change
        return Patterns.all.map(\.name) + CustomPatterns.names
    }

    func saveCustomPattern(name: String, inhale: Double, holdFull: Double,
                           exhale: Double, holdEmpty: Double) {
        CustomPatterns.save(CustomPattern(name: name, inhale: inhale, holdFull: holdFull,
                                          exhale: exhale, holdEmpty: holdEmpty))
        patternsRevision += 1
        patternName = name
    }

    func deleteCustomPattern(_ name: String) {
        CustomPatterns.delete(name)
        patternsRevision += 1
        if patternName == name { patternName = Patterns.default.name }
    }

    /// Ask iOS to let Vesper use the user's Personal Voice; on success it
    /// appears in the voice picker.
    func enablePersonalVoice() {
        Narrator.requestPersonalVoice { [weak self] ok in self?.personalVoiceAuthorized = ok }
    }

    /// Speak one line in the chosen voice so the user can audition it.
    func previewVoice() {
        ensureEngine()
        let line = "This is how tonight's stories will sound, soft and slow."
        if let kid = KokoroCatalog.voiceID(fromPicker: narrationVoiceID), NeuralTTS.isReady {
            neuralNarrator.speak(lines: [line], voiceID: kid, rate: 0.95, linePause: 0)
        } else {
            narrator.rate = 0.92
            narrator.linePause = 0.2
            narrator.selectVoice(id: narrationVoiceID)
            narrator.speak([line])
        }
    }

    // MARK: reader

    /// Narrate a text (a fable, a pasted passage) sentence-by-sentence in the
    /// chosen narration voice, resuming from `fromIndex`. `sleepFade` adds the
    /// Sleep wind-down (slow + soften toward silence). Independent of a breath
    /// session — you can read on its own, or over a running breath bed.
    func readText(title: String, content: String, fromIndex: Int, sleepFade: Bool) {
        let all = Books.sentences(content)
        guard !all.isEmpty else { return }
        let from = max(0, min(fromIndex, all.count - 1))
        ensureEngine()
        readingTitle = title
        readingBase = from
        reading = true
        readingCaption = ""
        UIApplication.shared.isIdleTimerDisabled = true
        let slice = Array(all[from...])
        let wind: Double = sleepFade ? 1500 : 0
        if let kid = KokoroCatalog.voiceID(fromPicker: narrationVoiceID), NeuralTTS.isReady {
            neuralNarrator.speak(lines: slice, voiceID: kid, rate: 0.9,
                                 linePause: 0.5, windDown: wind)
        } else {
            narrator.rate = 0.9
            narrator.linePause = 0.45
            narrator.selectVoice(id: narrationVoiceID)
            narrator.speak(slice, windDown: sleepFade)
        }
        if timer == nil { startTimer() }
    }

    /// Compose a fresh bedtime story on-device (Foundation Models, iOS 26+) and
    /// narrate it with the Sleep wind-down. Falls back to reading the currently
    /// selected lecture when the on-device model isn't available or generation
    /// fails — so the button always does something soothing.
    @MainActor
    func generateAndNarrateBedtime() async {
        guard !generating else { return }
        generating = true
        let theme = GenerativeContent.themes.randomElement() ?? "a quiet, starlit night"
        let lines = await GenerativeContent.generateBedtime(theme: theme)
        generating = false
        if let lines, !lines.isEmpty {
            readText(title: "Tonight's Story", content: lines.joined(separator: " "),
                     fromIndex: 0, sleepFade: true)
        } else {
            // graceful fallback: read the selected lecture as the bedtime story
            readText(title: lecture.title, content: lecture.lines.joined(separator: " "),
                     fromIndex: 0, sleepFade: true)
        }
    }

    /// Stop the Reader, saving where we got to so it can resume later.
    func stopReading() {
        if reading {
            Books.setResume(readingTitle, readingBase + neuralNarrator.currentIndex)
        }
        reading = false
        readingCaption = ""
        neuralNarrator.stop()
        narrator.stop()
        if !running {
            UIApplication.shared.isIdleTimerDisabled = false
            timer?.invalidate(); timer = nil
        }
    }

    var progress: Double {
        guard sessionMinutes > 0 else { return 0 }
        return min(1, elapsed / (sessionMinutes * 60))
    }

    static let sceneNames = ["Auto", "None", "Night Sky", "Embers", "Fireplace", "Aurora", "Ocean"]

    /// The background scene to draw, resolving "Auto" to a per-mode default.
    var resolvedBackdrop: SceneKind {
        switch backdrop {
        case "None":      return .none
        case "Night Sky": return .nightSky
        case "Embers":    return .embers
        case "Fireplace": return .fireplace
        case "Aurora":    return .aurora
        case "Ocean":     return .ocean
        default:
            switch mode {
            case .sleep: return .nightSky
            case .relax: return .ocean      // moonlit sea suits Relax (desktop WaveScene)
            default:     return .none
            }
        }
    }

    /// How sleepy the Sleep companion looks (0..1): a cozy baseline that deepens
    /// with the wind-down dimming, drooping its eyes and (past ~0.6) drifting "z"s.
    var companionDrowsy: Double {
        guard mode == .sleep else { return 0 }
        return min(0.95, 0.45 + (dimLevel / 0.6) * 0.5)
    }

    /// Sleep screen-dim: eases 0 → 0.6 over the session (or ~15 min if open-ended)
    /// so the screen recedes as you drift off — the desktop wind-down dimming.
    var dimLevel: Double {
        guard mode == .sleep && running else { return 0 }
        let span = sessionMinutes > 0 ? sessionMinutes * 60 : 900
        return min(0.6, max(0, elapsed) / span * 0.6)
    }

    init() {
        let m = Mode(rawValue: d.string(forKey: "mode") ?? "meditate") ?? .meditate
        mode = m
        let startPattern = Patterns.byName(d.string(forKey: "pattern") ?? m.defaultPattern)
            ?? Patterns.default
        patternName = startPattern.name
        voiceName = d.string(forKey: "voice") ?? m.defaultVoice
        ambienceName = d.string(forKey: "ambience") ?? m.defaultAmbience
        ambienceLevel = d.object(forKey: "ambienceLevel") as? Double ?? 0.5
        breathLevel = d.object(forKey: "breathLevel") as? Double ?? 0.8
        masterVolume = d.object(forKey: "master") as? Double ?? 0.9
        narrate = d.object(forKey: "narrate") as? Bool ?? true
        narrationVoiceID = d.string(forKey: "voiceID") ?? ""
        let startLec = Lectures.byTitle(d.string(forKey: "lecture") ?? "")
            ?? Lectures.all.first ?? Lectures.fallback[0]
        lectureBranch = d.string(forKey: "lectureBranch") ?? startLec.branch
        lectureTitle = startLec.title
        companionName = d.string(forKey: "companion") ?? Characters.default
        sleepAid = d.string(forKey: "sleepAid") ?? SleepAids.storyName
        programName = d.string(forKey: "programName") ?? Programs.none
        sessionMinutes = d.object(forKey: "minutes") as? Double ?? 0
        haptics = d.object(forKey: "haptics") as? Bool ?? true
        settleIn = d.object(forKey: "settleIn") as? Bool ?? true
        moodEnabled = d.object(forKey: "moodEnabled") as? Bool ?? true
        syncHealth = d.object(forKey: "syncHealth") as? Bool ?? false
        backdrop = d.string(forKey: "backdrop") ?? "Auto"
        pacedBpm = d.object(forKey: "pacedBpm") as? Double ?? 0
        bellMinutes = d.object(forKey: "bellMinutes") as? Double ?? 0
        hasOnboarded = d.bool(forKey: "hasOnboarded")
        reminderOn = d.bool(forKey: "reminderOn")
        reminderTime = (d.object(forKey: "reminderTime") as? Double).map {
            Date(timeIntervalSinceReferenceDate: $0)
        } ?? (Calendar.current.date(bySettingHour: 21, minute: 0, second: 0, of: Date()) ?? Date())
        let active = (d.object(forKey: "pacedBpm") as? Double ?? 0) > 0
            ? BreathPattern.paced(bpm: d.object(forKey: "pacedBpm") as? Double ?? 5.5)
            : startPattern
        clock = BreathClock(pattern: active)
        breath = BreathMath.state(active, at: 0)
        showOnboarding = !hasOnboarded
        nowPlaying.configure { [weak self] in self?.togglePlay() }
    }

    private func updateNowPlaying(playing: Bool) {
        let title = mode == .sleep ? lecture.title : mode.title
        nowPlaying.update(title: title, subtitle: "Vesper · \(pattern.name)", playing: playing)
    }

    // MARK: transport

    func togglePlay() { running ? pause() : start() }

    func start() {
        UIApplication.shared.isIdleTimerDisabled = true   // don't auto-lock mid-session
        moodAskedThisRun = false
        running = true
        updateNowPlaying(playing: true)
        if settleIn && mode != .sleep {
            // A short "breathe with me" lead-in before the pattern engages.
            leadIn = 3.0
            breath = BreathMath.state(pattern, at: 0)
            if haptics { Haptics.prepare() }
            startTimer()
        } else {
            beginSession()
            startTimer()
        }
    }

    /// Actually begin the breath clock, audio and narration (after any lead-in).
    private func beginSession() {
        // A guided program's first stage sets the starting pace before the clock.
        var program: GuidedProgram?
        if programName != Programs.none, let p = Programs.byName(programName), !p.stages.isEmpty {
            program = p
            programStage = 0
            patternName = p.stages[0].pattern
            stageEndsAt = p.stages[0].minutes * 60
        }
        ensureEngine()
        clock.start()
        runStart = clock.now()
        runStartDate = Date()
        engine?.start()
        nextBellAt = bellMinutes > 0 ? bellMinutes * 60 : .greatestFiniteMagnitude
        lastPhase = clock.state().phase
        // Heart-coherence biofeedback (Meditate): fresh model; stream real HR only
        // when the user has opted into Apple Health (else the demo source drives it).
        if mode == .meditate {
            coherenceModel.reset(); coherence = 0; lastHRSample = 0; lastCohUpdate = 0
            if syncHealth {
                hrSource.startReal { [weak self] hr, t in self?.coherenceModel.add(hr: hr, at: t) }
            }
        }
        if haptics && mode != .sleep { Haptics.prepare() }
        if let p = program { speakCue(p.stages[0].say) }
        if mode.narrates && narrate {
            let rate: Float = mode == .sleep ? 0.85 : 0.95
            let pause: Double = mode == .sleep ? 1.4 : 0.6
            // Sleep gently slows + softens the narration over the session (or ~20
            // min if open-ended), so you drift off — the desktop wind-down.
            let windDown: Double = mode == .sleep
                ? (sessionMinutes > 0 ? sessionMinutes * 60 : 1200) : 0
            // In Sleep, a chosen guided aid replaces the bedtime story.
            let lines = (mode == .sleep && sleepAid != SleepAids.storyName
                ? SleepAids.lines(for: sleepAid) : nil) ?? lecture.lines
            if let kid = KokoroCatalog.voiceID(fromPicker: narrationVoiceID), NeuralTTS.isReady {
                neuralNarrator.speak(lines: lines, voiceID: kid,
                                     rate: rate, linePause: pause, windDown: windDown)
            } else {
                narrator.rate = rate
                narrator.linePause = pause
                narrator.selectVoice(id: narrationVoiceID)   // falls back to best for neural ids
                narrator.speak(lines, windDown: mode == .sleep)
            }
        }
    }

    func pause() {
        let ran = max(0, clock.now() - runStart)
        leadIn = 0
        PracticeLog.log(minutes: ran / 60)
        if syncHealth && ran >= 60 {
            HealthStore.shared.saveMindfulMinutes(start: runStartDate, end: Date())
        }
        clock.pause()
        engine?.stop()
        narrator.pause()
        neuralNarrator.stop()
        hrSource.stop()
        running = false
        UIApplication.shared.isIdleTimerDisabled = false   // allow auto-lock again
        updateNowPlaying(playing: false)
        maybeAskMood(ranSeconds: ran)
    }

    func reset() {
        clock.reset()
        narrator.stop()
        neuralNarrator.stop()
        caption = ""
        leadIn = 0
        runStart = 0
        moodAskedThisRun = false
        nextBellAt = bellMinutes > 0 ? bellMinutes * 60 : .greatestFiniteMagnitude
        programStage = 0
        stageEndsAt = 0
        breath = clock.state()
        elapsed = 0
    }

    // MARK: reflection + onboarding

    private func maybeAskMood(ranSeconds: Double) {
        guard moodEnabled, ranSeconds >= 60, !moodAskedThisRun else { return }
        moodAskedThisRun = true
        askMood = true
    }

    func logMood(_ level: Int) {
        PracticeLog.setLastMood(level)
        askMood = false
        // Mirror the 1–5 mood to Apple Health as a State of Mind (iOS 18+).
        if syncHealth, #available(iOS 18.0, *) {
            let valence = (Double(level) - 3.0) / 2.0   // 1→−1 … 3→0 … 5→+1
            HealthStore.shared.saveStateOfMind(valence: valence, at: Date())
        }
    }
    func dismissMood() { askMood = false }
    func finishOnboarding() {
        hasOnboarded = true
        d.set(true, forKey: "hasOnboarded")
        showOnboarding = false
    }
    func showWelcomeAgain() { showOnboarding = true }

    // MARK: intents + reminders

    /// Apply a pending Siri / Shortcuts request on launch or foreground.
    func applyPendingIntent() {
        if let raw = d.string(forKey: "pendingMode"), let m = Mode(rawValue: raw) {
            d.removeObject(forKey: "pendingMode")
            if mode != m { mode = m }
        }
        if d.bool(forKey: "pendingAutoStart") {
            d.removeObject(forKey: "pendingAutoStart")
            if !running { start() }
        }
    }

    private func updateReminder() {
        if reminderOn {
            let c = Calendar.current.dateComponents([.hour, .minute], from: reminderTime)
            Reminders.enable(hour: c.hour ?? 21, minute: c.minute ?? 0)
        } else {
            Reminders.disable()
        }
    }

    /// Speak a short guided-program instruction (neural if ready, else system).
    private func speakCue(_ s: String) {
        if let kid = KokoroCatalog.voiceID(fromPicker: narrationVoiceID), NeuralTTS.isReady {
            neuralNarrator.speak(lines: [s], voiceID: kid, rate: 0.98, linePause: 0)
        } else {
            narrator.rate = 0.98
            narrator.linePause = 0
            narrator.selectVoice(id: narrationVoiceID)
            narrator.speak([s])
        }
    }

    private func ensureEngine() {
        if engine == nil {
            let e = AudioEngine(clock: clock, voice: voice)
            e.masterVolume = Float(masterVolume)
            e.setBreathLevel(Float(breathLevel))
            e.setAmbience(ambience)
            e.setAmbienceLevel(Float(ambienceLevel))
            engine = e
        }
    }

    // MARK: modes

    private func applyMode() {
        if programName != Programs.none { programName = Programs.none }
        patternName = mode.defaultPattern
        voiceName = mode.defaultVoice
        ambienceName = mode.defaultAmbience
        save()
    }

    // MARK: tick

    private func startTimer() {
        timer?.invalidate()
        let t = Timer(timeInterval: 1.0 / 60.0, repeats: true) { [weak self] _ in
            self?.tick()
        }
        RunLoop.main.add(t, forMode: .common)
        timer = t
    }

    private func tick() {
        // Settle-in lead-in: count down "breathe with me", then begin the session.
        if leadIn > 0 {
            leadIn -= 1.0 / 60.0
            animT += 1.0 / 60.0
            if leadIn <= 0 { leadIn = 0; beginSession() }
            return
        }
        // Reader: poll narration progress; can run with or without a breath session.
        if reading {
            animT += 1.0 / 60.0
            if neuralNarrator.isSpeaking {
                readingCaption = neuralNarrator.currentLine
                Books.setResume(readingTitle, readingBase + neuralNarrator.currentIndex)
                mouth = max(0, 0.45 + 0.45 * sin(animT * 9)) * 0.7
            } else if narrator.isSpeaking {
                readingCaption = narrator.currentLine
                mouth = max(0, 0.45 + 0.45 * sin(animT * 9)) * 0.7
            } else {
                Books.setResume(readingTitle, 0)   // reached the end — reset for next time
                reading = false
                readingCaption = ""
                mouth = 0
                if !running {
                    UIApplication.shared.isIdleTimerDisabled = false
                    timer?.invalidate(); timer = nil
                }
            }
            if !running { return }   // reading on its own — skip breath/session logic
        }
        breath = clock.state()
        elapsed = clock.now()
        animT += 1.0 / 60.0
        // Interval bell (Meditate).
        if elapsed >= nextBellAt {
            bell.ring()
            nextBellAt += max(60, bellMinutes * 60)
        }
        // Guided program: advance stages, speaking each instruction.
        if programName != Programs.none, let prog = Programs.byName(programName), elapsed >= stageEndsAt {
            programStage += 1
            if programStage < prog.stages.count {
                let st = prog.stages[programStage]
                patternName = st.pattern
                stageEndsAt += st.minutes * 60
                speakCue(st.say)
            } else {
                if haptics { Haptics.done() }
                pause()
                return
            }
        }
        // Gentle haptic as each breath phase begins (not during Sleep).
        if breath.phase != lastPhase {
            lastPhase = breath.phase
            if haptics && running && mode != .sleep { Haptics.phase(breath.phase) }
        }
        if neuralNarrator.isSpeaking {
            caption = neuralNarrator.currentLine
            mouth = max(0, 0.45 + 0.45 * sin(animT * 9)) * 0.7
        } else if narrator.isSpeaking {
            caption = narrator.currentLine
            mouth = max(0, 0.45 + 0.45 * sin(animT * 9)) * 0.7   // gentle lip-sync
        } else {
            mouth = 0
        }
        // heart-rhythm coherence (Meditate)
        if mode == .meditate { tickCoherence() }
        // gentle auto-stop
        if sessionMinutes > 0 && elapsed >= sessionMinutes * 60 && running {
            if haptics { Haptics.done() }
            pause()
        }
    }

    /// Feed the coherence model (~2 Hz) and recompute (~1 Hz). Uses live HealthKit
    /// HR when streaming, otherwise a breath-driven demo tachogram (sim-friendly).
    private func tickCoherence() {
        if animT - lastHRSample >= 0.5 {
            lastHRSample = animT
            if !hrSource.streamingReal {
                coherenceModel.add(hr: HeartRateSource.demoHR(t: animT, breath: breath.volume),
                                   at: animT)
            }
        }
        if animT - lastCohUpdate >= 1.0 {
            lastCohUpdate = animT
            coherenceModel.update()
            coherence = coherenceModel.coherence
            coherenceBpm = coherenceModel.suggestedBpm
        }
    }

    private func save() {
        d.set(mode.rawValue, forKey: "mode")
        d.set(patternName, forKey: "pattern")
        d.set(voiceName, forKey: "voice")
        d.set(ambienceName, forKey: "ambience")
        d.set(ambienceLevel, forKey: "ambienceLevel")
        d.set(breathLevel, forKey: "breathLevel")
        d.set(masterVolume, forKey: "master")
        d.set(narrate, forKey: "narrate")
        d.set(narrationVoiceID, forKey: "voiceID")
        d.set(lectureBranch, forKey: "lectureBranch")
        d.set(lectureTitle, forKey: "lecture")
        d.set(companionName, forKey: "companion")
        d.set(sleepAid, forKey: "sleepAid")
        d.set(programName, forKey: "programName")
        d.set(sessionMinutes, forKey: "minutes")
        d.set(haptics, forKey: "haptics")
        d.set(settleIn, forKey: "settleIn")
        d.set(moodEnabled, forKey: "moodEnabled")
        d.set(syncHealth, forKey: "syncHealth")
        d.set(backdrop, forKey: "backdrop")
        d.set(pacedBpm, forKey: "pacedBpm")
        d.set(bellMinutes, forKey: "bellMinutes")
        d.set(reminderOn, forKey: "reminderOn")
        d.set(reminderTime.timeIntervalSinceReferenceDate, forKey: "reminderTime")
    }
}
