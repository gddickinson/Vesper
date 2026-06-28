//  PracticeLog.swift
//  Vesper — a tiny practice history (the iOS analogue of the desktop store
//  history): sits, total minutes and a day streak, kept in UserDefaults.

import Foundation

struct PracticeEntry: Codable {
    let day: String        // "yyyy-MM-dd"
    let minutes: Double
    let at: Double         // epoch seconds
    var mood: Int? = nil   // 1…5, captured after the session (optional, back-compat)
}

enum PracticeLog {
    private static let key = "practiceLog"
    private static let d = UserDefaults.standard

    private static let dayFmt: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"; f.calendar = .current; f.locale = .current
        return f
    }()

    static var entries: [PracticeEntry] {
        guard let data = d.data(forKey: key),
              let list = try? JSONDecoder().decode([PracticeEntry].self, from: data)
        else { return [] }
        return list
    }

    static func log(minutes: Double) {
        guard minutes >= 1 else { return }
        let now = Date()
        var list = entries
        list.append(PracticeEntry(day: dayFmt.string(from: now),
                                  minutes: minutes, at: now.timeIntervalSince1970))
        if let data = try? JSONEncoder().encode(list) { d.set(data, forKey: key) }
    }

    /// Attach a mood (1…5) to the most recent session.
    static func setLastMood(_ mood: Int) {
        var list = entries
        guard !list.isEmpty else { return }
        list[list.count - 1].mood = max(1, min(5, mood))
        if let data = try? JSONEncoder().encode(list) { d.set(data, forKey: key) }
    }

    static var totalSessions: Int { entries.count }
    static var totalMinutes: Int { Int(entries.reduce(0) { $0 + $1.minutes }.rounded()) }

    /// Average post-session mood (1…5), or nil if none logged yet.
    static var averageMood: Double? {
        let m = entries.compactMap(\.mood)
        return m.isEmpty ? nil : Double(m.reduce(0, +)) / Double(m.count)
    }

    private static let cal = Calendar.current

    /// Minutes practised this calendar month.
    static var thisMonthMinutes: Int {
        let now = cal.dateComponents([.year, .month], from: Date())
        let total = entries.filter {
            let c = cal.dateComponents([.year, .month], from: Date(timeIntervalSince1970: $0.at))
            return c.year == now.year && c.month == now.month
        }.reduce(0.0) { $0 + $1.minutes }
        return Int(total.rounded())
    }

    /// Minutes per day for the last `days` days; index 0 = today, back in time.
    static func dailyMinutes(lastDays days: Int) -> [Double] {
        var out = [Double](repeating: 0, count: days)
        let today = cal.startOfDay(for: Date())
        for e in entries {
            let d = cal.startOfDay(for: Date(timeIntervalSince1970: e.at))
            if let ago = cal.dateComponents([.day], from: d, to: today).day, ago >= 0, ago < days {
                out[ago] += e.minutes
            }
        }
        return out
    }

    /// The part of day the user practises most often.
    static var bestTimeOfDay: String? {
        guard !entries.isEmpty else { return nil }
        var buckets = ["morning": 0, "afternoon": 0, "evening": 0, "night": 0]
        for e in entries {
            let h = cal.component(.hour, from: Date(timeIntervalSince1970: e.at))
            let key = (h < 6 || h >= 22) ? "night" : h < 12 ? "morning" : h < 18 ? "afternoon" : "evening"
            buckets[key, default: 0] += 1
        }
        return buckets.max { $0.value < $1.value }?.key
    }

    /// The most impressive milestone reached so far (for a gentle badge).
    static var badge: String? {
        if streak >= 30 { return "🔥 30-day streak" }
        if streak >= 7 { return "🔥 7-day streak" }
        if totalSessions >= 100 { return "✨ 100 sessions" }
        if totalMinutes >= 1000 { return "✨ 1,000 minutes" }
        if totalSessions >= 50 { return "✨ 50 sessions" }
        if totalSessions >= 25 { return "✨ 25 sessions" }
        if totalSessions >= 10 { return "✨ 10 sessions" }
        return nil
    }

    /// Consecutive days (including today/yesterday) with at least one session.
    static var streak: Int {
        let days = Set(entries.map(\.day))
        guard !days.isEmpty else { return 0 }
        let cal = Calendar.current
        var probe = Date()
        // allow the streak to "hold" if nothing yet today but yesterday counts
        if !days.contains(dayFmt.string(from: probe)),
           let y = cal.date(byAdding: .day, value: -1, to: probe) { probe = y }
        var count = 0
        while days.contains(dayFmt.string(from: probe)) {
            count += 1
            guard let prev = cal.date(byAdding: .day, value: -1, to: probe) else { break }
            probe = prev
        }
        return count
    }
}
