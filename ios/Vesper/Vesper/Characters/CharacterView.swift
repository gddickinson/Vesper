//  CharacterView.swift
//  Vesper — renders a chosen cartoon character with a SwiftUI Canvas, breathing
//  with the breath state and moving its mouth to the narration (lip-sync proxy).

import SwiftUI

struct CharacterView: View {
    let character: String
    let state: BreathState
    let animT: Double
    let mouth: Double
    var drowsy: Double = 0      // 0..1 Sleep wind-down → sleepy eyes + "z"s

    var body: some View {
        Canvas { context, size in
            let hue = Theme.phaseColor(state.phase, state.progress)
            let a = CharAnim.make(state, t: animT, mouth: mouth, hue: hue, drowsy: drowsy)
            // A struct copy still draws into the shared backing store.
            var ctx = context
            // Ground the character with a soft contact shadow (drawn upright)…
            CharKit.contactShadow(&ctx, size, a)
            // …then give the body a gentle idle head-tilt so it feels alive.
            let cx = size.width / 2, cy = size.height * 0.5
            ctx.translateBy(x: cx, y: cy)
            ctx.rotate(by: .radians(sin(animT * 0.3) * 0.022 + a.sway * 0.012))
            ctx.translateBy(x: -cx, y: -cy)
            Characters.get(character).draw(&ctx, size, a)
            // drifting "z" sleep cue when the companion is genuinely drowsy
            if drowsy > 0.6 {
                var zc = context
                for i in 0..<3 {
                    let ph = (animT * 0.45 + Double(i) * 0.34).truncatingRemainder(dividingBy: 1)
                    let zx = size.width * 0.62 + CGFloat(ph) * size.width * 0.05
                    let zy = size.height * 0.33 - CGFloat(ph) * size.height * 0.13
                    let op = (1 - ph) * min(1, (drowsy - 0.6) / 0.4)
                    let txt = Text("z").font(.system(size: 13 + CGFloat(i) * 4,
                                                     weight: .bold, design: .rounded))
                        .foregroundColor(Theme.text.opacity(op * 0.6))
                    zc.draw(zc.resolve(txt), at: CGPoint(x: zx, y: zy))
                }
            }
        }
        .allowsHitTesting(false)
    }
}
