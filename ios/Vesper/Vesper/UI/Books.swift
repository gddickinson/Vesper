//  Books.swift
//  Vesper — short readable texts for the bedtime Reader: a couple of bundled
//  public-domain fables plus any text you paste in, with a per-title resume
//  point. Reading is narrated by the same wind-down voice as the stories.

import Foundation

struct ReadText: Codable, Identifiable {
    var title: String
    var content: String
    var id: String { title }
}

enum Books {
    private static let key = "readTexts"
    private static let d = UserDefaults.standard

    /// Bundled public-domain samples (Aesop; plain ASCII).
    static let samples: [ReadText] = [
        ReadText(title: "The North Wind and the Sun",
                 content: "The North Wind and the Sun disputed as to which was the more powerful, and agreed that he should be declared the victor who could first strip a wayfaring man of his clothes. The North Wind first tried his power, and blew with all his might. But the keener his blasts, the closer the traveller wrapped his cloak around him, until at last, the North Wind gave up the attempt. Then the Sun shone out warmly, and the traveller, overcome with the heat, soon took off his cloak. And so the North Wind was obliged to confess that the Sun was the stronger of the two. Kindness, gentle and warm, can do what force cannot."),
        ReadText(title: "The Tortoise and the Hare",
                 content: "A Hare was making fun of the Tortoise one day for being so slow. Do you ever get anywhere, he asked, with a mocking laugh. Yes, replied the Tortoise, and I get there sooner than you think. I will run you a race and prove it. The Hare was much amused at the idea of running a race with the Tortoise, but for the fun of the thing he agreed. So the Fox, who had consented to act as judge, marked the distance and started the runners off. The Hare was soon far out of sight, and to make the Tortoise feel very deeply how ridiculous it was for him to try a race with a Hare, he lay down beside the course to take a nap until the Tortoise should catch up. The Tortoise meanwhile kept going slowly but steadily, and after a time passed the place where the Hare was sleeping. But the Hare slept on very peacefully, and when at last he did wake up, the Tortoise was near the goal. The Hare now ran his swiftest, but he could not overtake the Tortoise in time. Slow and steady wins the race."),
    ]

    static var userTexts: [ReadText] {
        guard let data = d.data(forKey: key),
              let list = try? JSONDecoder().decode([ReadText].self, from: data)
        else { return [] }
        return list
    }

    static var all: [ReadText] { samples + userTexts }
    static func byTitle(_ t: String) -> ReadText? { all.first { $0.title == t } }

    static func add(title: String, content: String) {
        var list = userTexts.filter { $0.title != title }
        list.append(ReadText(title: title, content: content))
        if let data = try? JSONEncoder().encode(list) { d.set(data, forKey: key) }
    }

    static func deleteUser(_ title: String) {
        let list = userTexts.filter { $0.title != title }
        if let data = try? JSONEncoder().encode(list) { d.set(data, forKey: key) }
    }

    // Per-title resume sentence index.
    static func resume(_ title: String) -> Int { d.integer(forKey: "readResume." + title) }
    static func setResume(_ title: String, _ index: Int) { d.set(index, forKey: "readResume." + title) }

    /// Split text into spoken sentences (on . ! ?), trimmed, non-empty.
    static func sentences(_ content: String) -> [String] {
        var out: [String] = []
        var cur = ""
        for ch in content {
            cur.append(ch)
            if ch == "." || ch == "!" || ch == "?" {
                let s = cur.trimmingCharacters(in: .whitespacesAndNewlines)
                if !s.isEmpty { out.append(s) }
                cur = ""
            }
        }
        let tail = cur.trimmingCharacters(in: .whitespacesAndNewlines)
        if !tail.isEmpty { out.append(tail) }
        return out
    }
}
