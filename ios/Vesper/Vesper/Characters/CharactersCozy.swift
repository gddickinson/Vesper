//  CharactersCozy.swift
//  Vesper — the cozy woodland cast (Hedgehog, Rat, Red Panda, Koala). Same
//  CharKit primitives as the rest of the cast; each adds one bespoke flourish
//  (a spiky crown, a long snout, a white face mask + tear-marks, a spoon nose).

import SwiftUI

private func col(_ r: Double, _ g: Double, _ b: Double) -> Color { Color(red: r, green: g, blue: b) }

struct HedgehogChar: CharacterDrawer {
    let name = "Hedgehog"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        // spiky crown: short brown triangles fanning around the upper half,
        // pointing outward/up — drawn BEHIND the head so their bases tuck under it.
        let spike = col(0.46, 0.33, 0.2), spikeDark = col(0.36, 0.25, 0.15)
        let n = 17
        for i in 0..<n {
            let ang = -Double.pi + (Double(i) + 0.5) / Double(n) * Double.pi
            let dx = CGFloat(cos(ang)), dy = CGFloat(sin(ang))
            let px = -dy, py = dx
            let baseR = r * 0.84
            let bx = c.x + dx * baseR, by = c.y + dy * baseR
            let tipR = r * (1.27 + 0.05 * CGFloat(a.breath))
            let tx = c.x + dx * tipR, ty = c.y + dy * tipR
            let hw = r * 0.12
            CharKit.tri(&ctx,
                        CGPoint(x: bx + px * hw, y: by + py * hw),
                        CGPoint(x: tx, y: ty),
                        CGPoint(x: bx - px * hw, y: by - py * hw),
                        i % 2 == 0 ? spike : spikeDark)
        }
        // smooth tan/cream lower face
        CharKit.head(&ctx, c, r, col(0.92, 0.82, 0.64), col(0.78, 0.65, 0.46))
        CharKit.eyes(&ctx, c.x, c.y - r*0.04, r*0.36, r*0.16, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.2, r*0.52, r*0.16, .pink)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.24, r*0.08, r*0.06, .color(col(0.16, 0.11, 0.09)))
        CharKit.mouth(&ctx, c.x, c.y + r*0.42, r*0.13, a)
        return (c, r)
    }
}

struct RatChar: CharacterDrawer {
    let name = "Rat"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let fur = col(0.6, 0.6, 0.64)
        let innerEar = col(0.93, 0.74, 0.78)
        // two big round ears on top — BEHIND the head
        CharKit.circle(&ctx, c.x - r*0.66, c.y - r*0.74, r*0.4, fur)
        CharKit.circle(&ctx, c.x + r*0.66, c.y - r*0.74, r*0.4, fur)
        CharKit.circle(&ctx, c.x - r*0.66, c.y - r*0.74, r*0.24, innerEar)
        CharKit.circle(&ctx, c.x + r*0.66, c.y - r*0.74, r*0.24, innerEar)
        CharKit.head(&ctx, c, r, fur, col(0.42, 0.42, 0.47))
        // small pointed muzzle projecting toward the front/bottom
        CharKit.ellipse(&ctx, c.x, c.y + r*0.56, r*0.34, r*0.42, .color(col(0.67, 0.67, 0.71)))
        CharKit.eyes(&ctx, c.x, c.y - r*0.06, r*0.32, r*0.15, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.18, r*0.6, r*0.13, .pink)
        // whiskers from the snout + pink nose at the tip
        CharKit.whiskers(&ctx, c.x, c.y + r*0.68, r, -1, col(0.78, 0.78, 0.82))
        CharKit.whiskers(&ctx, c.x, c.y + r*0.68, r,  1, col(0.78, 0.78, 0.82))
        CharKit.ellipse(&ctx, c.x, c.y + r*0.88, r*0.09, r*0.07, .color(col(0.95, 0.55, 0.62)))
        return (c, r)
    }
}

