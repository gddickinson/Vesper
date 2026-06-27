//  CharactersRobots.swift
//  Vesper — the robots & visitors cast (Robot, Bot, Alien, Martian). Each is a
//  small CharacterDrawer using the shared CharKit primitives plus a couple of
//  local helpers (glowing dots, antennae, almond eyes). Add a character by adding
//  a struct and listing it in Characters.all.

import SwiftUI

private func col(_ r: Double, _ g: Double, _ b: Double) -> Color {
    Color(red: r, green: g, blue: b)
}

/// A bright dot with a soft halo — a glowing LED / antenna tip / robot eye.
private func glowDot(_ ctx: inout GraphicsContext, _ p: CGPoint, _ r: CGFloat, _ color: Color) {
    let g = r * 2.6
    ctx.fill(Path(ellipseIn: CGRect(x: p.x - g, y: p.y - g, width: g * 2, height: g * 2)),
             with: .radialGradient(Gradient(colors: [color.opacity(0.55), .clear]),
                                   center: p, startRadius: 0, endRadius: g))
    ctx.fill(Path(ellipseIn: CGRect(x: p.x - r, y: p.y - r, width: r * 2, height: r * 2)),
             with: .color(color))
    ctx.fill(Path(ellipseIn: CGRect(x: p.x - r * 0.45, y: p.y - r * 0.55,
                                    width: r * 0.8, height: r * 0.8)),
             with: .color(.white.opacity(0.75)))
}

/// A thin stalk from `base` to `top`, capped by a knob (glowing or matte).
private func antenna(_ ctx: inout GraphicsContext, _ base: CGPoint, _ top: CGPoint,
                     _ knobR: CGFloat, stalk: Color, knob: Color, glow: Bool = true) {
    var p = Path(); p.move(to: base); p.addLine(to: top)
    ctx.stroke(p, with: .color(stalk), lineWidth: max(1.6, knobR * 0.55))
    if glow {
        glowDot(&ctx, top, knobR, knob)
    } else {
        ctx.fill(Path(ellipseIn: CGRect(x: top.x - knobR, y: top.y - knobR,
                                        width: knobR * 2, height: knobR * 2)),
                 with: .color(knob))
        ctx.fill(Path(ellipseIn: CGRect(x: top.x - knobR * 0.4, y: top.y - knobR * 0.55,
                                        width: knobR * 0.7, height: knobR * 0.7)),
                 with: .color(.white.opacity(0.6)))
    }
}

/// A tilted almond shape (two facing quad curves), rotated `tilt` radians.
private func almond(_ ctx: inout GraphicsContext, _ cx: CGFloat, _ cy: CGFloat,
                    _ w: CGFloat, _ h: CGFloat, _ tilt: CGFloat, _ color: Color) {
    var p = Path()
    p.move(to: CGPoint(x: cx - w, y: cy))
    p.addQuadCurve(to: CGPoint(x: cx + w, y: cy), control: CGPoint(x: cx, y: cy - h))
    p.addQuadCurve(to: CGPoint(x: cx - w, y: cy), control: CGPoint(x: cx, y: cy + h))
    p.closeSubpath()
    let t = CGAffineTransform(translationX: cx, y: cy)
        .rotated(by: tilt)
        .translatedBy(x: -cx, y: -cy)
    ctx.fill(p.applying(t), with: .color(color))
}

// MARK: - Robot — brushed-metal box head, glowing mint eyes, LED mouth

