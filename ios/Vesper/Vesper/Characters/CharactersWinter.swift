//  CharactersWinter.swift
//  Vesper — the wintry/night cast (Snowman, Luna). Each is a small
//  CharacterDrawer using the shared CharKit primitives. Add a character by
//  adding a struct and listing it in Characters.all.

import SwiftUI

private func col(_ r: Double, _ g: Double, _ b: Double) -> Color {
    Color(red: r, green: g, blue: b)
}

/// A small six-spoke snowflake, drawn as faint white strokes.
private func snowflake(_ ctx: inout GraphicsContext, _ p: CGPoint, _ s: CGFloat,
                       _ op: Double) {
    let arm = Color.white.opacity(op)
    for k in 0..<3 {
        let ang = Double(k) * .pi / 3
        let dx = CGFloat(cos(ang)) * s, dy = CGFloat(sin(ang)) * s
        var line = Path()
        line.move(to: CGPoint(x: p.x - dx, y: p.y - dy))
        line.addLine(to: CGPoint(x: p.x + dx, y: p.y + dy))
        ctx.stroke(line, with: .color(arm), lineWidth: max(1, s * 0.16))
    }
    ctx.fill(Path(ellipseIn: CGRect(x: p.x - s * 0.18, y: p.y - s * 0.18,
                                    width: s * 0.36, height: s * 0.36)),
             with: .color(arm))
}

struct SnowmanChar: CharacterDrawer {
    let name = "Snowman"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)

        // drifting snowflakes near the head
        let drift = CGFloat(sin(a.t * 0.7))
        snowflake(&ctx, CGPoint(x: c.x - r * 1.08 + drift * r * 0.12,
                                y: c.y - r * 0.30 + drift * r * 0.06), r * 0.18, 0.7)
        snowflake(&ctx, CGPoint(x: c.x + r * 1.12 - drift * r * 0.10,
                                y: c.y + r * 0.34 - drift * r * 0.08), r * 0.13, 0.55)

        // white snowball head (near-white light/shade)
        CharKit.head(&ctx, c, r, col(0.99, 0.99, 1.0), col(0.84, 0.87, 0.93))

        // knit cap: a coloured dome over the crown + a ribbed cuff band + pom
        let cap = col(0.82, 0.30, 0.32), cuff = col(0.90, 0.42, 0.44)
        let bandY = c.y - r * 0.64
        var dome = Path()
        dome.move(to: CGPoint(x: c.x - r * 0.80, y: bandY + r * 0.06))
        dome.addQuadCurve(to: CGPoint(x: c.x, y: c.y - r * 1.30),
                          control: CGPoint(x: c.x - r * 0.74, y: c.y - r * 1.22))
        dome.addQuadCurve(to: CGPoint(x: c.x + r * 0.80, y: bandY + r * 0.06),
                          control: CGPoint(x: c.x + r * 0.74, y: c.y - r * 1.22))
        dome.closeSubpath()
        ctx.fill(dome, with: .color(cap))
        let band = Path(roundedRect: CGRect(x: c.x - r * 0.86, y: bandY,
                                            width: r * 1.72, height: r * 0.34),
                        cornerRadius: r * 0.17)
        ctx.fill(band, with: .color(cuff))
        CharKit.circle(&ctx, c.x, c.y - r * 1.34, r * 0.17, .white)

        // two coal eyes (small dark circles, with a subtle blink)
        let coal = col(0.11, 0.11, 0.14)
        let eyeY = c.y - r * 0.04
        let openH = r * 0.11 * CGFloat(max(0.18, 1 - a.blink))
        CharKit.ellipse(&ctx, c.x - r * 0.30, eyeY, r * 0.11, openH, .color(coal))
        CharKit.ellipse(&ctx, c.x + r * 0.30, eyeY, r * 0.11, openH, .color(coal))

        // carrot nose: an orange triangle pointing outward/down from the centre
        let carrot = col(0.95, 0.54, 0.18)
        let ny = c.y + r * 0.10
        CharKit.tri(&ctx,
                    CGPoint(x: c.x - r * 0.04, y: ny - r * 0.08),
                    CGPoint(x: c.x - r * 0.04, y: ny + r * 0.07),
                    CGPoint(x: c.x + r * 0.54, y: ny + r * 0.20), carrot)

        // button smile: a small downward arc of coal dots
        let sw = r * 0.40, smileY = c.y + r * 0.42
        for i in 0..<5 {
            let f = CGFloat(i) / 4 * 2 - 1            // -1 … 1
            let dx = f * sw
            let dy = (1 - f * f) * r * 0.18           // dip in the middle
            CharKit.circle(&ctx, c.x + dx, smileY + dy, r * 0.05, coal)
        }
        return (c, r)
    }
}

struct LunaChar: CharacterDrawer {
    let name = "Luna"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        // warm outer glow
        CharKit.aura(&ctx, c, r, col(1.0, 0.90, 0.62), a.breath)

        // pale cream/ivory head
        CharKit.head(&ctx, c, r, col(0.99, 0.97, 0.88), col(0.90, 0.86, 0.74))

        // a soft radial highlight (dreamy top-left sheen)
        let headRect = CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)
        ctx.fill(Path(ellipseIn: headRect), with: .radialGradient(
            Gradient(colors: [.white.opacity(0.55), .clear]),
            center: CGPoint(x: c.x - r * 0.30, y: c.y - r * 0.34),
            startRadius: 0, endRadius: r * 0.95))

        // faint grey craters of varying size
        let crater = col(0.80, 0.78, 0.72).opacity(0.5)
        CharKit.circle(&ctx, c.x + r * 0.44, c.y - r * 0.34, r * 0.14, crater)
        CharKit.circle(&ctx, c.x - r * 0.50, c.y + r * 0.30, r * 0.11, crater)
        CharKit.circle(&ctx, c.x + r * 0.30, c.y + r * 0.46, r * 0.08, crater)
        CharKit.circle(&ctx, c.x - r * 0.22, c.y - r * 0.52, r * 0.06, crater)

        // sleepy CLOSED eyes — each a gentle downward arc
        let lid = col(0.48, 0.45, 0.40)
        let lw = max(1.6, r * 0.05), eyeW = r * 0.16, ey = c.y - r * 0.02
        for side in [-1.0, 1.0] {
            let ex = c.x + CGFloat(side) * r * 0.36
            var p = Path()
            p.move(to: CGPoint(x: ex - eyeW, y: ey))
            p.addQuadCurve(to: CGPoint(x: ex + eyeW, y: ey),
                           control: CGPoint(x: ex, y: ey + eyeW * 0.9))
            ctx.stroke(p, with: .color(lid), lineWidth: lw)
        }

        // a tiny soft smile
        var smile = Path()
        smile.move(to: CGPoint(x: c.x - r * 0.13, y: c.y + r * 0.34))
        smile.addQuadCurve(to: CGPoint(x: c.x + r * 0.13, y: c.y + r * 0.34),
                           control: CGPoint(x: c.x, y: c.y + r * 0.44))
        ctx.stroke(smile, with: .color(lid), lineWidth: lw)
        return (c, r)
    }
}
