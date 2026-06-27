//  CharactersMore.swift
//  Vesper — more of the cast (Owl, Penguin, Frog, Sloth, Mouse, Lion). Same
//  CharKit primitives; a few draw their own eyes where the standard pair doesn't
//  fit (owl discs, frog bulges).

import SwiftUI

private func c2(_ r: Double, _ g: Double, _ b: Double) -> Color { Color(red: r, green: g, blue: b) }

struct OwlChar: CharacterDrawer {
    let name = "Owl"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let body = c2(0.55, 0.45, 0.62), dark = c2(0.4, 0.32, 0.48)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.7, y: c.y - r*0.6),
                    CGPoint(x: c.x - r*0.45, y: c.y - r*1.15),
                    CGPoint(x: c.x - r*0.15, y: c.y - r*0.7), body)
        CharKit.tri(&ctx, CGPoint(x: c.x + r*0.7, y: c.y - r*0.6),
                    CGPoint(x: c.x + r*0.45, y: c.y - r*1.15),
                    CGPoint(x: c.x + r*0.15, y: c.y - r*0.7), body)
        CharKit.head(&ctx, c, r, body, dark)
        // facial discs
        let lid = CGFloat(max(0.1, 1 - a.blink))
        for s in [-1.0, 1.0] {
            let ex = c.x + CGFloat(s) * r*0.38
            CharKit.circle(&ctx, ex, c.y - r*0.06, r*0.38, c2(0.92, 0.88, 0.78))
            CharKit.ellipse(&ctx, ex, c.y - r*0.06, r*0.24, r*0.24*lid, .color(c2(0.1, 0.09, 0.12)))
            if a.blink < 0.55 {
                CharKit.circle(&ctx, ex, c.y - r*0.06, r*0.1, a.hue)
                CharKit.circle(&ctx, ex - r*0.05, c.y - r*0.12, r*0.05, .white)
            }
        }
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.08, y: c.y + r*0.12),
                    CGPoint(x: c.x + r*0.08, y: c.y + r*0.12),
                    CGPoint(x: c.x, y: c.y + r*0.34), c2(0.95, 0.74, 0.3))
        return (c, r)
    }
}

struct PenguinChar: CharacterDrawer {
    let name = "Penguin"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        CharKit.head(&ctx, c, r, c2(0.27, 0.31, 0.4), c2(0.13, 0.16, 0.22))
        CharKit.ellipse(&ctx, c.x, c.y + r*0.18, r*0.62, r*0.72, .color(c2(0.95, 0.96, 0.98)))
        CharKit.eyes(&ctx, c.x, c.y - r*0.12, r*0.3, r*0.15, a)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.16, y: c.y + r*0.16),
                    CGPoint(x: c.x + r*0.16, y: c.y + r*0.16),
                    CGPoint(x: c.x, y: c.y + r*0.4), c2(0.96, 0.66, 0.18))
        return (c, r)
    }
}

struct FrogChar: CharacterDrawer {
    let name = "Frog"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let green = c2(0.5, 0.78, 0.34), dark = c2(0.34, 0.6, 0.24)
        // eye bulges on top
        let puff = CGFloat(a.breath) * r * 0.04
        for s in [-1.0, 1.0] {
            let ex = c.x + CGFloat(s) * r*0.42
            CharKit.circle(&ctx, ex, c.y - r*0.78 - puff, r*0.34, green)
        }
        CharKit.head(&ctx, c, r, green, dark)
        for s in [-1.0, 1.0] {
            let ex = c.x + CGFloat(s) * r*0.42
            let lid = CGFloat(max(0.12, 1 - a.blink))
            CharKit.circle(&ctx, ex, c.y - r*0.82 - puff, r*0.2, .white)
            CharKit.ellipse(&ctx, ex, c.y - r*0.82 - puff, r*0.12, r*0.12*lid, .color(c2(0.1, 0.12, 0.1)))
        }
        CharKit.circle(&ctx, c.x - r*0.18, c.y + r*0.16, r*0.05, c2(0.2, 0.4, 0.18))
        CharKit.circle(&ctx, c.x + r*0.18, c.y + r*0.16, r*0.05, c2(0.2, 0.4, 0.18))
        // wide smile
        var p = Path()
        p.move(to: CGPoint(x: c.x - r*0.5, y: c.y + r*0.3))
        p.addQuadCurve(to: CGPoint(x: c.x + r*0.5, y: c.y + r*0.3),
                       control: CGPoint(x: c.x, y: c.y + r*0.62))
        ctx.stroke(p, with: .color(c2(0.22, 0.4, 0.2)), lineWidth: max(1.6, r*0.05))
        return (c, r)
    }
}