struct RobotChar: CharacterDrawer {
    let name = "Robot"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let mint = col(0.45, 0.96, 0.78)
        // antenna on the crown, tipped with a glowing mint dot
        antenna(&ctx, CGPoint(x: c.x, y: c.y - r),
                CGPoint(x: c.x, y: c.y - r * 1.5), r * 0.12,
                stalk: col(0.55, 0.58, 0.63), knob: mint)
        // brushed-metal rounded-rectangle head
        let headRect = CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)
        ctx.fill(Path(roundedRect: headRect, cornerRadius: r * 0.35),
                 with: .linearGradient(Gradient(colors: [col(0.83, 0.85, 0.89),
                                                         col(0.50, 0.53, 0.59)]),
                                       startPoint: CGPoint(x: c.x, y: c.y - r),
                                       endPoint: CGPoint(x: c.x, y: c.y + r)))
        ctx.stroke(Path(roundedRect: headRect.insetBy(dx: r * 0.05, dy: r * 0.05),
                        cornerRadius: r * 0.3),
                   with: .color(.white.opacity(0.18)), lineWidth: max(1, r * 0.03))
        // rivets in the four corners
        let bolt = col(0.38, 0.41, 0.47)
        for sx in [-1.0, 1.0] {
            for sy in [-1.0, 1.0] {
                let b = CGPoint(x: c.x + CGFloat(sx) * r * 0.76, y: c.y + CGFloat(sy) * r * 0.76)
                ctx.fill(Path(ellipseIn: CGRect(x: b.x - r * 0.09, y: b.y - r * 0.09,
                                                width: r * 0.18, height: r * 0.18)),
                         with: .color(bolt))
                ctx.fill(Path(ellipseIn: CGRect(x: b.x - r * 0.035, y: b.y - r * 0.05,
                                                width: r * 0.08, height: r * 0.08)),
                         with: .color(.white.opacity(0.35)))
            }
        }
        // glowing mint eyes
        let eyeY = c.y - r * 0.12
        for s in [-1.0, 1.0] {
            glowDot(&ctx, CGPoint(x: c.x + CGFloat(s) * r * 0.42, y: eyeY), r * 0.18, mint)
        }
        // LED mouth: a dark display with a row of bright dashes
        let mw = r * 0.95, mh = r * 0.28, my = c.y + r * 0.48
        ctx.fill(Path(roundedRect: CGRect(x: c.x - mw / 2, y: my - mh / 2, width: mw, height: mh),
                      cornerRadius: mh * 0.4),
                 with: .color(col(0.11, 0.13, 0.16)))
        let n = 5
        for i in 0..<n {
            let frac = CGFloat(i) / CGFloat(n - 1)
            let dx = c.x - mw * 0.36 + frac * mw * 0.72
            let lit = 0.45 + 0.55 * sin(a.t * 5 + Double(i) * 0.9)
            let bh = mh * (0.4 + 0.4 * CGFloat(max(0.1, lit)) + 0.4 * CGFloat(a.mouth))
            let bw = mw * 0.07
            ctx.fill(Path(roundedRect: CGRect(x: dx - bw / 2, y: my - min(bh, mh * 0.8) / 2,
                                              width: bw, height: min(bh, mh * 0.8)),
                          cornerRadius: bw * 0.4),
                     with: .color(mint.opacity(0.9)))
        }
        return (c, r)
    }
}

// MARK: - Bot — soft, round, friendly little robot

struct BotChar: CharacterDrawer {
    let name = "Bot"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.30, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        // tiny antenna with a soft glowing dot
        antenna(&ctx, CGPoint(x: c.x, y: c.y - r * 0.97),
                CGPoint(x: c.x, y: c.y - r * 1.34), r * 0.1,
                stalk: col(0.62, 0.7, 0.8), knob: col(0.6, 0.86, 0.96))
        // round light blue-grey head
        CharKit.head(&ctx, c, r, col(0.85, 0.90, 0.96), col(0.59, 0.67, 0.78))
        // a faint visor sheen across the brow
        CharKit.ellipse(&ctx, c.x, c.y - r * 0.42, r * 0.7, r * 0.22, .color(.white.opacity(0.14)))
        // big round dark eyes with bright catchlights
        CharKit.eyes(&ctx, c.x, c.y - r * 0.04, r * 0.4, r * 0.2, a)
        // cool little blush
        CharKit.blush(&ctx, c.x, c.y + r * 0.22, r * 0.56, r * 0.16, col(0.5, 0.8, 0.95))
        // gentle smile
        CharKit.mouth(&ctx, c.x, c.y + r * 0.42, r * 0.16, a)
        return (c, r)
    }
}

// MARK: - Alien — mint teardrop head, big black almond eyes

