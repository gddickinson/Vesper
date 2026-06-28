//  NeuralNarrator.swift
//  Vesper — plays neural-TTS (Kokoro) narration. Synthesizes each line via the
//  registered NeuralTTSBackend (off the main thread) and streams the float PCM
//  through an AVAudioPlayerNode, with breath-length silence between lines. If no
//  backend is registered it does nothing (the caller falls back to the system
//  narrator), so this compiles and links with no ML dependency.

import Foundation
@preconcurrency import AVFoundation

final class NeuralNarrator: NSObject, ObservableObject {
    @Published var currentLine = ""
    @Published var isSpeaking = false
    @Published var currentIndex = 0   // index of the line being spoken (for resume)

    private let engine = AVAudioEngine()
    private let player = AVAudioPlayerNode()
    private var connected = false
    private var token = 0

    /// Can this narrator actually speak right now?
    var isAvailable: Bool { NeuralTTS.isReady }

    /// Speak a stream of lines. `windDown` (seconds, 0 = off) gradually slows and
    /// softens delivery over that span — the desktop's sleep wind-down feel.
    func speak(lines: [String], voiceID: String, rate: Float, linePause: Double,
               windDown: Double = 0) {
        guard let backend = NeuralTTS.backend else { return }
        stop()
        token += 1
        let myToken = token
        isSpeaking = true
        currentIndex = 0
        let start = ProcessInfo.processInfo.systemUptime

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }
            for (idx, line) in lines.enumerated() {
                if self.token != myToken { return }
                let caption = line.trimmingCharacters(in: .whitespacesAndNewlines)
                let text = Speakable.clean(line)        // speak words, not symbols
                if text.isEmpty { continue }
                // Ease level 1 -> 0.15 over `windDown`; map to a slower speed and
                // a softer gain so the narration drifts toward sleep.
                let lvl = windDown > 0
                    ? max(0.15, 1.0 - 0.85 * min(1.0,
                        (ProcessInfo.processInfo.systemUptime - start) / windDown))
                    : 1.0
                let speed = Float(min(1.2, max(0.55, Double(rate) * (0.72 + 0.28 * lvl))))
                let gain = Float(0.72 * (0.30 + 0.70 * lvl))
                guard let out = backend.synthesize(text: text, voiceID: voiceID, speed: speed),
                      let buf = Self.buffer(out.samples, sampleRate: out.sampleRate, gain: gain)
                else { continue }
                DispatchQueue.main.async {
                    guard self.token == myToken else { return }
                    self.ensureGraph(format: buf.format)
                    self.currentLine = caption          // captions keep the original
                    self.currentIndex = idx
                    self.player.scheduleBuffer(buf, completionHandler: nil)
                    if linePause > 0,
                       let gap = Self.buffer(Array(repeating: 0,
                                                   count: Int(out.sampleRate * linePause)),
                                             sampleRate: out.sampleRate) {
                        self.player.scheduleBuffer(gap, completionHandler: nil)
                    }
                }
            }
            DispatchQueue.main.async { if self.token == myToken { self.isSpeaking = false } }
        }
    }

    func pause() { player.pause() }
    func resume() { if isAvailable { try? engine.start(); player.play() } }

    func stop() {
        token += 1
        player.stop()
        currentLine = ""
        isSpeaking = false
    }

    // MARK: graph

    private func ensureGraph(format: AVAudioFormat) {
        if !connected {
            engine.attach(player)
            engine.connect(player, to: engine.mainMixerNode, format: format)
            connected = true
        }
        if !engine.isRunning {
            try? AVAudioSession.sharedInstance().setActive(true)
            try? engine.start()
        }
        if !player.isPlaying { player.play() }
    }

    /// Build a mono buffer, scaled by `gain`, with 10 ms raised-cosine edge fades
    /// so each clip starts/stops without a click (matches the desktop narrator).
    private static func buffer(_ samples: [Float], sampleRate: Double,
                               gain: Float = 1) -> AVAudioPCMBuffer? {
        guard !samples.isEmpty,
              let fmt = AVAudioFormat(standardFormatWithSampleRate: sampleRate, channels: 1),
              let buf = AVAudioPCMBuffer(pcmFormat: fmt,
                                         frameCapacity: AVAudioFrameCount(samples.count))
        else { return nil }
        let n = samples.count
        buf.frameLength = AVAudioFrameCount(n)
        let nf = min(Int(sampleRate * 0.010), n / 2)   // 10 ms fade
        let dst = buf.floatChannelData![0]
        samples.withUnsafeBufferPointer { p in
            for i in 0..<n {
                var s = p[i] * gain
                if nf > 0 {
                    if i < nf {
                        s *= 0.5 - 0.5 * cos(Float.pi * Float(i) / Float(nf))
                    } else if i >= n - nf {
                        s *= 0.5 - 0.5 * cos(Float.pi * Float(n - 1 - i) / Float(nf))
                    }
                }
                dst[i] = s
            }
        }
        return buf
    }
}
