//  SessionViewModel.swift
//  Vesper — the app's single state hub.
//
//  Owns the breath clock (the timing authority), the audio engine (breath bed)
//  and the narrator, and republishes the breath state ~60×/s so SwiftUI can
//  animate the orb. Modes (Meditate / Breathwork / Relax / Sleep) one-tap
//  configure pattern + voice + narration, mirroring the desktop mode bar.

import SwiftUI
import Combine

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

    // User selections (persisted).
    @Published var mode: Mode { didSet { if oldValue != mode { applyMode() } } }
    @Published var patternName: String { didSet { clock.setPattern(pattern); save() } }
    @Published var voiceName: String { didSet { engine?.setVoice(voice); save() } }
    @Published var ambienceName: String { didSet { engine?.setAmbience(ambience); save() } }
    @Published var ambienceLevel: Double { didSet { engine?.setAmbienceLevel(Float(ambienceLevel)); save() } }
    @Published var breathLevel: Double { didSet { engine?.setBreathLevel(Float(breathLevel)); save() } }
    @Published var masterVolume: Double { didSet { engine?.masterVolume = Float(masterVolume); save() } }
    @Published var narrate: Bool { didSet { save() } }
    @Published var lectureBranch: String { didSet { if oldValue != lectureBranch { onBranchChange() } } }
    @Published var lectureTitle: String { didSet { save() } }
    /// "Orb" or a character name — the Sleep avatar.
    @Published var companionName: String { didSet { save() } }
    /// Optional auto-stop minutes (0 = open-ended). Drives the progress arc.
    @Published var sessionMinutes: Double { didSet { save() } }

    var audioAvailable: Bool { engine?.isAvailable ?? true }

    private let clock: BreathClock
    private var engine: AudioEngine?
    private let narrator = Narrator()
    private var timer: Timer?
    private let d = UserDefaults.standard

    var pattern: BreathPattern { Patterns.byName(patternName) ?? Patterns.default }
    var voice: BreathVoice { BreathVoice.byName(voiceName) ?? .default }
    var ambience: AmbienceVoice { AmbienceVoice.byName(ambienceName) ?? AmbienceVoice.all[0] }
    var lecture: Lecture { Lectures.byTitle(lectureTitle) ?? Lectures.all.first ?? Lectures.fallback[0] }
    var lecturesInBranch: [Lecture] { Lectures.inBranch(lectureBranch) }

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

    var progress: Double {
        guard sessionMinutes > 0 else { return 0 }
        return min(1, elapsed / (sessionMinutes * 60))
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
        let startLec = Lectures.byTitle(d.string(forKey: "lecture") ?? "")
            ?? Lectures.all.first ?? Lectures.fallback[0]
        lectureBranch = d.string(forKey: "lectureBranch") ?? startLec.branch
        lectureTitle = startLec.title
        companionName = d.string(forKey: "companion") ?? Characters.default
        sessionMinutes = d.object(forKey: "minutes") as? Double ?? 0
        clock = BreathClock(pattern: startPattern)
        breath = BreathMath.state(startPattern, at: 0)
    }

    // MARK: transport

    func togglePlay() { running ? pause() : start() }

    func start() {
        ensureEngine()
        clock.start()
        engine?.start()
        if mode.narrates && narrate {
            narrator.rate = mode == .sleep ? 0.85 : 0.95
            narrator.linePause = mode == .sleep ? 1.4 : 0.6
            narrator.speak(lecture.lines)
        }
        running = true
        startTimer()
    }

    func pause() {
        clock.pause()
        engine?.stop()
        narrator.pause()
        running = false
    }

    func reset() {
        clock.reset()
        narrator.stop()
        caption = ""
        breath = clock.state()
        elapsed = 0
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
        breath = clock.state()
        elapsed = clock.now()
        animT += 1.0 / 60.0
        if narrator.isSpeaking {
            caption = narrator.currentLine
            mouth = max(0, 0.45 + 0.45 * sin(animT * 9)) * 0.7   // gentle lip-sync
        } else {
            mouth = 0
        }
        // gentle auto-stop
        if sessionMinutes > 0 && elapsed >= sessionMinutes * 60 && running {
            pause()
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
        d.set(lectureBranch, forKey: "lectureBranch")
        d.set(lectureTitle, forKey: "lecture")
        d.set(companionName, forKey: "companion")
        d.set(sessionMinutes, forKey: "minutes")
    }
}
