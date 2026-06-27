//  CharactersFarm.swift
//  Vesper — the barnyard cast (Chicken, Duckling, Sheep, Pig, Cow). Each is a
//  small CharacterDrawer built from the shared CharKit primitives; cute,
//  recognizable, and breath-animated. Characters with tall head-gear (comb,
//  tuft, wool ring, horns) use a smaller headBox so the crown isn't clipped.
//  Add a character by adding a struct and listing it in Characters.all.

import SwiftUI

private func col(_ r: Double, _ g: Double, _ b: Double) -> Color {
    Color(red: r, green: g, blue: b)
}

struct ChickenChar: CharacterDrawer {
    let name = "Chicken"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let cream = col(0.99, 0.97, 0.92), shade = col(0.9, 0.86, 0.78)
        let red = col(0.86, 0.2, 0.22)
        // red comb — three small bumps on the crown, behind the head
        CharKit.circle(&ctx, c.x - r*0.32, c.y - r*0.92, r*0.2, red)
        CharKit.circle(&ctx, c.x,         c.y - r*1.05, r*0.22, red)
        CharKit.circle(&ctx, c.x + r*0.32, c.y - r*0.92, r*0.2, red)
        CharKit.head(&ctx, c, r, cream, shade)
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.34, r*0.16, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.22, r*0.6, r*0.16, .pink)
        // orange diamond beak below the eyes
        let bx = c.x, by = c.y + r*0.34
        let orange = col(0.97, 0.6, 0.16)
        var beak = Path()
        beak.move(to: CGPoint(x: bx, y: by - r*0.14))
        beak.addLine(to: CGPoint(x: bx + r*0.18, y: by))
        beak.addLine(to: CGPoint(x: bx, y: by + r*0.14))
        beak.addLine(to: CGPoint(x: bx - r*0.18, y: by))
        beak.closeSubpath()
        ctx.fill(beak, with: .color(orange))
        // small red wattle dot under the beak
        CharKit.circle(&ctx, bx, by + r*0.26, r*0.1, red)
        return (c, r)
    }
}

struct DucklingChar: CharacterDrawer {
    let name = "Duckling"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let yellow = col(0.99, 0.86, 0.28), shade = col(0.92, 0.74, 0.18)
        let orange = col(0.97, 0.58, 0.14)
        // little top tuft — a small triangle on the crown, behind the head
        let tw = sin(a.t * 3) * r * 0.05
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.16, y: c.y - r*0.9),
                    CGPoint(x: c.x + tw, y: c.y - r*1.32),
                    CGPoint(x: c.x + r*0.16, y: c.y - r*0.9), yellow)
        CharKit.head(&ctx, c, r, yellow, shade)
        CharKit.eyes(&ctx, c.x, c.y - r*0.12, r*0.32, r*0.16, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.14, r*0.6, r*0.15, .pink)
        // wide flat orange bill below the eyes
        CharKit.ellipse(&ctx, c.x, c.y + r*0.32, r*0.42, r*0.18, .color(orange))
        var line = Path()
        line.move(to: CGPoint(x: c.x - r*0.34, y: c.y + r*0.32))
        line.addLine(to: CGPoint(x: c.x + r*0.34, y: c.y + r*0.32))
        ctx.stroke(line, with: .color(col(0.8, 0.45, 0.1)), lineWidth: max(1, r*0.03))
        return (c, r)
    }
}

struct SheepChar: CharacterDrawer {
    let name = "Sheep"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let wool = col(0.98, 0.98, 0.99), woolSh = col(0.85, 0.86, 0.9)
        let cream = col(0.96, 0.92, 0.86), shade = col(0.85, 0.79, 0.71)
        // ring of soft white wool bumps around the head perimeter
        let n = 12
        for i in 0..<n {
            let ang = Double(i) / Double(n) * 2 * .pi
            let bx = c.x + CGFloat(cos(ang)) * r
            let by = c.y + CGFloat(sin(ang)) * r
            CharKit.circle(&ctx, bx, by, r * 0.34, woolSh)
            CharKit.circle(&ctx, bx, by, r * 0.27, wool)
        }
        // small dark floppy ears at the sides (behind the face)
        let earCol = col(0.46, 0.42, 0.42)
        CharKit.ellipse(&ctx, c.x - r*0.96, c.y + r*0.12, r*0.28, r*0.15, .color(earCol))
        CharKit.ellipse(&ctx, c.x + r*0.96, c.y + r*0.12, r*0.28, r*0.15, .color(earCol))
        CharKit.head(&ctx, c, r, cream, shade)
        // a woolly fringe on the forehead
        CharKit.circle(&ctx, c.x - r*0.3, c.y - r*0.6, r*0.26, wool)
        CharKit.circle(&ctx, c.x + r*0.3, c.y - r*0.6, r*0.26, wool)
        CharKit.circle(&ctx, c.x, c.y - r*0.72, r*0.28, wool)
        CharKit.eyes(&ctx, c.x, c.y - r*0.02, r*0.32, r*0.15, a)
        CharKit.circle(&ctx, c.x, c.y + r*0.26, r*0.08, col(0.32, 0.27, 0.29))
        CharKit.mouth(&ctx, c.x, c.y + r*0.42, r*0.14, a)
        return (c, r)
    }
}

