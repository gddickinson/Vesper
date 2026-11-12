//  SleepDiary.swift
//  Vesper — a CBT-I sleep diary. Each morning you log last night; from the last
//  ~7 nights we compute Time-In-Bed (TIB), Total Sleep Time (TST) and Sleep
//  Efficiency (SE = TST/TIB), which drive the sleep-window (sleep-restriction)
//  prescription in CBTI.swift. Persisted as JSON in UserDefaults (mirrors
//  CustomPatterns). The sleep diary + efficiency-driven window follow the steps
//  used in CBT-I (a self-guided routine tool, not medical treatment). See [[vesper-sleep-science-upgrades]].

import Foundation

struct DiaryEntry: Codable, Identifiable {
    var day: String            // yyyy-MM-dd (the morning you woke)
    var inBedAt: Date          // got into bed
    var triedAt: Date          // turned out the light / tried to sleep
    var sleepOnsetMins: Int    // SOL — minutes to fall asleep
    var awakenings: Int        // number of night wakings
    var wasoMins: Int          // WASO — minutes awake during the night
    var finalWakeAt: Date      // final awakening
    var outOfBedAt: Date       // got out of bed
    var quality: Int           // 1…5 subjective rating
    var note: String

    var id: String { day }

    /// Minutes between two times-of-day, wrapping past midnight (e.g. 23:00→07:00).
    private static func span(_ a: Date, _ b: Date) -> Double {
        var iv = b.timeIntervalSince(a) / 60
        if iv < 0 { iv += 24 * 60 }
        return max(0, iv)
    }

    var timeInBed: Double { Self.span(inBedAt, outOfBedAt) }                 // TIB
    var totalSleep: Double { max(0, timeInBed - Double(sleepOnsetMins) - Double(wasoMins)) } // TST
    var efficiency: Double { timeInBed > 0 ? min(1, totalSleep / timeInBed) : 0 }
}

enum SleepDiary {
    private static let key = "sleepDiary"
    private static let d = UserDefaults.standard

    static var all: [DiaryEntry] {
        guard let data = d.data(forKey: key),
              let list = try? JSONDecoder().decode([DiaryEntry].self, from: data)
        else { return [] }
        return list.sorted { $0.day < $1.day }
    }

    static func recent(_ n: Int) -> [DiaryEntry] { Array(all.suffix(n)) }
    static var count: Int { all.count }

    /// Add or replace the entry for its `day`.
    static func save(_ e: DiaryEntry) {
        var list = all.filter { $0.day != e.day }
        list.append(e)
        write(list.sorted { $0.day < $1.day })
    }

    static func delete(_ day: String) { write(all.filter { $0.day != day }) }

    private static func write(_ list: [DiaryEntry]) {
        if let data = try? JSONEncoder().encode(list) { d.set(data, forKey: key) }
    }

    // MARK: aggregates (over the most recent `n` nights)

    /// Mean sleep efficiency 0…1 (0 if no entries).
    static func avgEfficiency(_ n: Int = 7) -> Double {
        let r = recent(n); guard !r.isEmpty else { return 0 }
        return r.map(\.efficiency).reduce(0, +) / Double(r.count)
    }

    /// Mean total sleep time in minutes (0 if no entries).
    static func avgTotalSleep(_ n: Int = 7) -> Double {
        let r = recent(n); guard !r.isEmpty else { return 0 }
        return r.map(\.totalSleep).reduce(0, +) / Double(r.count)
    }

    /// Today's yyyy-MM-dd for a fresh entry.
    static func today(_ date: Date) -> String {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; f.locale = Locale(identifier: "en_US_POSIX")
        return f.string(from: date)
    }
}
