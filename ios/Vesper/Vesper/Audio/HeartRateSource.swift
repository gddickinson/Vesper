//  HeartRateSource.swift
//  Vesper — feeds heart-rate samples to the CoherenceModel. Two modes:
//   • real: a guarded HealthKit live-HR stream (HKAnchoredObjectQuery on
//     .heartRate). Needs the HealthKit READ entitlement — without it the auth
//     request just fails and nothing streams (no crash). See HEALTHKIT_SETUP.md.
//   • demo: a synthetic tachogram driven by the breath (respiratory sinus
//     arrhythmia — HR rises on the in-breath, falls on the out-breath) so the
//     coherence ring is fully demonstrable on the simulator with no sensor.

import Foundation
import HealthKit

final class HeartRateSource {
    private let store = HKHealthStore()
    private var query: HKAnchoredObjectQuery?
    private(set) var streamingReal = false

    /// A believable instantaneous HR (bpm) for `breath` (0…1 lung volume) at
    /// time `t` — a slow respiratory-sinus-arrhythmia swing plus light noise.
    static func demoHR(t: Double, breath: Double) -> Double {
        let rsa = (breath - 0.5) * 2                 // -1…1, tracks the breath
        let noise = 0.6 * sin(t * 1.7) + 0.3 * sin(t * 0.9)
        return 62 + 6 * rsa + noise
    }

    /// Request HealthKit read access and, if granted, stream live HR into `feed`
    /// (bpm, time-seconds). No-op without the read entitlement / on the sim.
    func startReal(feed: @escaping (Double, Double) -> Void) {
        guard HKHealthStore.isHealthDataAvailable(),
              let hrType = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }
        store.requestAuthorization(toShare: [], read: [hrType]) { [weak self] ok, _ in
            guard ok, let self else { return }
            let unit = HKUnit.count().unitDivided(by: .minute())
            let handler: (HKAnchoredObjectQuery, [HKSample]?, [HKDeletedObject]?, HKQueryAnchor?, Error?) -> Void
                = { _, samples, _, _, _ in
                    guard let qs = samples as? [HKQuantitySample] else { return }
                    for s in qs {
                        let bpm = s.quantity.doubleValue(for: unit)
                        let t = s.startDate.timeIntervalSinceReferenceDate
                        DispatchQueue.main.async { feed(bpm, t) }
                    }
                }
            let q = HKAnchoredObjectQuery(type: hrType, predicate: nil, anchor: nil,
                                          limit: HKObjectQueryNoLimit, resultsHandler: handler)
            q.updateHandler = handler
            DispatchQueue.main.async {
                self.query = q
                self.streamingReal = true
                self.store.execute(q)
            }
        }
    }

    func stop() {
        if let q = query { store.stop(q) }
        query = nil
        streamingReal = false
    }
}