struct AlienChar: CharacterDrawer {
    let name = "Alien"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.32, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let green = col(0.62, 0.92, 0.55), dark = col(0.34, 0.66, 0.34)
        // two thin antennae with little knobs, swaying
        let sway = CGFloat(sin(a.t * 2)) * r * 0.05
        antenna(&ctx, CGPoint(x: c.x - r * 0.3, y: c.y - r * 0.85),
                CGPoint(x: c.x - r * 0.44 + sway, y: c.y - r * 1.4), r * 0.09,
                stalk: dark, knob: green)
        antenna(&ctx, CGPoint(x: c.x + r * 0.3, y: c.y - r * 0.85),
                CGPoint(x: c.x + r * 0.44 - sway, y: c.y - r * 1.4), r * 0.09,
                stalk: dark, knob: green)
        // teardrop head: wide at the top, narrowing to a small chin
        let topW = r * 1.05, midY = c.y - r * 0.1
        var head = Path()
        head.move(to: CGPoint(x: c.x, y: c.y - r * 1.05))
        head.addQuadCurve(to: CGPoint(x: c.x - topW, y: midY),
                          control: CGPoint(x: c.x - topW * 1.05, y: c.y - r * 0.95))
        head.addQuadCurve(to: CGPoint(x: c.x, y: c.y + r * 1.05),
                          control: CGPoint(x: c.x - r * 0.55, y: c.y + r * 0.95))
        head.addQuadCurve(to: CGPoint(x: c.x + topW, y: midY),
                          control: CGPoint(x: c.x + r * 0.55, y: c.y + r * 0.95))
        head.addQuadCurve(to: CGPoint(x: c.x, y: c.y - r * 1.05),
                          control: CGPoint(x: c.x + topW * 1.05, y: c.y - r * 0.95))
        head.closeSubpath()
        ctx.fill(head, with: .radialGradient(Gradient(colors: [green, dark]),
                                             center: CGPoint(x: c.x, y: c.y - r * 0.3),
                                             startRadius: 0, endRadius: r * 1.3))
        // big black almond eyes, tilted outward, squashing on a blink
        let eyeY = c.y - r * 0.02
        let eh = r * 0.4 * CGFloat(max(0.14, 1 - a.blink))
        almond(&ctx, c.x - r * 0.42, eyeY, r * 0.34, eh, -0.32, col(0.06, 0.08, 0.1))
        almond(&ctx, c.x + r * 0.42, eyeY, r * 0.34, eh, 0.32, col(0.06, 0.08, 0.1))
        if a.blink < 0.55 {
            for s in [-1.0, 1.0] {
                CharKit.ellipse(&ctx, c.x + CGFloat(s) * r * 0.5, eyeY - r * 0.12,
                                r * 0.07, r * 0.1, .color(.white.opacity(0.8)))
            }
        }
        // tiny curious mouth low on the chin
        CharKit.mouth(&ctx, c.x, c.y + r * 0.62, r * 0.09, a, color: col(0.2, 0.4, 0.2))
        return (c, r)
    }
}

// MARK: - Martian — purple cyclops, two antennae, a cheerful smile

struct MartianChar: CharacterDrawer {
    let name = "Martian"
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat) {
        let (c, r) = CharKit.headBox(size, a, scale: 0.32, ypos: 0.54)
        CharKit.aura(&ctx, c, r, a.hue, a.breath)
        let light = col(0.78, 0.6, 0.94), dark = col(0.46, 0.30, 0.66)
        let tip = col(0.97, 0.86, 0.42)
        // two short antennae, each ending in a glowing knob
        antenna(&ctx, CGPoint(x: c.x - r * 0.34, y: c.y - r * 0.9),
                CGPoint(x: c.x - r * 0.46, y: c.y - r * 1.3), r * 0.1, stalk: dark, knob: tip)
        antenna(&ctx, CGPoint(x: c.x + r * 0.34, y: c.y - r * 0.9),
                CGPoint(x: c.x + r * 0.46, y: c.y - r * 1.3), r * 0.1, stalk: dark, knob: tip)
        // round purple head
        CharKit.head(&ctx, c, r, light, dark)
        // single big central cyclops eye, blinking with a.blink
        let eyeC = CGPoint(x: c.x, y: c.y - r * 0.06)
        let ew = r * 0.46
        let eh = ew * CGFloat(max(0.12, 1 - a.blink))
        CharKit.ellipse(&ctx, eyeC.x, eyeC.y, ew, eh, .color(.white))
        if a.blink < 0.6 {
            let irisR = ew * 0.52
            CharKit.ellipse(&ctx, eyeC.x, eyeC.y, irisR, min(irisR, eh * 0.92),
                            .color(col(0.32, 0.58, 0.88)))
            let pupR = ew * 0.26
            CharKit.ellipse(&ctx, eyeC.x, eyeC.y, pupR, min(pupR, eh * 0.6),
                            .color(col(0.05, 0.05, 0.08)))
            CharKit.circle(&ctx, eyeC.x - ew * 0.18, eyeC.y - eh * 0.4,
                           ew * 0.13, .white.opacity(0.92))
        }
        // rosy blush
        CharKit.blush(&ctx, c.x, c.y + r * 0.36, r * 0.56, r * 0.16, .pink)
        // little cheerful smile
        CharKit.mouth(&ctx, c.x, c.y + r * 0.52, r * 0.16, a)
        return (c, r)
    }
}
