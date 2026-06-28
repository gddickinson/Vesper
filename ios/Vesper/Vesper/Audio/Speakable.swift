//  Speakable.swift
//  Vesper — spoken-text sanitiser (mirrors the desktop `narration.speakable`).
//
//  Folds/strips the characters a TTS engine would otherwise read aloud by NAME
//  ("underscore", "asterisk", "em dash"…) or mispronounce, so the narrator
//  speaks the words — not the punctuation. Applied ONLY to the text sent to the
//  engine; the on-screen captions keep the original. Pure + testable.

import Foundation

enum Speakable {
    /// Smart-punctuation / non-ASCII folded so the engine speaks words.
    private static let fold: [Character: String] = [
        "\u{2014}": " -- ", "\u{2013}": "-", "\u{2012}": "-", "\u{2015}": " -- ",
        "\u{2018}": "'", "\u{2019}": "'", "\u{201A}": "'", "\u{201B}": "'",
        "\u{201C}": "\"", "\u{201D}": "\"", "\u{201E}": "\"", "\u{00AB}": "\"", "\u{00BB}": "\"",
        "\u{2026}": "...", "\u{00A0}": " ", "\u{2022}": " ", "\u{00B7}": " ",
    ]
    /// Symbols a TTS engine reads as their name (markup, footnote stars, diagram
    /// glyphs) — dropped from the spoken text (never the read-along view).
    private static let drop = Set("_*|\\`~^#=<>{}+/@")

    static func clean(_ text: String) -> String {
        var out = ""
        out.reserveCapacity(text.count)
        for ch in text {
            if let f = fold[ch] { out += f }
            else if ch == "[" { out += "(" }
            else if ch == "]" { out += ")" }
            else if ch == "&" { out += " and " }
            else if drop.contains(ch) { out += " " }
            else { out.append(ch) }
        }
        // A long ASCII rule -> a single pause; then squeeze whitespace.
        out = out.replacingOccurrences(of: "-{3,}", with: " -- ",
                                       options: .regularExpression)
        out = out.replacingOccurrences(of: "\\s{2,}", with: " ",
                                       options: .regularExpression)
        return out.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
