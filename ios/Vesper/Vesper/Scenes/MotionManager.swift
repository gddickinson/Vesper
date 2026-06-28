//  MotionManager.swift
//  Vesper — a tiny CoreMotion source for gentle tilt parallax on the scene
//  backdrops. Pull-based: the device-motion handler smooths an offset on the
//  main thread; the backdrop's TimelineView reads `offset` each frame (no
//  SwiftUI observation, so it never forces extra view rebuilds). Degrades to a
//  zero offset where device motion is unavailable (e.g. the simulator).

import CoreMotion
import CoreGraphics

final class MotionManager {
    static let shared = MotionManager()

    /// Smoothed parallax offset in points; read on the main thread each frame.
    private(set) var offset: CGSize = .zero

    private let mgr = CMMotionManager()
    private var running = false

    private init() {}

    func start() {
        guard !running, mgr.isDeviceMotionAvailable else { return }
        running = true
        mgr.deviceMotionUpdateInterval = 1.0 / 30.0
        mgr.startDeviceMotionUpdates(to: .main) { [weak self] m, _ in
            guard let self, let m else { return }
            let maxShift = 16.0
            let dx = CGFloat(m.attitude.roll)  * maxShift
            let dy = CGFloat(m.attitude.pitch) * maxShift
            // ease toward the target so the parallax glides rather than jitters
            self.offset = CGSize(width: self.offset.width  * 0.85 + dx * 0.15,
                                 height: self.offset.height * 0.85 + dy * 0.15)
        }
    }

    func stop() {
        guard running else { return }
        mgr.stopDeviceMotionUpdates()
        running = false
        offset = .zero
    }
}
