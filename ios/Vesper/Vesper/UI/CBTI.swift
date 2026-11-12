//  CBTI.swift
//  Vesper — the CBT-I "sleep window" engine (sleep restriction / consolidation).
//  From the sleep diary's recent sleep efficiency and a fixed wake time it
//  prescribes a time-in-bed window anchored to that wake time, with the standard
//  titration rule (SE≥90% → extend 15 min; ≤85% → tighten 15 min; else hold).
//  Pure, deterministic, testable. Follows the sleep-diary / sleep-window steps used
//  in CBT-I; a self-guided routine tool, not medical treatment. See [[vesper-sleep-science-upgrades]].

import Foundation

struct CBTIPlan {
    var ready: Bool             // ≥3 nights logged
    var nights: Int
    var avgEfficiencyPct: Int
    var avgSleepMins: Int
    var windowMins: Int         // prescribed time in bed
    var bedtimeMinutes: Int     // earliest-to-bed, minutes from midnight (0…1439)
    var wakeMinutes: Int
    var titration: String
    var window: String          // "11:40 PM – 6:30 AM"
}

enum CBTI {
    /// Stimulus-control + circadian rules — the behavioural core of CBT-I.
    static let rules: [String] = [
        "Keep the same wake time every day, even after a poor night — it anchors your body clock.",
        "Use the bed only for sleep. Do your winding-down somewhere else.",
        "Only go to bed when you feel sleepy, not just tired.",
        "If you're awake longer than about 20 minutes, get up, keep the lights low, and return when sleepy.",
        "Don't watch the clock — turn it away from view.",
        "Get bright light soon after waking; keep the evening dim and warm.",
    ]

    /// A rotating sleep-hygiene tip (deterministic by the day).
    static func tip(for date: Date) -> String {
        let tips = [
            "Caffeine has a ~5–6 hour half-life — try to finish coffee by early afternoon.",
            "A warm bath or shower an hour or two before bed is a pleasant way to wind down.",
            "Many people sleep more comfortably in a cool bedroom (around 18°C / 65°F).",
            "Many people find a late drink leaves the night more broken, even if it helps them doze off.",
            "Morning daylight helps set your body clock for the day ahead.",
            "A steady wake time, even at weekends, helps many people settle into a rhythm.",
            "If you can't sleep, getting up beats lying there frustrated — it keeps bed a cue for sleep.",
            "Daytime exercise can help you feel ready for sleep — finish vigorous workouts a few hours before bed.",
            "A short to-do list before bed can help you set tomorrow's worries down.",
            "Naps after about 3 pm can borrow from tonight's sleep pressure — keep them early and short.",
        ]
        let day = Calendar.current.ordinality(of: .day, in: .year, for: date) ?? 1
        return tips[(day - 1) % tips.count]
    }

    /// Build the plan from the diary + the user's fixed wake time (minutes from midnight).
    static func plan(wakeMinutes: Int, nights: Int = 7) -> CBTIPlan {
        let n = SleepDiary.recent(nights).count
        let eff = SleepDiary.avgEfficiency(nights)
        let tst = SleepDiary.avgTotalSleep(nights)
        let effPct = Int((eff * 100).rounded())

        // Sleep restriction: time in bed ≈ average total sleep, floored at 5 h,
        // capped at 9 h, so the bed re-associates with consolidated sleep.
        let windowMins = max(300, min(540, Int(tst.rounded())))
        let bed = ((wakeMinutes - windowMins) % 1440 + 1440) % 1440

        let titration: String
        if n < 3 {
            titration = "Log a few nights and your personalised window will appear here."
        } else if effPct >= 90 {
            titration = "Your sleep is efficient — you can move your earliest bedtime 15 minutes earlier."
        } else if effPct <= 85 {
            titration = "Tighten the window: move your earliest bedtime 15 minutes later to build sleep pressure."
        } else {
            titration = "Hold this window for now — you're on track."
        }

        return CBTIPlan(
            ready: n >= 3, nights: n, avgEfficiencyPct: effPct,
            avgSleepMins: Int(tst.rounded()), windowMins: windowMins,
            bedtimeMinutes: bed, wakeMinutes: wakeMinutes,
            titration: titration,
            window: "\(clock(bed)) – \(clock(wakeMinutes))")
    }

    /// A 0–100 sleep-regularity score from the consistency of bed + wake times of
    /// day over recent nights (circular mean absolute deviation, mapped to 0–100).
    /// Sleep regularity predicts mortality better than duration (UK Biobank, 2024).
    /// nil if fewer than 3 nights are logged.
    static func regularity(nights: Int = 7) -> Int? {
        let r = SleepDiary.recent(nights)
        guard r.count >= 3 else { return nil }
        func tod(_ d: Date) -> Double {
            let c = Calendar.current.dateComponents([.hour, .minute], from: d)
            return Double((c.hour ?? 0) * 60 + (c.minute ?? 0))
        }
        func circMAD(_ mins: [Double]) -> Double {       // mean abs deviation, minutes (circular)
            let ang = mins.map { $0 / 1440 * 2 * Double.pi }
            let mean = atan2(ang.map(sin).reduce(0, +), ang.map(cos).reduce(0, +))
            let dev = ang.map { a -> Double in
                var d = a - mean
                while d > .pi { d -= 2 * .pi }
                while d < -Double.pi { d += 2 * .pi }
                return abs(d)
            }
            return dev.reduce(0, +) / Double(dev.count) / (2 * Double.pi) * 1440
        }
        let mad = (circMAD(r.map { tod($0.finalWakeAt) }) + circMAD(r.map { tod($0.inBedAt) })) / 2
        return Int(max(0, min(100, 100 - mad * 1.4)).rounded())
    }

    /// minutes-from-midnight ↔ a Date today (for the wake-time DatePicker).
    static func dateFrom(_ minutes: Int) -> Date {
        Calendar.current.date(bySettingHour: minutes / 60, minute: minutes % 60,
                              second: 0, of: Date()) ?? Date()
    }
    static func minutesFrom(_ date: Date) -> Int {
        let c = Calendar.current.dateComponents([.hour, .minute], from: date)
        return (c.hour ?? 6) * 60 + (c.minute ?? 30)
    }

    /// minutes-from-midnight → "11:40 PM".
    static func clock(_ m: Int) -> String {
        let mm = ((m % 1440) + 1440) % 1440
        let h24 = mm / 60, min = mm % 60
        let ampm = h24 < 12 ? "AM" : "PM"
        var h12 = h24 % 12; if h12 == 0 { h12 = 12 }
        return String(format: "%d:%02d %@", h12, min, ampm)
    }
}
