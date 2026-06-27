//  CharactersWild.swift
//  Vesper — the wild cast (Tiger, Elephant, Giraffe, Rhino, Monkey, Deer).
//  Same CharKit primitives as CharactersMore.swift; tall head-gear characters
//  (Giraffe ossicones, Rhino horn, Deer antlers) use a smaller head box raised
//  on screen so nothing clips at the top.

import SwiftUI

private func col(_ r: Double, _ g: Double, _ b: Double) -> Color { Color(red: r, green: g, blue: b) }

struct TigerChar: CharacterDrawer {
    let name = "Tiger"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let orange = col(0.96, 0.58, 0.2), dark = col(0.82, 0.44, 0.12)
        // rounded ears with dark inner, behind the head
        for s in [-1.0, 1.0] {
            let ex = c.x + CGFloat(s) * r*0.74
            CharKit.circle(&ctx, ex, c.y - r*0.82, r*0.32, orange)
            CharKit.circle(&ctx, ex, c.y - r*0.82, r*0.17, col(0.2, 0.13, 0.1))
        }
        CharKit.head(&ctx, c, r, orange, dark)
        // white muzzle area (lower face)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.34, r*0.5, r*0.42, .color(col(0.99, 0.95, 0.9)))
        // black stripes — forehead + cheeks (tapered triangles)
        let st = col(0.12, 0.08, 0.06)
        CharKit.tri(&ctx, CGPoint(x: c.x, y: c.y - r*0.92),
                    CGPoint(x: c.x - r*0.07, y: c.y - r*0.42),
                    CGPoint(x: c.x + r*0.07, y: c.y - r*0.42), st)
        for s in [-1.0, 1.0] {
            // angled forehead stripes
            CharKit.tri(&ctx, CGPoint(x: c.x + CGFloat(s)*r*0.3, y: c.y - r*0.82),
                        CGPoint(x: c.x + CGFloat(s)*r*0.36, y: c.y - r*0.38),
                        CGPoint(x: c.x + CGFloat(s)*r*0.22, y: c.y - r*0.4), st)
            // cheek stripes (horizontal, pointing inward)
            let sx = c.x + CGFloat(s) * r*0.72
            CharKit.tri(&ctx, CGPoint(x: sx + CGFloat(s)*r*0.18, y: c.y),
                        CGPoint(x: sx - CGFloat(s)*r*0.12, y: c.y - r*0.08),
                        CGPoint(x: sx - CGFloat(s)*r*0.12, y: c.y + r*0.08), st)
            CharKit.tri(&ctx, CGPoint(x: sx + CGFloat(s)*r*0.14, y: c.y + r*0.24),
                        CGPoint(x: sx - CGFloat(s)*r*0.12, y: c.y + r*0.17),
                        CGPoint(x: sx - CGFloat(s)*r*0.12, y: c.y + r*0.31), st)
        }
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.38, r*0.16, a)
        CharKit.nose(&ctx, c.x, c.y + r*0.2, r*0.1, col(0.95, 0.5, 0.55))
        CharKit.whiskers(&ctx, c.x, c.y + r*0.3, r, -1, .white)
        CharKit.whiskers(&ctx, c.x, c.y + r*0.3, r, 1, .white)
        CharKit.mouth(&ctx, c.x, c.y + r*0.42, r*0.13, a)
        return (c, r)
    }
}