struct PigChar: CharacterDrawer {
    let name = "Pig"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let pink = col(0.97, 0.74, 0.78), shade = col(0.9, 0.62, 0.68)
        let deep = col(0.85, 0.52, 0.6)
        // two small forward-flopping triangle ears at the top
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.62, y: c.y - r*0.76),
                    CGPoint(x: c.x - r*0.26, y: c.y - r*1.02),
                    CGPoint(x: c.x - r*0.14, y: c.y - r*0.58), pink)
        CharKit.tri(&ctx, CGPoint(x: c.x + r*0.62, y: c.y - r*0.76),
                    CGPoint(x: c.x + r*0.26, y: c.y - r*1.02),
                    CGPoint(x: c.x + r*0.14, y: c.y - r*0.58), pink)
        CharKit.head(&ctx, c, r, pink, shade)
        CharKit.eyes(&ctx, c.x, c.y - r*0.12, r*0.34, r*0.16, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.16, r*0.62, r*0.16, .pink)
        // flat pink snout with two darker nostril dots
        CharKit.ellipse(&ctx, c.x, c.y + r*0.3, r*0.3, r*0.2, .color(deep))
        CharKit.circle(&ctx, c.x - r*0.11, c.y + r*0.3, r*0.06, col(0.6, 0.36, 0.42))
        CharKit.circle(&ctx, c.x + r*0.11, c.y + r*0.3, r*0.06, col(0.6, 0.36, 0.42))
        CharKit.mouth(&ctx, c.x, c.y + r*0.58, r*0.14, a)
        return (c, r)
    }
}

struct CowChar: CharacterDrawer {
    let name = "Cow"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let white = col(0.98, 0.97, 0.96), shade = col(0.86, 0.85, 0.86)
        let dark = col(0.28, 0.24, 0.24)
        let horn = col(0.95, 0.9, 0.78), hornSh = col(0.82, 0.74, 0.58)
        // ellipse ears at the sides (behind the head)
        CharKit.ellipse(&ctx, c.x - r*0.96, c.y + r*0.02, r*0.3, r*0.2, .color(shade))
        CharKit.ellipse(&ctx, c.x + r*0.96, c.y + r*0.02, r*0.3, r*0.2, .color(shade))
        // two small cream horns on top
        CharKit.ellipse(&ctx, c.x - r*0.42, c.y - r*0.92, r*0.1, r*0.2, .color(hornSh))
        CharKit.ellipse(&ctx, c.x + r*0.42, c.y - r*0.92, r*0.1, r*0.2, .color(hornSh))
        CharKit.ellipse(&ctx, c.x - r*0.42, c.y - r*0.95, r*0.08, r*0.16, .color(horn))
        CharKit.ellipse(&ctx, c.x + r*0.42, c.y - r*0.95, r*0.08, r*0.16, .color(horn))
        CharKit.head(&ctx, c, r, white, shade)
        // one asymmetric dark patch over the upper-left of the head
        ctx.fill(Path(ellipseIn: CGRect(x: c.x - r*0.82, y: c.y - r*0.68,
                                        width: r*0.72, height: r*0.56)),
                 with: .color(dark))
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.34, r*0.16, a)
        // pink oval muzzle with two nostril dots
        CharKit.ellipse(&ctx, c.x, c.y + r*0.36, r*0.38, r*0.24, .color(col(0.95, 0.7, 0.72)))
        CharKit.circle(&ctx, c.x - r*0.14, c.y + r*0.34, r*0.06, col(0.7, 0.46, 0.5))
        CharKit.circle(&ctx, c.x + r*0.14, c.y + r*0.34, r*0.06, col(0.7, 0.46, 0.5))
        return (c, r)
    }
}
