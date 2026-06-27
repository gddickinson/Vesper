//  PracticeLog.swift
//  Vesper — a tiny practice history (the iOS analogue of the desktop store
//  history): sits, total minutes and a day streak, kept in UserDefaults.

import Foundation

struct PracticeEntry: Codable {
    let day: String        // "yyyy-MM-dd"
    let minutes: Double
    let at: Double         // epoch seconds
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

    static var totalSessions: Int { entries.count }
    static var totalMinutes: Int { Int(entries.reduce(0) { $0 + $1.minutes }.rounded()) }

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