struct ElephantChar: CharacterDrawer {
    let name = "Elephant"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let grey = col(0.62, 0.64, 0.7), dark = col(0.46, 0.48, 0.55)
        // big fan ears behind the head
        for s in [-1.0, 1.0] {
            CharKit.ellipse(&ctx, c.x + CGFloat(s)*r*0.92, c.y, r*0.62, r*0.8, .color(grey))
            CharKit.ellipse(&ctx, c.x + CGFloat(s)*r*1.0, c.y + r*0.04, r*0.42, r*0.58,
                            .color(col(0.74, 0.66, 0.66)))
        }
        CharKit.head(&ctx, c, r, grey, dark)
        CharKit.eyes(&ctx, c.x, c.y - r*0.18, r*0.36, r*0.14, a)
        // small white tusks (drawn before the trunk so it overlaps their tops)
        for s in [-1.0, 1.0] {
            CharKit.tri(&ctx, CGPoint(x: c.x + CGFloat(s)*r*0.14, y: c.y + r*0.46),
                        CGPoint(x: c.x + CGFloat(s)*r*0.3, y: c.y + r*0.52),
                        CGPoint(x: c.x + CGFloat(s)*r*0.22, y: c.y + r*0.78),
                        col(0.97, 0.96, 0.9))
        }
        // trunk curving down from the centre of the face
        let wA = r*0.22, wB = r*0.17, wC = r*0.11, wD = r*0.07
        var tr = Path()
        tr.move(to: CGPoint(x: c.x - wA, y: c.y))
        tr.addQuadCurve(to: CGPoint(x: c.x - wB, y: c.y + r*0.45),
                        control: CGPoint(x: c.x - wA, y: c.y + r*0.25))
        tr.addQuadCurve(to: CGPoint(x: c.x + r*0.14 - wC, y: c.y + r*0.78),
                        control: CGPoint(x: c.x - wB, y: c.y + r*0.66))
        tr.addQuadCurve(to: CGPoint(x: c.x + r*0.34 - wD, y: c.y + r*0.95),
                        control: CGPoint(x: c.x + r*0.06, y: c.y + r*0.92))
        tr.addQuadCurve(to: CGPoint(x: c.x + r*0.34 + wD, y: c.y + r*0.95),
                        control: CGPoint(x: c.x + r*0.34, y: c.y + r*1.04))
        tr.addQuadCurve(to: CGPoint(x: c.x + r*0.14 + wC, y: c.y + r*0.78),
                        control: CGPoint(x: c.x + r*0.32, y: c.y + r*0.9))
        tr.addQuadCurve(to: CGPoint(x: c.x + wB, y: c.y + r*0.45),
                        control: CGPoint(x: c.x + wB + r*0.06, y: c.y + r*0.66))
        tr.addQuadCurve(to: CGPoint(x: c.x + wA, y: c.y),
                        control: CGPoint(x: c.x + wA, y: c.y + r*0.25))
        tr.closeSubpath()
        ctx.fill(tr, with: .color(grey))
        // trunk rings for texture
        for f in [0.35, 0.55, 0.72] as [CGFloat] {
            let ty = c.y + r * 0.95 * f
            let tx = c.x + r*0.34 * f * f
            let hw = r * (0.22 - 0.16 * f)
            var rp = Path()
            rp.move(to: CGPoint(x: tx - hw, y: ty))
            rp.addQuadCurve(to: CGPoint(x: tx + hw, y: ty), control: CGPoint(x: tx, y: ty + r*0.06))
            ctx.stroke(rp, with: .color(dark.opacity(0.5)), lineWidth: max(1, r*0.025))
        }
        return (c, r)
    }
}

struct GiraffeChar: CharacterDrawer {
    let name = "Giraffe"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.55)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let pale = col(0.97, 0.86, 0.5), dark = col(0.86, 0.72, 0.36)
        // long neck behind the head
        CharKit.ellipse(&ctx, c.x, c.y + r*1.35, r*0.42, r*0.95, .color(pale))
        // ossicones — short stalks each ending in a knob
        for s in [-1.0, 1.0] {
            let ox = c.x + CGFloat(s) * r*0.3
            var stalk = Path()
            stalk.move(to: CGPoint(x: ox - r*0.06, y: c.y - r*0.78))
            stalk.addLine(to: CGPoint(x: ox - r*0.04, y: c.y - r*1.18))
            stalk.addLine(to: CGPoint(x: ox + r*0.04, y: c.y - r*1.18))
            stalk.addLine(to: CGPoint(x: ox + r*0.06, y: c.y - r*0.78))
            stalk.closeSubpath()
            ctx.fill(stalk, with: .color(pale))
            CharKit.circle(&ctx, ox, c.y - r*1.22, r*0.12, col(0.5, 0.34, 0.2))
        }
        CharKit.head(&ctx, c, r, pale, dark)
        // soft orange patches
        let patch = col(0.85, 0.6, 0.28)
        CharKit.circle(&ctx, c.x - r*0.5, c.y - r*0.28, r*0.22, patch.opacity(0.5))
        CharKit.circle(&ctx, c.x + r*0.54, c.y - r*0.06, r*0.2, patch.opacity(0.5))
        CharKit.circle(&ctx, c.x - r*0.26, c.y + r*0.18, r*0.16, patch.opacity(0.45))
        // lighter muzzle
        CharKit.ellipse(&ctx, c.x, c.y + r*0.46, r*0.45, r*0.32, .color(col(0.99, 0.93, 0.72)))
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.38, r*0.16, a)
        CharKit.circle(&ctx, c.x - r*0.16, c.y + r*0.42, r*0.05, dark)
        CharKit.circle(&ctx, c.x + r*0.16, c.y + r*0.42, r*0.05, dark)
        CharKit.mouth(&ctx, c.x, c.y + r*0.6, r*0.12, a)
        return (c, r)
    }
}

struct RhinoChar: CharacterDrawer {
    let name = "Rhino"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.55)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let grey = col(0.63, 0.65, 0.69), dark = col(0.47, 0.49, 0.55)
        // small ears
        for s in [-1.0, 1.0] {
            CharKit.ellipse(&ctx, c.x + CGFloat(s)*r*0.72, c.y - r*0.72, r*0.18, r*0.24, .color(grey))
            CharKit.ellipse(&ctx, c.x + CGFloat(s)*r*0.72, c.y - r*0.72, r*0.1, r*0.15,
                            .color(col(0.8, 0.6, 0.62)))
        }
        CharKit.head(&ctx, c, r, grey, dark)
        // broad muzzle
        CharKit.ellipse(&ctx, c.x, c.y + r*0.46, r*0.6, r*0.42, .color(col(0.72, 0.74, 0.78)))
        // smaller second horn (behind, higher up)
        let horn = col(0.93, 0.91, 0.83), hornD = col(0.8, 0.77, 0.68)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.08, y: c.y - r*0.12),
                    CGPoint(x: c.x + r*0.08, y: c.y - r*0.12),
                    CGPoint(x: c.x, y: c.y - r*0.46), hornD)
        // prominent nose horn pointing up from the snout
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.14, y: c.y + r*0.54),
                    CGPoint(x: c.x + r*0.14, y: c.y + r*0.54),
                    CGPoint(x: c.x, y: c.y - r*0.06), horn)
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.38, r*0.16, a)
        CharKit.circle(&ctx, c.x - r*0.22, c.y + r*0.58, r*0.05, dark)
        CharKit.circle(&ctx, c.x + r*0.22, c.y + r*0.58, r*0.05, dark)
        return (c, r)
    }
}

