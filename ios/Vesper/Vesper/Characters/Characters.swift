//  Characters.swift
//  Vesper — the character registry (the iOS analogue of characters.py). Add a
//  character → make a CharacterDrawer and list it here.

import Foundation

enum Characters {
    static let all: [CharacterDrawer] = [
        CatChar(), DogChar(), BunnyChar(), BearChar(), PandaChar(), FoxChar(),
        OwlChar(), PenguinChar(), FrogChar(), SlothChar(), MouseChar(), LionChar(),
    ]
    static let names: [String] = all.map(\.name)
    static let byName: [String: CharacterDrawer] =
        Dictionary(all.map { ($0.name, $0) }, uniquingKeysWith: { a, _ in a })

    /// The sleepy mascot leads, fitting for a sleep app.
    static let `default` = "Sloth"

    static func get(_ name: String) -> CharacterDrawer { byName[name] ?? all[0] }
}