struct RedPandaChar: CharacterDrawer {
    let name = "Red Panda"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let rust = col(0.74, 0.37, 0.18), rustDark = col(0.58, 0.27, 0.12)
        let white = col(0.96, 0.93, 0.88)
        // pointed ears with white tips — BEHIND the head
        for s in [-1.0, 1.0] {
            let sx = CGFloat(s)
            let bx = c.x + sx * r*0.62
            CharKit.tri(&ctx,
                        CGPoint(x: bx - r*0.3, y: c.y - r*0.5),
                        CGPoint(x: bx + sx*r*0.12, y: c.y - r*1.18),
                        CGPoint(x: bx + r*0.3, y: c.y - r*0.5),
                        rust)
            CharKit.tri(&ctx,
                        CGPoint(x: bx - r*0.15, y: c.y - r*0.76),
                        CGPoint(x: bx + sx*r*0.08, y: c.y - r*1.1),
                        CGPoint(x: bx + r*0.15, y: c.y - r*0.76),
                        white)
        }
        CharKit.head(&ctx, c, r, rust, rustDark)
        // white face mask: patches around the eyes + a white muzzle below
        CharKit.circle(&ctx, c.x - r*0.36, c.y - r*0.04, r*0.3, white)
        CharKit.circle(&ctx, c.x + r*0.36, c.y - r*0.04, r*0.3, white)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.34, r*0.44, r*0.4, .color(white))
        // dark tear-mark lines running down from each eye
        for s in [-1.0, 1.0] {
            let sx = CGFloat(s)
            ctx.fill(Path { p in
                p.move(to: CGPoint(x: c.x + sx*r*0.34, y: c.y + r*0.06))
                p.addQuadCurve(to: CGPoint(x: c.x + sx*r*0.18, y: c.y + r*0.5),
                               control: CGPoint(x: c.x + sx*r*0.14, y: c.y + r*0.28))
                p.addLine(to: CGPoint(x: c.x + sx*r*0.3, y: c.y + r*0.5))
                p.addQuadCurve(to: CGPoint(x: c.x + sx*r*0.42, y: c.y + r*0.08),
                               control: CGPoint(x: c.x + sx*r*0.4, y: c.y + r*0.28))
                p.closeSubpath()
            }, with: .color(col(0.4, 0.2, 0.12)))
        }
        CharKit.eyes(&ctx, c.x, c.y - r*0.04, r*0.36, r*0.16, a)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.34, r*0.09, r*0.07, .color(col(0.12, 0.08, 0.07)))
        CharKit.mouth(&ctx, c.x, c.y + r*0.52, r*0.12, a)
        return (c, r)
    }
}

struct KoalaChar: CharacterDrawer {
    let name = "Koala"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let grey = col(0.62, 0.64, 0.68), greyDark = col(0.46, 0.48, 0.53)
        let pale = col(0.83, 0.84, 0.87)
        // two BIG fuzzy round ears on the sides — BEHIND the head
        let puff = CGFloat(a.breath) * r * 0.03
        for s in [-1.0, 1.0] {
            let ex = c.x + CGFloat(s) * r*0.9
            CharKit.circle(&ctx, ex, c.y - r*0.06, r*0.56 + puff, grey)
            CharKit.circle(&ctx, ex, c.y - r*0.06, r*0.36, pale)
            CharKit.circle(&ctx, ex, c.y - r*0.06, r*0.2, col(0.95, 0.82, 0.85))
        }
        CharKit.head(&ctx, c, r, grey, greyDark)
        // eyes set wide
        CharKit.eyes(&ctx, c.x, c.y - r*0.12, r*0.48, r*0.14, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.14, r*0.62, r*0.16, .pink)
        // big dark "spoon" nose (narrow top, bulbous bottom)
        let nx = c.x, ny = c.y + r*0.16
        ctx.fill(Path { p in
            p.move(to: CGPoint(x: nx - r*0.14, y: ny - r*0.22))
            p.addQuadCurve(to: CGPoint(x: nx + r*0.14, y: ny - r*0.22),
                           control: CGPoint(x: nx, y: ny - r*0.36))
            p.addQuadCurve(to: CGPoint(x: nx + r*0.24, y: ny + r*0.16),
                           control: CGPoint(x: nx + r*0.26, y: ny - r*0.04))
            p.addQuadCurve(to: CGPoint(x: nx - r*0.24, y: ny + r*0.16),
                           control: CGPoint(x: nx, y: ny + r*0.42))
            p.addQuadCurve(to: CGPoint(x: nx - r*0.14, y: ny - r*0.22),
                           control: CGPoint(x: nx - r*0.26, y: ny - r*0.04))
            p.closeSubpath()
        }, with: .color(col(0.18, 0.16, 0.2)))
        CharKit.circle(&ctx, nx - r*0.08, ny - r*0.12, r*0.05, .white.opacity(0.5))
        CharKit.mouth(&ctx, c.x, c.y + r*0.5, r*0.1, a)
        return (c, r)
    }
}
