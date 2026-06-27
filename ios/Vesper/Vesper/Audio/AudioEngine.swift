//  AudioEngine.swift
//  Vesper — AVAudioEngine host for the procedural breath bed.
//
//  An AVAudioSourceNode renders the BreathSynth in real time, reading the shared
//  BreathClock so the sound stays in lock-step with the on-screen breath. The
//  audio session uses the `.playback` category, which — together with the
//  `audio` UIBackgroundMode — lets the breath and narration keep playing with
//  the screen locked. That background-with-screen-off ability is the whole
//  reason this is a native app rather than a web page.

import Foundation
import AVFoundation

final class AudioEngine {
    private let engine = AVAudioEngine()
    private var source: AVAudioSourceNode?
    private let clock: BreathClock
    private let synth: BreathSynth
    private let ambience: AmbienceSynth
    private let sr: Double

    private let maxFrames = 8192
    private var scratch: UnsafeMutablePointer<Float>

    private(set) var isAvailable = false
    private(set) var isRunning = false

    /// Master output volume 0…1.
    var masterVolume: Float = 0.9 {
        didSet { engine.mainMixerNode.outputVolume = max(0, min(1, masterVolume)) }
    }

    init(clock: BreathClock, voice: BreathVoice) {
        self.clock = clock
        let session = AVAudioSession.sharedInstance()
        // Pick a sensible hardware sample rate.
        let rate = session.sampleRate > 0 ? session.sampleRate : 44100
        self.sr = rate
        self.synth = BreathSynth(sr: Float(rate), voice: voice)
        self.ambience = AmbienceSynth(sr: Float(rate),
                                      voice: AmbienceVoice.byName("None") ?? AmbienceVoice.all[0])
        self.scratch = .allocate(capacity: maxFrames)
        scratch.initialize(repeating: 0, count: maxFrames)
        configureSession()
        buildGraph()
    }

    deinit { scratch.deinitialize(count: maxFrames); scratch.deallocate() }

    // MARK: session

    private func configureSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playback, mode: .default, options: [])
            try session.setActive(true)
        } catch {
            NSLog("Vesper audio session error: \(error.localizedDescription)")
        }
        NotificationCenter.default.addObserver(
            self, selector: #selector(handleInterruption),
            name: AVAudioSession.interruptionNotification, object: session)
    }

    @objc private func handleInterruption(_ note: Notification) {
        guard let info = note.userInfo,
              let raw = info[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: raw) else { return }
        if type == .began {
            engine.pause()
        } else if type == .ended {
            try? AVAudioSession.sharedInstance().setActive(true)
            if isRunning { try? engine.start() }
        }
    }

    // MARK: graph

    private func buildGraph() {
        let format = AVAudioFormat(standardFormatWithSampleRate: sr, channels: 2)
        guard let format else { return }

        let clk = clock
        let syn = synth
        let amb = ambience
        let scratchPtr = scratch
        let srF = Float(sr)

        let node = AVAudioSourceNode(format: format) { _, _, frameCount, ablPtr -> OSStatus in
            let frames = Int(frameCount)
            let abl = UnsafeMutableAudioBufferListPointer(ablPtr)

            // Paused → emit silence.
            guard clk.isRunning, frames > 0, frames <= 8192 else {
                let bytes = Int(frameCount) * MemoryLayout<Float>.size
                for buffer in abl {
                    if let p = buffer.mData { memset(p, 0, bytes) }
                }
                return noErr
            }

            // Read the one clock at block start and end; ramp across the block.
            let t0 = clk.now()
            let t1 = t0 + Double(frames) / Double(srF)
            let s0 = clk.state(at: t0)
            let s1 = clk.state(at: t1)
            let a0 = Float(s0.airflow), a1 = Float(s1.airflow)
            let m0: Float = s0.phase == .inhale ? 1 : 0
            let m1: Float = s1.phase == .inhale ? 1 : 0

            syn.render(into: scratchPtr, frames: frames,
                       airflow0: a0, airflow1: a1, mix0: m0, mix1: m1)
            amb.addInto(scratchPtr, frames: frames)   // continuous nature bed on top

            for buffer in abl {
                guard let dst = buffer.mData?.assumingMemoryBound(to: Float.self) else { continue }
                for i in 0..<frames { dst[i] = softClip(scratchPtr[i]) }
            }
            return noErr
        }

        engine.attach(node)
        engine.connect(node, to: engine.mainMixerNode, format: format)
        engine.mainMixerNode.outputVolume = masterVolume
        source = node
        engine.prepare()
        isAvailable = true
    }

    // MARK: control

    func start() {
        guard isAvailable else { return }
        do {
            try AVAudioSession.sharedInstance().setActive(true)
            if !engine.isRunning { try engine.start() }
            isRunning = true
        } catch {
            NSLog("Vesper engine start error: \(error.localizedDescription)")
        }
    }

    func stop() {
        engine.pause()
        isRunning = false
    }

    func setBreathLevel(_ level: Float) { synth.level = max(0, min(1, level)) }
    func setVoice(_ v: BreathVoice) { synth.setVoice(v) }
    func setAmbience(_ v: AmbienceVoice) { ambience.setVoice(v) }
    func setAmbienceLevel(_ l: Float) { ambience.level = max(0, min(1, l)) }
}
