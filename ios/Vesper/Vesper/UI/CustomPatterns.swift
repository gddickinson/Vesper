//  CustomPatterns.swift
//  Vesper — user-created breathing patterns, saved as JSON in UserDefaults and
//  merged into the Pattern picker alongside the built-in presets.

import Foundation

struct CustomPattern: Codable, Identifiable {
    var name: String
    var inhale: Double
    var holdFull: Double
    var exhale: Double
    var holdEmpty: Double
    var id: String { name }

    var asBreathPattern: BreathPattern {
        BreathPattern(name, inhale, holdFull, exhale, holdEmpty, "Your custom pattern.")
    }
}

enum CustomPatterns {
    private static let key = "customPatterns"
    private static let d = UserDefaults.standard

    static var all: [CustomPattern] {
        guard let data = d.data(forKey: key),
              let list = try? JSONDecoder().decode([CustomPattern].self, from: data)
        else { return [] }
        return list
    }

    static var names: [String] { all.map(\.name) }

    static func byName(_ n: String) -> BreathPattern? {
        all.first { $0.name == n }?.asBreathPattern
    }

    /// Add or replace (by name).
    static func save(_ p: CustomPattern) {
        var list = all.filter { $0.name != p.name }
        list.append(p)
        write(list)
    }

    static func delete(_ name: String) {
        write(all.filter { $0.name != name })
    }

    private static func write(_ list: [CustomPattern]) {
        if let data = try? JSONEncoder().encode(list) { d.set(data, forKey: key) }
    }
}
