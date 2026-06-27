//  NeuralTTS.swift
//  Vesper — the neural-TTS plug-point + Kokoro model downloader.
//
//  The actual on-device inference (onnxruntime / sherpa-onnx running the Kokoro
//  model) is provided by a `NeuralTTSBackend` that is registered at runtime once
//  the ML package is added to the project — see docs/KOKORO_IOS.md. Until then
//  `NeuralTTS.backend` is nil and the app cleanly falls back to the system /
//  Personal voices. This keeps Vesper building with **no ML dependency**.

import Foundation

/// Synthesizes one line of text to mono float PCM. Implemented by the Kokoro
/// inference engine (added separately); returns nil if it can't synthesize.
protocol NeuralTTSBackend: AnyObject {
    func synthesize(text: String, voiceID: String, speed: Float) -> (samples: [Float], sampleRate: Double)?
}

enum NeuralTTS {
    /// The active backend. Register one at launch after adding the ML package:
    ///   NeuralTTS.backend = KokoroOnnxBackend(model: KokoroModel.modelPath,
    ///                                         voices: KokoroModel.voicesPath)
    static var backend: NeuralTTSBackend?

    /// True when a backend is registered *and* the model is downloaded.
    static var isReady: Bool { backend != nil && KokoroModel.isDownloaded }

    /// Whether neural voices can be offered at all (model present; backend may
    /// still be pending — the UI shows "needs setup" in that case).
    static var modelPresent: Bool { KokoroModel.isDownloaded }
}

/// Downloads the Kokoro model + voices into Application Support, with progress.
final class KokoroDownloader: NSObject, ObservableObject, URLSessionDownloadDelegate {
    enum State: Equatable { case idle, downloading, ready, failed(String) }

    @Published var state: State
    @Published var progress: Double = 0      // 0…1 across both files

    private var session: URLSession?

    override init() {
        state = KokoroModel.isDownloaded ? .ready : .idle
        super.init()
    }

    func start() {
        if KokoroModel.isDownloaded { state = .ready; return }
        guard state != .downloading else { return }
        state = .downloading
        progress = 0
        session = URLSession(configuration: .default, delegate: self, delegateQueue: nil)
        fetch(KokoroModel.modelURL, tag: "model")
    }

    func deleteModel() {
        KokoroModel.removeDownload()
        progress = 0
        state = .idle
    }

    private func fetch(_ url: URL, tag: String) {
        let task = session?.downloadTask(with: url)
        task?.taskDescription = tag
        task?.resume()
    }

    // MARK: URLSessionDownloadDelegate

    func urlSession(_ s: URLSession, downloadTask t: URLSessionDownloadTask,
                    didWriteData _: Int64, totalBytesWritten w: Int64,
                    totalBytesExpectedToWrite e: Int64) {
        guard e > 0 else { return }
        let frac = Double(w) / Double(e)
        let base = t.taskDescription == "model" ? 0.0 : 0.5   // two equal halves
        DispatchQueue.main.async { self.progress = base + frac * 0.5 }
    }

    func urlSession(_ s: URLSession, downloadTask t: URLSessionDownloadTask,
                    didFinishDownloadingTo location: URL) {
        let dest = t.taskDescription == "model" ? KokoroModel.modelPath : KokoroModel.voicesPath
        try? FileManager.default.removeItem(at: dest)
        do {
            try FileManager.default.moveItem(at: location, to: dest)
        } catch {
            DispatchQueue.main.async { self.state = .failed("Couldn't save \(t.taskDescription ?? "file").") }
            return
        }
        if t.taskDescription == "model" {
            fetch(KokoroModel.voicesURL, tag: "voices")
        } else {
            DispatchQueue.main.async { self.progress = 1; self.state = .ready }
        }
    }

    func urlSession(_ s: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error {
            DispatchQueue.main.async {
                if case .ready = self.state { return }
                self.state = .failed(error.localizedDescription)
            }
        }
    }
}
