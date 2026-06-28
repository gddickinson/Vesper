//  Narrator.swift
//  Vesper — spoken narration via AVSpeechSynthesizer (the iOS analogue of the
//  desktop `narration.Narrator`).
//
//  Speaks a stream of lines sequentially, softly, with breath-length pauses
//  between them, and keeps playing with the screen locked (it shares the app's
//  `.playback` audio session). Publishes the current line so the UI can show
//  captions / read-along. A neural on-device engine can be layered in later;
//  AVSpeechSynthesizer is the always-available baseline.

import Foundation
@preconcurrency import AVFoundation

final class Narrator: NSObject, ObservableObject, AVSpeechSynthesizerDelegate {
    private nonisolated(unsafe) let synth = AVSpeechSynthesizer()

    @Published var currentLine: String = ""
    @Published var isSpeaking: Bool = false

    /// Rate multiplier (1.0 = the gentle baseline). Stored for the next speak().
    var rate: Float = 0.9
    /// Seconds of silence appended after each line.
    var linePause: Double = 0.6
    var voice: AVSpeechSynthesisVoice? = Narrator.bestVoice()

    private var queueTexts: [ObjectIdentifier: String] = [:]

    override init() {
        super.init()
        synth.delegate = self
    }

    /// Prefer a natural English voice (premium → enhanced → default).
    static func bestVoice() -> AVSpeechSynthesisVoice? {
        let voices = AVSpeechSynthesisVoice.speechVoices()
            .filter { $0.language.hasPrefix("en") }
        func pick(_ q: AVSpeechSynthesisVoiceQuality) -> AVSpeechSynthesisVoice? {
            voices.first { $0.quality == q }
        }
        return pick(.premium) ?? pick(.enhanced) ?? voices.first
            ?? AVSpeechSynthesisVoice(language: "en-GB")
    }

    /// True if `v` is the user's Personal Voice (iOS 17+).
    static func isPersonalVoice(_ v: AVSpeechSynthesisVoice) -> Bool {
        if #available(iOS 17.0, *) { return v.voiceTraits.contains(.isPersonalVoice) }
        return false
    }

    /// All English voices plus any authorized Personal Voice, best first
    /// (Personal → Premium → Enhanced → default), then alphabetical.
    static func englishVoices() -> [AVSpeechSynthesisVoice] {
        func rank(_ v: AVSpeechSynthesisVoice) -> Int {
            if isPersonalVoice(v) { return -1 }
            switch v.quality {
            case .premium: return 0
            case .enhanced: return 1
            default: return 2
            }
        }
        return AVSpeechSynthesisVoice.speechVoices()
            .filter { $0.language.hasPrefix("en") || isPersonalVoice($0) }
            .sorted { rank($0) != rank($1) ? rank($0) < rank($1) : $0.name < $1.name }
    }

    /// A friendly label, e.g. "Ava — Premium", "My Voice — Personal Voice".
    static func label(for v: AVSpeechSynthesisVoice) -> String {
        if isPersonalVoice(v) { return "\(v.name) — Personal Voice" }
        let region = v.language.split(separator: "-").last.map(String.init) ?? ""
        switch v.quality {
        case .premium:  return "\(v.name) — Premium"
        case .enhanced: return "\(v.name) — Enhanced"
        default:        return "\(v.name) · \(region)"
        }
    }

    /// Ask the user to allow Vesper to use their Personal Voice (iOS 17+).
    /// Calls back with whether it's now authorized (always false pre-iOS 17).
    static func requestPersonalVoice(_ done: @escaping (Bool) -> Void) {
        if #available(iOS 17.0, *) {
            AVSpeechSynthesizer.requestPersonalVoiceAuthorization { status in
                DispatchQueue.main.async { done(status == .authorized) }
            }
        } else {
            done(false)
        }
    }

    /// Menu of (id, label) for the picker; "" = automatic best voice.
    static func voiceMenu() -> [(id: String, label: String)] {
        [(id: "", label: "Automatic (best)")]
            + englishVoices().map { (id: $0.identifier, label: label(for: $0)) }
    }

    /// Select a voice by identifier ("" = the best installed voice).
    func selectVoice(id: String) {
        voice = id.isEmpty ? Narrator.bestVoice()
                           : (AVSpeechSynthesisVoice(identifier: id) ?? Narrator.bestVoice())
    }

    /// Speak a sequence of lines. Replaces anything currently queued. When
    /// `windDown` is set, each successive line is a little slower, softer and
    /// more spaced out — the desktop's sleep wind-down, applied across the queue.
    func speak(_ lines: [String], windDown: Bool = false) {
        stop()
        let captions = lines.map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
                            .filter { !$0.isEmpty }
        guard !captions.isEmpty else { return }
        // AVSpeechUtterance.rate is 0…1 around `default`; map our multiplier.
        let base = AVSpeechUtteranceDefaultSpeechRate
        let span = Double(max(1, captions.count - 1))
        for (i, caption) in captions.enumerated() {
            let lvl = windDown ? max(0.25, 1.0 - 0.75 * Double(i) / span) : 1.0
            let u = AVSpeechUtterance(string: Speakable.clean(caption))  // speak words
            u.voice = voice
            u.rate = max(AVSpeechUtteranceMinimumSpeechRate,
                         min(AVSpeechUtteranceMaximumSpeechRate,
                             base * rate * Float(0.82 + 0.18 * lvl)))
            u.volume = Float(0.95 * (0.4 + 0.6 * lvl))
            u.pitchMultiplier = 0.98
            u.postUtteranceDelay = linePause * (1 + 0.6 * (1 - lvl))
            u.preUtteranceDelay = 0
            queueTexts[ObjectIdentifier(u)] = caption   // captions keep the original
            synth.speak(u)
        }
        isSpeaking = true
    }

    func pause() { synth.pauseSpeaking(at: .word) }
    func resume() { synth.continueSpeaking() }

    func stop() {
        synth.stopSpeaking(at: .immediate)
        queueTexts.removeAll()
        isSpeaking = false
        currentLine = ""
    }

    // MARK: AVSpeechSynthesizerDelegate

    func speechSynthesizer(_ s: AVSpeechSynthesizer, didStart u: AVSpeechUtterance) {
        if let t = queueTexts[ObjectIdentifier(u)] {
            DispatchQueue.main.async { self.currentLine = t }
        }
    }

    func speechSynthesizer(_ s: AVSpeechSynthesizer, didFinish u: AVSpeechUtterance) {
        queueTexts[ObjectIdentifier(u)] = nil
        if queueTexts.isEmpty {
            DispatchQueue.main.async { self.isSpeaking = false }
        }
    }

    func speechSynthesizer(_ s: AVSpeechSynthesizer, didCancel u: AVSpeechUtterance) {
        queueTexts[ObjectIdentifier(u)] = nil
    }
}
