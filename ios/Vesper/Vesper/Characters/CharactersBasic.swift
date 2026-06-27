//  CharactersBasic.swift
//  Vesper — the everyday cast (Cat, Dog, Bunny, Bear, Panda, Fox). Each is a
//  small CharacterDrawer using the shared CharKit primitives; cute, recognizable,
//  and breath-animated. Add a character by adding a struct and listing it in
//  Characters.all.

import SwiftUI

private func col(_ r: Double, _ g: Double, _ b: Double) -> Color {
    Color(red: r, green: g, blue: b)
}

struct CatChar: CharacterDrawer {
    let name = "Cat"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let fur = col(0.66, 0.69, 0.74), dark = col(0.42, 0.46, 0.52)
        // ears
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.7, y: c.y - r*0.55),
                    CGPoint(x: c.x - r*0.3, y: c.y - r*1.25),
                    CGPoint(x: c.x - r*0.05, y: c.y - r*0.7), fur)
        CharKit.tri(&ctx, CGPoint(x: c.x + r*0.7, y: c.y - r*0.55),
                    CGPoint(x: c.x + r*0.3, y: c.y - r*1.25),
                    CGPoint(x: c.x + r*0.05, y: c.y - r*0.7), fur)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.5, y: c.y - r*0.7),
                    CGPoint(x: c.x - r*0.3, y: c.y - r*1.05),
                    CGPoint(x: c.x - r*0.16, y: c.y - r*0.75), col(0.95, 0.7, 0.78))
        CharKit.tri(&ctx, CGPoint(x: c.x + r*0.5, y: c.y - r*0.7),
                    CGPoint(x: c.x + r*0.3, y: c.y - r*1.05),
                    CGPoint(x: c.x + r*0.16, y: c.y - r*0.75), col(0.95, 0.7, 0.78))
        CharKit.head(&ctx, c, r, fur, dark)
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.42, r*0.17, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.22, r*0.6, r*0.18, .pink)
        CharKit.whiskers(&ctx, c.x, c.y + r*0.3, r, -1, .white)
        CharKit.whiskers(&ctx, c.x, c.y + r*0.3, r, 1, .white)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.08, y: c.y + r*0.22),
                    CGPoint(x: c.x + r*0.08, y: c.y + r*0.22),
                    CGPoint(x: c.x, y: c.y + r*0.32), col(0.95, 0.6, 0.66))
        CharKit.mouth(&ctx, c.x, c.y + r*0.42, r*0.16, a)
        return (c, r)
    }
}

struct DogChar: CharacterDrawer {
    let name = "Dog"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let fur = col(0.84, 0.66, 0.42), dark = col(0.6, 0.44, 0.26)
        let ear = CGFloat(a.breath) * r * 0.06
        CharKit.ellipse(&ctx, c.x - r*0.86, c.y + r*0.1 + ear, r*0.34, r*0.62, .color(dark))
        CharKit.ellipse(&ctx, c.x + r*0.86, c.y + r*0.1 + ear, r*0.34, r*0.62, .color(dark))
        CharKit.head(&ctx, c, r, fur, col(0.7, 0.52, 0.32))
        CharKit.ellipse(&ctx, c.x, c.y + r*0.34, r*0.5, r*0.42, .color(col(0.95, 0.86, 0.72)))
        CharKit.eyes(&ctx, c.x, c.y - r*0.08, r*0.4, r*0.17, a)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.2, r*0.16, r*0.12, .color(col(0.12, 0.1, 0.1)))
        CharKit.mouth(&ctx, c.x, c.y + r*0.48, r*0.16, a)
        if a.mouth > 0.1 {
            CharKit.ellipse(&ctx, c.x, c.y + r*0.6, r*0.1, r*0.16, .color(col(0.9, 0.45, 0.5)))
        }
        return (c, r)
    }
}

struct BunnyChar: CharacterDrawer {
    let name = "Bunny"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let fur = col(0.96, 0.95, 0.97), shade = col(0.85, 0.84, 0.9)
        let tw = sin(a.t * 3) * r * 0.03
        CharKit.ellipse(&ctx, c.x - r*0.32 + tw, c.y - r*1.05, r*0.18, r*0.6, .color(fur))
        CharKit.ellipse(&ctx, c.x + r*0.32 - tw, c.y - r*1.05, r*0.18, r*0.6, .color(fur))
        CharKit.ellipse(&ctx, c.x - r*0.32 + tw, c.y - r*1.05, r*0.09, r*0.42, .color(col(0.97, 0.78, 0.82)))
        CharKit.ellipse(&ctx, c.x + r*0.32 - tw, c.y - r*1.05, r*0.09, r*0.42, .color(col(0.97, 0.78, 0.82)))
        CharKit.head(&ctx, c, r, fur, shade)
        CharKit.eyes(&ctx, c.x, c.y - r*0.04, r*0.4, r*0.17, a)
        CharKit.blush(&ctx, c.x, c.y + r*0.24, r*0.58, r*0.16, .pink)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.07, y: c.y + r*0.22),
                    CGPoint(x: c.x + r*0.07, y: c.y + r*0.22),
                    CGPoint(x: c.x, y: c.y + r*0.31), col(0.95, 0.6, 0.66))
        CharKit.mouth(&ctx, c.x, c.y + r*0.42, r*0.14, a)
        return (c, r)
    }
}

