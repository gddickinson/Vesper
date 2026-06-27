//  Lectures.swift
//  Vesper — the sleep-lecture library, loaded from the bundled `lectures.json`
//  (337 lectures across 73 branches, exported from the desktop core by
//  ios/tools/export_content.py). Falls back to a small built-in set if the JSON
//  is missing, so the app always has something to narrate.

import Foundation

struct Lecture: Identifiable, Hashable {
    let title: String
    let branch: String
    let ambience: String
    let lines: [String]
    var id: String { title }
}

enum Lectures {
    /// All lectures, loaded once from the bundle (or the fallback).
    static let all: [Lecture] = load()
    /// Branch names in their authored order, with only those actually present.
    static let branches: [String] = orderedBranches(all)

    static func byTitle(_ t: String) -> Lecture? { index[t] }
    static func inBranch(_ b: String) -> [Lecture] { all.filter { $0.branch == b } }
    static func random() -> Lecture { all.randomElement() ?? fallback[0] }

    private static let index: [String: Lecture] =
        Dictionary(all.map { ($0.title, $0) }, uniquingKeysWith: { a, _ in a })

    // MARK: loading

    private struct File: Decodable {
        let lectures: [Item]
        let branches: [String]?
    }
    private struct Item: Decodable {
        let title: String
        let branch: String
        let ambience: String
        let lines: [String]
    }

    private static func load() -> [Lecture] {
        guard let url = Bundle.main.url(forResource: "lectures", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let file = try? JSONDecoder().decode(File.self, from: data),
              !file.lectures.isEmpty
        else { return fallback }
        return file.lectures.map {
            Lecture(title: $0.title, branch: $0.branch,
                    ambience: $0.ambience, lines: $0.lines)
        }
    }

    private static func orderedBranches(_ lectures: [Lecture]) -> [String] {
        var seen = Set<String>(); var out: [String] = []
        for l in lectures where !seen.contains(l.branch) {
            seen.insert(l.branch); out.append(l.branch)
        }
        return out
    }

    // MARK: fallback (used only if the bundled JSON is absent)

    static let fallback: [Lecture] = [
        Lecture(title: "The Tides", branch: "Earth & Sea", ambience: "Distant Surf", lines: [
            "Let everything grow calm, the way the shore calms between waves.",
            "Twice a day, all the seas of the world rise, and twice they fall.",
            "It is the moon that draws the water gently up toward itself.",
            "In and out. Rising and falling. The patient breath of the world.",
            "Let your breath fall in beside it now, unhurried, and let go.",
        ]),
        Lecture(title: "A Quiet Body Scan", branch: "The Body", ambience: "Brown Noise", lines: [
            "There is nothing to do now but rest, and follow these words.",
            "Let your forehead smooth, and the small muscles around your eyes rest.",
            "Feel your shoulders drop, a little further than you thought they could.",
            "Let your hips, your legs, your feet grow heavy and warm.",
            "Rest now. You are exactly where you need to be.",
        ]),
    ]
}
