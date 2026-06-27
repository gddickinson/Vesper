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

    /// All installed English voices, best quality first (premium → enhanced →
    /// default), then alphabetical. Drives the in-app voice picker.
    static func englishVoices() -> [AVSpeechSynthesisVoice] {
        func rank(_ q: AVSpeechSynthesisVoiceQuality) -> Int {
            switch q {
            case .premium: return 0
            case .enhanced: return 1
            default: return 2
            }
        }
        return AVSpeechSynthesisVoice.speechVoices()
            .filter { $0.language.hasPrefix("en") }
            .sorted {
                rank($0.quality) != rank($1.quality)
                    ? rank($0.quality) < rank($1.quality) : $0.name < $1.name
            }
    }

    /// A friendly label, e.g. "Ava — Premium" or "Daniel · GB".
    static func label(for v: AVSpeechSynthesisVoice) -> String {
        let region = v.language.split(separator: "-").last.map(String.init) ?? ""
        switch v.quality {
        case .premium:  return "\(v.name) — Premium"
        case .enhanced: return "\(v.name) — Enhanced"
        default:        return "\(v.name) · \(region)"
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

    /// Speak a sequence of lines. Replaces anything currently queued.
    func speak(_ lines: [String]) {
        stop()
        guard !lines.isEmpty else { return }
        // AVSpeechUtterance.rate is 0…1 around `default`; map our multiplier.
        let base = AVSpeechUtteranceDefaultSpeechRate
        let mapped = max(AVSpeechUtteranceMinimumSpeechRate,
                         min(AVSpeechUtteranceMaximumSpeechRate, base * rate))
        for line in lines {
            let text = line.trimmingCharacters(in: .whitespacesAndNewlines)
            if text.isEmpty { continue }
            let u = AVSpeechUtterance(string: text)
            u.voice = voice
            u.rate = mapped
            u.pitchMultiplier = 0.98
            u.postUtteranceDelay = linePause
            u.preUtteranceDelay = 0
            queueTexts[ObjectIdentifier(u)] = text
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