struct BearChar: CharacterDrawer {
    let name = "Bear"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let fur = col(0.6, 0.45, 0.33), dark = col(0.44, 0.32, 0.22)
        CharKit.circle(&ctx, c.x - r*0.72, c.y - r*0.72, r*0.34, fur)
        CharKit.circle(&ctx, c.x + r*0.72, c.y - r*0.72, r*0.34, fur)
        CharKit.circle(&ctx, c.x - r*0.72, c.y - r*0.72, r*0.18, col(0.72, 0.56, 0.42))
        CharKit.circle(&ctx, c.x + r*0.72, c.y - r*0.72, r*0.18, col(0.72, 0.56, 0.42))
        CharKit.head(&ctx, c, r, fur, dark)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.32, r*0.42, r*0.32, .color(col(0.8, 0.66, 0.52)))
        CharKit.eyes(&ctx, c.x, c.y - r*0.05, r*0.36, r*0.16, a)
        CharKit.ellipse(&ctx, c.x, c.y + r*0.2, r*0.14, r*0.1, .color(col(0.15, 0.1, 0.08)))
        CharKit.mouth(&ctx, c.x, c.y + r*0.46, r*0.15, a)
        return (c, r)
    }
}

struct PandaChar: CharacterDrawer {
    let name = "Panda"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let black = col(0.13, 0.13, 0.16)
        CharKit.circle(&ctx, c.x - r*0.74, c.y - r*0.68, r*0.32, black)
        CharKit.circle(&ctx, c.x + r*0.74, c.y - r*0.68, r*0.32, black)
        CharKit.head(&ctx, c, r, col(0.97, 0.97, 0.98), col(0.84, 0.84, 0.88))
        // eye patches
        for s in [-1.0, 1.0] {
            var p = Path()
            let ex = c.x + CGFloat(s) * r*0.34
            p.addEllipse(in: CGRect(x: ex - r*0.26, y: c.y - r*0.32, width: r*0.42, height: r*0.5))
            ctx.fill(p, with: .color(black))
        }
        CharKit.eyes(&ctx, c.x, c.y - r*0.04, r*0.34, r*0.15, a, dark: .white)
        CharKit.circle(&ctx, c.x, c.y + r*0.22, r*0.1, black)
        CharKit.mouth(&ctx, c.x, c.y + r*0.44, r*0.14, a)
        return (c, r)
    }
}

struct FoxChar: CharacterDrawer {
    let name = "Fox"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let fur = col(0.92, 0.52, 0.24), dark = col(0.74, 0.38, 0.16)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.75, y: c.y - r*0.5),
                    CGPoint(x: c.x - r*0.5, y: c.y - r*1.3),
                    CGPoint(x: c.x - r*0.1, y: c.y - r*0.7), fur)
        CharKit.tri(&ctx, CGPoint(x: c.x + r*0.75, y: c.y - r*0.5),
                    CGPoint(x: c.x + r*0.5, y: c.y - r*1.3),
                    CGPoint(x: c.x + r*0.1, y: c.y - r*0.7), fur)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.55, y: c.y - r*0.7),
                    CGPoint(x: c.x - r*0.45, y: c.y - r*1.1),
                    CGPoint(x: c.x - r*0.2, y: c.y - r*0.78), col(0.18, 0.16, 0.18))
        CharKit.tri(&ctx, CGPoint(x: c.x + r*0.55, y: c.y - r*0.7),
                    CGPoint(x: c.x + r*0.45, y: c.y - r*1.1),
                    CGPoint(x: c.x + r*0.2, y: c.y - r*0.78), col(0.18, 0.16, 0.18))
        CharKit.head(&ctx, c, r, fur, dark)
        // white muzzle/cheeks
        CharKit.tri(&ctx, CGPoint(x: c.x, y: c.y - r*0.1),
                    CGPoint(x: c.x - r*0.55, y: c.y + r*0.7),
                    CGPoint(x: c.x + r*0.55, y: c.y + r*0.7), col(0.97, 0.97, 0.98))
        CharKit.eyes(&ctx, c.x, c.y - r*0.08, r*0.4, r*0.16, a)
        CharKit.tri(&ctx, CGPoint(x: c.x - r*0.08, y: c.y + r*0.36),
                    CGPoint(x: c.x + r*0.08, y: c.y + r*0.36),
                    CGPoint(x: c.x, y: c.y + r*0.48), col(0.13, 0.11, 0.12))
        CharKit.mouth(&ctx, c.x, c.y + r*0.56, r*0.13, a)
        return (c, r)
    }
}
