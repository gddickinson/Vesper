//  HealthStore.swift
//  Vesper — optional Apple Health write-back. On session end Vesper can log a
//  Mindful Minutes (mindfulSession) sample, and on iOS 18+ a State of Mind
//  sample from the post-session mood check-in.
//
//  Designed to compile, link and run with NO HealthKit entitlement: every call
//  is guarded so it is a silent no-op when HealthKit is unavailable or the user
//  has not granted (or enabled) sharing. To actually persist data the app needs
//  the HealthKit capability + the two Info.plist usage strings — see
//  ios/docs/HEALTHKIT_SETUP.md. Until then nothing is written and nothing breaks.

import Foundation
import HealthKit

final class HealthStore {
    static let shared = HealthStore()

    /// HealthKit is only present on iPhone-class devices.
    static var isSupported: Bool { HKHealthStore.isHealthDataAvailable() }

    private let store = HKHealthStore()
    private var authorized = false          // set true once the user grants sharing

    private init() {}

    /// The set of sample types we'd like permission to write.
    private var shareTypes: Set<HKSampleType> {
        var types = Set<HKSampleType>()
        if let mindful = HKObjectType.categoryType(forIdentifier: .mindfulSession) {
            types.insert(mindful)
        }
        if #available(iOS 18.0, *) {
            types.insert(HKObjectType.stateOfMindType())
        }
        return types
    }

    /// Ask the user to allow Vesper to write to Health. Only call this when the
    /// "Sync to Apple Health" setting is turned on. Safe no-op if unsupported.
    func requestAuthorization(_ completion: ((Bool) -> Void)? = nil) {
        guard Self.isSupported else { completion?(false); return }
        let types = shareTypes
        guard !types.isEmpty else { completion?(false); return }
        store.requestAuthorization(toShare: types, read: []) { [weak self] ok, _ in
            self?.authorized = ok
            DispatchQueue.main.async { completion?(ok) }
        }
    }

    /// Log a Mindful Minutes session spanning [start, end]. No-op if too short,
    /// unsupported, or sharing is denied (the save simply fails silently).
    func saveMindfulMinutes(start: Date, end: Date) {
        guard Self.isSupported, end > start,
              let mindful = HKObjectType.categoryType(forIdentifier: .mindfulSession)
        else { return }
        // Don't write if the user hasn't authorised sharing for this type.
        guard store.authorizationStatus(for: mindful) == .sharingAuthorized else { return }
        let sample = HKCategorySample(type: mindful,
                                      value: HKCategoryValue.notApplicable.rawValue,
                                      start: start, end: end)
        store.save(sample) { _, _ in }     // best-effort; ignore the result
    }

    /// Log a State of Mind reading (iOS 18+) from a mood check-in. `valence` is
    /// −1 (unpleasant) … +1 (pleasant). Best-effort; silent on any failure.
    @available(iOS 18.0, *)
    func saveStateOfMind(valence: Double, at date: Date) {
        guard Self.isSupported else { return }
        let type = HKObjectType.stateOfMindType()
        guard store.authorizationStatus(for: type) == .sharingAuthorized else { return }
        let v = max(-1.0, min(1.0, valence))
        let sample = HKStateOfMind(date: date, kind: .momentaryEmotion,
                                   valence: v, labels: [], associations: [])
        store.save(sample) { _, _ in }
    }
}
