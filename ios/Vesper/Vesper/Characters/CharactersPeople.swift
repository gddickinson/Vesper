//  CharactersPeople.swift
//  Vesper — the people cast (Woman, Man, Skull). Each is a small
//  CharacterDrawer built from the shared CharKit primitives: an aura, a warm
//  (or bone) round head, framing hair drawn behind the head, then the face.
//  Gentle, friendly chibi style; breath-animated. Add a character by adding a
//  struct and listing it in Characters.all.

import SwiftUI

private func col(_ r: Double, _ g: Double, _ b: Double) -> Color {
    Color(red: r, green: g, blue: b)
}

// Shared warm chibi skin tones.
private let skinLight = col(0.99, 0.83, 0.70)
private let skinDark  = col(0.88, 0.66, 0.54)
private let skinLine  = col(0.80, 0.58, 0.47)

struct WomanChar: CharacterDrawer {
    let name = "Woman"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let hair = col(0.30, 0.21, 0.18), hairLo = col(0.22, 0.15, 0.13)

        // HAIR behind the head: a larger rounded shape that peeks at the sides
        // and falls past the jaw, framing the face.
        ctx.fill(Path { p in
            p.addEllipse(in: CGRect(x: c.x - r*1.18, y: c.y - r*1.02,
                                    width: r*2.36, height: r*2.5))
        }, with: .radialGradient(
            Gradient(colors: [hair, hairLo]),
            center: CGPoint(x: c.x, y: c.y - r*0.2),
            startRadius: r*0.3, endRadius: r*1.5))

        // Warm round head.
        CharKit.head(&ctx, c, r, skinLight, skinDark)

        // Soft fringe / bangs across the top of the forehead, dipping a little
        // in the centre.
        ctx.fill(Path { p in
            p.move(to: CGPoint(x: c.x - r*0.98, y: c.y - r*0.20))
            p.addQuadCurve(to: CGPoint(x: c.x + r*0.98, y: c.y - r*0.20),
                           control: CGPoint(x: c.x, y: c.y - r*1.34))
            p.addLine(to: CGPoint(x: c.x + r*0.62, y: c.y - r*0.34))
            p.addQuadCurve(to: CGPoint(x: c.x - r*0.62, y: c.y - r*0.34),
                           control: CGPoint(x: c.x, y: c.y - r*0.02))
            p.closeSubpath()
        }, with: .color(hair))
        // a soft sheen on the fringe
        var sheen = Path()
        sheen.move(to: CGPoint(x: c.x - r*0.5, y: c.y - r*0.78))
        sheen.addQuadCurve(to: CGPoint(x: c.x + r*0.3, y: c.y - r*0.86),
                           control: CGPoint(x: c.x - r*0.1, y: c.y - r*1.04))
        ctx.stroke(sheen, with: .color(.white.opacity(0.16)), lineWidth: max(1, r*0.05))

        // Eyes.
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.34, r*0.15, a)
        // Soft eyelashes at the outer corners (only when the eyes are open).
        if a.blink < 0.55 {
            for side in [-1.0, 1.0] {
                let ex = c.x + CGFloat(side) * r*0.34
                var p = Path()
                p.move(to: CGPoint(x: ex + CGFloat(side)*r*0.10, y: c.y - r*0.15))
                p.addLine(to: CGPoint(x: ex + CGFloat(side)*r*0.22, y: c.y - r*0.21))
                ctx.stroke(p, with: .color(hairLo), lineWidth: max(1, r*0.03))
            }
        }
        // Tiny nose (a short line).
        var nose = Path()
        nose.move(to: CGPoint(x: c.x, y: c.y + r*0.06))
        nose.addLine(to: CGPoint(x: c.x, y: c.y + r*0.15))
        ctx.stroke(nose, with: .color(skinLine), lineWidth: max(1, r*0.03))

        CharKit.blush(&ctx, c.x, c.y + r*0.26, r*0.6, r*0.16, .pink)
        CharKit.mouth(&ctx, c.x, c.y + r*0.42, r*0.16, a)
        return (c, r)
    }
}

struct ManChar: CharacterDrawer {
    let name = "Man"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let hair = col(0.27, 0.20, 0.17), hairLo = col(0.19, 0.14, 0.12)

        // HAIR behind the head: a low rim peeking above and around the crown,
        // so the cap reads as real hair, not a hat.
        ctx.fill(Path { p in
            p.addEllipse(in: CGRect(x: c.x - r*1.04, y: c.y - r*1.10,
                                    width: r*2.08, height: r*1.9))
        }, with: .color(hairLo))