struct SlothChar: CharacterDrawer {
    let name = "Sloth"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        CharKit.head(&ctx, c, r, c2(0.78, 0.69, 0.55), c2(0.6, 0.52, 0.4))
        CharKit.ellipse(&ctx, c.x, c.y + r*0.05, r*0.78, r*0.74, .color(c2(0.9, 0.84, 0.72)))
        // dark eye patches
        for s in [-1.0, 1.0] {
            let ex = c.x + CGFloat(s) * r*0.33
            CharKit.ellipse(&ctx, ex, c.y - r*0.02, r*0.26, r*0.34, .color(c2(0.42, 0.32, 0.26)))
        }
        // sleepy half-closed eyes
        let sleepy = max(0.45, a.blink)
        var aa = a; aa.blink = sleepy
        CharKit.eyes(&ctx, c.x, c.y, r*0.33, r*0.13, aa)
        CharKit.circle(&ctx, c.x, c.y + r*0.26, r*0.08, c2(0.3, 0.22, 0.18))
        CharKit.mouth(&ctx, c.x, c.y + r*0.46, r*0.13, a)
        return (c, r)
    }
}

struct MouseChar: CharacterDrawer {
    let name = "Mouse"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let fur = c2(0.72, 0.73, 0.78)
        CharKit.circle(&ctx, c.x - r*0.74, c.y - r*0.66, r*0.42, fur)
        CharKit.circle(&ctx, c.x + r*0.74, c.y - r*0.66, r*0.42, fur)
        CharKit.circle(&ctx, c.x - r*0.74, c.y - r*0.66, r*0.26, c2(0.95, 0.78, 0.82))
        CharKit.circle(&ctx, c.x + r*0.74, c.y - r*0.66, r*0.26, c2(0.95, 0.78, 0.82))
        CharKit.head(&ctx, c, r, fur, c2(0.52, 0.53, 0.6))
        CharKit.eyes(&ctx, c.x, c.y - r*0.04, r*0.36, r*0.16, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.24, r*0.55, r*0.15, .pink)
        CharKit.whiskers(&ctx, c.x, c.y + r*0.32, r, -1, c2(0.8, 0.8, 0.85))
        CharKit.whiskers(&ctx, c.x, c.y + r*0.32, r, 1, c2(0.8, 0.8, 0.85))
        CharKit.ellipse(&ctx, c.x, c.y + r*0.26, r*0.08, r*0.06, .color(c2(0.95, 0.55, 0.62)))
        CharKit.mouth(&ctx, c.x, c.y + r*0.42, r*0.12, a)
        return (c, r)
    }
}

struct LionChar: CharacterDrawer {
    let name = "Lion"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        // scalloped mane ring
        let mane = c2(0.85, 0.55, 0.2), maneDark = c2(0.66, 0.4, 0.14)
        let n = 13
        for i in 0..<n {
            let ang = Double(i) / Double(n) * 2 * .pi + a.t * 0.05
            let mx = c.x + CGFloat(cos(ang)) * r * 1.32
            let my = c.y + CGFloat(sin(ang)) * r * 1.32
            CharKit.circle(&ctx, mx, my, r*0.42, i % 2 == 0 ? mane : maneDark)
        }
        CharKit.head(&ctx, c, r*1.18, mane, maneDark)
        CharKit.head(&ctx, c, r, c2(0.96, 0.82, 0.56), c2(0.86, 0.68, 0.42))
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.4, r*0.16, a)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.32, r*0.4, r*0.3, .color(c2(0.99, 0.92, 0.78)))
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.12, y: c.y + r*0.2),
                    CGPoint(x: c.x + r*0.12, y: c.y + r*0.2),
                    CGPoint(x: c.x, y: c.y + r*0.32), c2(0.5, 0.32, 0.3))
        CharKit.whiskers(&ctx, c.x, c.y + r*0.34, r, -1, .white)
        CharKit.whiskers(&ctx, c.x, c.y + r*0.34, r, 1, .white)
        CharKit.mouth(&ctx, c.x, c.y + r*0.46, r*0.15, a)
        return (c, r)
    }
}
