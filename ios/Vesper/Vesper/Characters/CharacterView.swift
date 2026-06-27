//  CharacterView.swift
//  Vesper — renders a chosen cartoon character with a SwiftUI Canvas, breathing
//  with the breath state and moving its mouth to the narration (lip-sync proxy).

import SwiftUI

struct CharacterView: View {
    let character: String
    let state: BreathState
    let animT: Double
    let mouth: Double

    var body: some View {
        Canvas { context, size in
            let hue = Theme.phaseColor(state.phase, state.progress)
            let a = CharAnim.make(state, t: animT, mouth: mouth, hue: hue)
            // A struct copy still draws into the shared backing store.
            var ctx = context
            Characters.get(character).draw(&ctx, size, a)
        }
        .allowsHitTesting(false)
    }
}