        // Warm round head.
        CharKit.head(&ctx, c, r, skinLight, skinDark)

        // Short hair: a neat cap across the top, hairline arcing up over the
        // forehead.
        ctx.fill(Path { p in
            p.move(to: CGPoint(x: c.x - r*0.93, y: c.y - r*0.16))
            p.addQuadCurve(to: CGPoint(x: c.x + r*0.93, y: c.y - r*0.16),
                           control: CGPoint(x: c.x, y: c.y - r*1.34))
            p.addQuadCurve(to: CGPoint(x: c.x - r*0.93, y: c.y - r*0.16),
                           control: CGPoint(x: c.x, y: c.y - r*0.66))
            p.closeSubpath()
        }, with: .color(hair))

        // Simple eyebrows.
        for side in [-1.0, 1.0] {
            let bx = c.x + CGFloat(side) * r*0.34
            var p = Path()
            p.move(to: CGPoint(x: bx - r*0.16, y: c.y - r*0.25))
            p.addQuadCurve(to: CGPoint(x: bx + r*0.16, y: c.y - r*0.25),
                           control: CGPoint(x: bx, y: c.y - r*0.33))
            ctx.stroke(p, with: .color(hairLo), lineWidth: max(1.4, r*0.05))
        }

        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.34, r*0.15, a)
        // Small nose (a short line).
        var nose = Path()
        nose.move(to: CGPoint(x: c.x - r*0.02, y: c.y + r*0.06))
        nose.addLine(to: CGPoint(x: c.x + r*0.04, y: c.y + r*0.17))
        ctx.stroke(nose, with: .color(skinLine), lineWidth: max(1, r*0.035))

        CharKit.blush(&ctx, c.x, c.y + r*0.27, r*0.6, r*0.15, col(0.92, 0.6, 0.55))
        CharKit.mouth(&ctx, c.x, c.y + r*0.43, r*0.16, a)
        return (c, r)
    }
}

struct SkullChar: CharacterDrawer {
    let name = "Skull"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let socket = col(0.07, 0.06, 0.09)
        let tooth  = col(0.96, 0.95, 0.90)
        let ember  = col(1.0, 0.55, 0.22)

        // Pale bone-coloured head.
        CharKit.head(&ctx, c, r, col(0.94, 0.92, 0.86), col(0.78, 0.74, 0.66))

        // Two large dark hollow eye sockets, each with a faint ember glow that
        // breathes gently.
        let pulse = 1 + 0.14 * CGFloat(a.breath)
        for side in [-1.0, 1.0] {
            let ex = c.x + CGFloat(side) * r*0.36
            let ey = c.y - r*0.06
            CharKit.ellipse(&ctx, ex, ey, r*0.28, r*0.34, .color(socket))
            let er = r*0.13 * pulse
            ctx.fill(Path(ellipseIn: CGRect(x: ex - er, y: ey - er,
                                            width: er*2, height: er*2)),
                     with: .radialGradient(
                        Gradient(colors: [ember.opacity(0.95), ember.opacity(0.0)]),
                        center: CGPoint(x: ex, y: ey),
                        startRadius: 0, endRadius: er))
        }

        // Dark inverted-triangle nasal cavity (apex pointing down).
        CharKit.tri(&ctx,
                    CGPoint(x: c.x - r*0.11, y: c.y + r*0.20),
                    CGPoint(x: c.x + r*0.11, y: c.y + r*0.20),
                    CGPoint(x: c.x, y: c.y + r*0.44), socket)

        // A row of small rounded-rectangle teeth across the lower face.
        let count = 6
        let tw = r*0.13, th = r*0.17, gap = r*0.025
        let total = CGFloat(count)*tw + CGFloat(count - 1)*gap
        let startX = c.x - total/2
        let ty = c.y + r*0.52
        for i in 0..<count {
            let tx = startX + CGFloat(i)*(tw + gap)
            let rect = CGRect(x: tx, y: ty, width: tw, height: th)
            let path = Path(roundedRect: rect, cornerRadius: r*0.04)
            ctx.fill(path, with: .color(tooth))
            ctx.stroke(path, with: .color(socket.opacity(0.45)),
                       lineWidth: max(1, r*0.012))
        }
        return (c, r)
    }
}
