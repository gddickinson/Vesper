//  Bell.swift
//  Vesper — a soft mindfulness bell (singing-bowl-like), for the Meditate
//  interval cue and the gentle session-end chime.
//
//  Synthesised once into an in-memory WAV and played via AVAudioPlayer, which
//  mixes over the breath bed through the shared `.playback` session and keeps
//  working with the screen locked. No asset files needed.

import AVFoundation

final class Bell {
    private var player: AVAudioPlayer?

    init() {
        player = try? AVAudioPlayer(data: Bell.render())
        player?.volume = 0.6
        player?.prepareToPlay()
    }

    /// Strike the bell from the start.
    func ring() {
        guard let p = player else { return }
        p.currentTime = 0
        p.play()
    }

    // MARK: synthesis

    /// A ~3s soft bowl: a few inharmonic partials with a slow exponential decay
    /// and a gentle attack, rendered to 16-bit mono WAV bytes.
    private static func render(sr: Double = 44100, seconds: Double = 3.0) -> Data {
        let n = Int(sr * seconds)
        let f0 = 528.0
        // Inharmonic partials (ratio, relative amplitude, decay rate).
        let partials: [(Double, Double, Double)] = [
            (1.00, 1.00, 1.6), (2.74, 0.55, 2.3), (5.41, 0.30, 3.4), (8.93, 0.12, 4.8),
        ]
        var samples = [Float](repeating: 0, count: n)
        for i in 0..<n {
            let t = Double(i) / sr
            let attack = min(1.0, t / 0.006)              // 6 ms soft attack
            var s = 0.0
            for (ratio, amp, decay) in partials {
                s += amp * exp(-decay * t) * sin(2 * .pi * f0 * ratio * t)
            }
            samples[i] = Float(0.5 * attack * s)
        }
        // Normalise to a comfortable peak.
        let peak = samples.map { abs($0) }.max() ?? 1
        if peak > 0 { let g = Float(0.85) / peak; for i in 0..<n { samples[i] *= g } }
        return wav(samples, sr: Int(sr))
    }

    /// Wrap mono float samples as a 16-bit PCM WAV in memory.
    private static func wav(_ samples: [Float], sr: Int) -> Data {
        var d = Data()
        let bytesPerSample = 2, channels = 1
        let dataBytes = samples.count * bytesPerSample
        func u32(_ v: UInt32) { var x = v.littleEndian; withUnsafeBytes(of: &x) { d.append(contentsOf: $0) } }
        func u16(_ v: UInt16) { var x = v.littleEndian; withUnsafeBytes(of: &x) { d.append(contentsOf: $0) } }
        d.append(contentsOf: Array("RIFF".utf8)); u32(UInt32(36 + dataBytes))
        d.append(contentsOf: Array("WAVE".utf8))
        d.append(contentsOf: Array("fmt ".utf8)); u32(16); u16(1); u16(UInt16(channels))
        u32(UInt32(sr)); u32(UInt32(sr * channels * bytesPerSample))
        u16(UInt16(channels * bytesPerSample)); u16(16)
        d.append(contentsOf: Array("data".utf8)); u32(UInt32(dataBytes))
        for s in samples {
            let clamped = max(-1, min(1, s))
            u16(UInt16(bitPattern: Int16(clamped * 32767)))
        }
        return d
    }
}
