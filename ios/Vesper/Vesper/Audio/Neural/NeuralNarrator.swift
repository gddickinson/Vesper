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

    private let engine = AVAudioEngine()
    private let player = AVAudioPlayerNode()
    private var connected = false
    private var token = 0

    /// Can this narrator actually speak right now?
    var isAvailable: Bool { NeuralTTS.isReady }

    func speak(lines: [String], voiceID: String, rate: Float, linePause: Double) {
        guard let backend = NeuralTTS.backend else { return }
        stop()
        token += 1
        let myToken = token
        isSpeaking = true

        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self else { return }
            for line in lines {
                if self.token != myToken { return }
                let text = line.trimmingCharacters(in: .whitespacesAndNewlines)
                if text.isEmpty { continue }
                guard let out = backend.synthesize(text: text, voiceID: voiceID, speed: rate),
                      let buf = Self.buffer(out.samples, sampleRate: out.sampleRate)
                else { continue }
                DispatchQueue.main.async {
                    guard self.token == myToken else { return }
                    self.ensureGraph(format: buf.format)
                    self.currentLine = text
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

    private static func buffer(_ samples: [Float], sampleRate: Double) -> AVAudioPCMBuffer? {
        guard !samples.isEmpty,
              let fmt = AVAudioFormat(standardFormatWithSampleRate: sampleRate, channels: 1),
              let buf = AVAudioPCMBuffer(pcmFormat: fmt,
                                         frameCapacity: AVAudioFrameCount(samples.count))
        else { return nil }
        buf.frameLength = AVAudioFrameCount(samples.count)
        samples.withUnsafeBufferPointer { p in
            buf.floatChannelData![0].update(from: p.baseAddress!, count: samples.count)
        }
        return buf
    }
}