struct MonkeyChar: CharacterDrawer {
    let name = "Monkey"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let brown = col(0.55, 0.4, 0.28), dark = col(0.42, 0.29, 0.18)
        // big round ears on the sides of the head
        for s in [-1.0, 1.0] {
            CharKit.circle(&ctx, c.x + CGFloat(s)*r*1.02, c.y, r*0.4, brown)
            CharKit.circle(&ctx, c.x + CGFloat(s)*r*1.02, c.y, r*0.24, col(0.78, 0.6, 0.45))
        }
        CharKit.head(&ctx, c, r, brown, dark)
        // heart-/peanut-shaped face patch covering eyes + muzzle
        let face = col(0.85, 0.68, 0.5)
        CharKit.circle(&ctx, c.x - r*0.2, c.y - r*0.14, r*0.3, face)
        CharKit.circle(&ctx, c.x + r*0.2, c.y - r*0.14, r*0.3, face)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.04, r*0.5, r*0.4, .color(face))
        CharKit.ellipse(&ctx, c.x, c.y + r*0.34, r*0.42, r*0.32, .color(face))
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.38, r*0.16, a)
        // small muzzle with nostrils
        CharKit.circle(&ctx, c.x - r*0.1, c.y + r*0.26, r*0.04, dark)
        CharKit.circle(&ctx, c.x + r*0.1, c.y + r*0.26, r*0.04, dark)
        CharKit.mouth(&ctx, c.x, c.y + r*0.42, r*0.14, a)
        return (c, r)
    }
}

struct DeerChar: CharacterDrawer {
    let name = "Deer"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.55)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let tan = col(0.8, 0.58, 0.36), dark = col(0.64, 0.44, 0.26)
        // branched antlers on top (a few strokes)
        let antler = col(0.7, 0.55, 0.35)
        for s in [-1.0, 1.0] {
            let bx = c.x + CGFloat(s) * r*0.3
            var p = Path()
            p.move(to: CGPoint(x: bx, y: c.y - r*0.68))
            p.addLine(to: CGPoint(x: bx + CGFloat(s)*r*0.26, y: c.y - r*1.3))
            p.move(to: CGPoint(x: bx + CGFloat(s)*r*0.1, y: c.y - r*0.94))
            p.addLine(to: CGPoint(x: bx + CGFloat(s)*r*0.42, y: c.y - r*1.04))
            p.move(to: CGPoint(x: bx + CGFloat(s)*r*0.19, y: c.y - r*1.12))
            p.addLine(to: CGPoint(x: bx + CGFloat(s)*r*0.04, y: c.y - r*1.38))
            ctx.stroke(p, with: .color(antler), lineWidth: max(2, r*0.07))
        }
        // large ears out to the sides, behind the head
        for s in [-1.0, 1.0] {
            CharKit.ellipse(&ctx, c.x + CGFloat(s)*r*0.92, c.y - r*0.36, r*0.26, r*0.42, .color(tan))
            CharKit.ellipse(&ctx, c.x + CGFloat(s)*r*0.92, c.y - r*0.36, r*0.14, r*0.28,
                            .color(col(0.94, 0.82, 0.7)))
        }
        CharKit.head(&ctx, c, r, tan, dark)
        // light fawn spots
        let spot = col(0.96, 0.86, 0.69)
        CharKit.circle(&ctx, c.x - r*0.42, c.y - r*0.3, r*0.08, spot)
        CharKit.circle(&ctx, c.x + r*0.44, c.y - r*0.2, r*0.07, spot)
        CharKit.circle(&ctx, c.x - r*0.3, c.y + r*0.12, r*0.06, spot)
        CharKit.circle(&ctx, c.x + r*0.32, c.y + r*0.16, r*0.07, spot)
        // lighter muzzle
        CharKit.ellipse(&ctx, c.x, c.y + r*0.42, r*0.34, r*0.28, .color(col(0.92, 0.8, 0.66)))
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.38, r*0.16, a)
        // dark nose
        CharKit.ellipse(&ctx, c.x, c.y + r*0.34, r*0.12, r*0.09, .color(col(0.18, 0.12, 0.12)))
        CharKit.mouth(&ctx, c.x, c.y + r*0.54, r*0.1, a)
        return (c, r)
    }
}
