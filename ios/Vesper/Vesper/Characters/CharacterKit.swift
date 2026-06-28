//  CharacterKit.swift
//  Vesper — the 2D cartoon-character framework (the iOS analogue of the desktop
//  char_base.py kit). Characters are drawn with a SwiftUI Canvas; shared
//  primitives here keep each character tiny and consistent: an aura glow, a soft
//  radial head, big glossy blinking eyes, blush and a smile/open mouth. Each
//  character breathes with the breath, sways gently, blinks and (in Sleep) moves
//  its mouth to the narration.

import SwiftUI

/// Per-frame animation inputs for a character.
struct CharAnim {
    var breath: Double = 0     // 0..1 lung volume (gentle bob / scale)
    var blink: Double = 0      // 0..1, 1 = eyes closed
    var sway: Double = 0       // -1..1 slow side sway
    var mouth: Double = 0      // 0..1 mouth openness (lip-sync)
    var t: Double = 0          // free-running seconds
    var hue: Color = Theme.accent
    var drowsy: Double = 0     // 0..1 sleepiness (Sleep wind-down): droopy lids

    /// Derive the idle motion (blink/sway) from time + the breath state. As
    /// `drowsy` rises the blinks lengthen into slow, sleepy blinks.
    static func make(_ state: BreathState, t: Double, mouth: Double, hue: Color,
                     drowsy: Double = 0) -> CharAnim {
        let dur = 0.16 + 0.30 * drowsy          // sleepy blinks last longer
        let cycle = t.truncatingRemainder(dividingBy: 4.5)
        let blink = cycle > (4.5 - dur) ? sin((cycle - (4.5 - dur)) / dur * .pi) : 0
        return CharAnim(breath: state.volume, blink: max(0, blink),
                        sway: sin(t * 0.5), mouth: mouth, t: t, hue: hue, drowsy: drowsy)
    }
}

/// Anything that can draw itself into a Canvas. `top` is the y of the crown,
/// used by the view to vertically centre tall characters (giraffe, etc.).
protocol CharacterDrawer {
    var name: String { get }
    /// Draw centred in `size`; return the head centre and radius.
    @discardableResult
    func draw(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) -> (CGPoint, CGFloat)
}

// MARK: - shared drawing helpers (the "B" kit)

enum CharKit {
    /// Smoothstep easing (0..1) — gives blinks and lip-sync a soft, natural feel.
    static func smooth(_ x: Double) -> Double {
        let t = max(0, min(1, x)); return t * t * (3 - 2 * t)
    }

    /// A soft contact shadow on the "ground" beneath the character, so it sits in
    /// the scene rather than floating. Breathes subtly with the breath.
    static func contactShadow(_ ctx: inout GraphicsContext, _ size: CGSize, _ a: CharAnim) {
        let w = min(size.width, size.height)
        let cx = size.width / 2 + CGFloat(a.sway) * w * 0.02
        let cy = size.height * 0.86
        let sw = w * (0.26 + 0.02 * CGFloat(a.breath))
        ctx.fill(Path(ellipseIn: CGRect(x: cx - sw, y: cy - sw * 0.16,
                                        width: sw * 2, height: sw * 0.32)),
                 with: .radialGradient(Gradient(colors: [.black.opacity(0.28), .clear]),
                                       center: CGPoint(x: cx, y: cy), startRadius: 0, endRadius: sw))
    }

    /// Head centre + radius for a character, with a gentle breath bob.
    static func headBox(_ size: CGSize, _ a: CharAnim, scale: CGFloat = 0.34,
                        ypos: CGFloat = 0.5) -> (CGPoint, CGFloat) {
        let r = min(size.width, size.height) * scale
        let bob = CGFloat(a.breath) * r * 0.05
        let cx = size.width / 2 + CGFloat(a.sway) * r * 0.05
        let cy = size.height * ypos - bob
        return (CGPoint(x: cx, y: cy), r)
    }

    /// Soft aura glow behind the head.
    static func aura(_ ctx: inout GraphicsContext, _ c: CGPoint, _ r: CGFloat,
                     _ hue: Color, _ breath: Double) {
        let rr = r * (1.7 + 0.12 * CGFloat(breath))
        let rect = CGRect(x: c.x - rr, y: c.y - rr, width: rr * 2, height: rr * 2)
        ctx.fill(Path(ellipseIn: rect), with: .radialGradient(
            Gradient(colors: [hue.opacity(0.18), .clear]),
            center: c, startRadius: r * 0.6, endRadius: rr))
    }

    /// A round head with a soft top-lit radial gradient, a chin ambient-occlusion
    /// shadow for volume, and a glossy rim highlight at the upper-left — all
    /// clipped to the head silhouette so every character reads as 3D.
    static func head(_ ctx: inout GraphicsContext, _ c: CGPoint, _ r: CGFloat,
                     _ light: Color, _ dark: Color) {
        let rect = CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)
        // base, top-lit
        ctx.fill(Path(ellipseIn: rect), with: .radialGradient(
            Gradient(colors: [light, dark]),
            center: CGPoint(x: c.x, y: c.y - r * 0.3),
            startRadius: 0, endRadius: r * 1.2))
        // chin ambient occlusion (darker toward the bottom of the head)
        ctx.fill(Path(ellipseIn: rect), with: .radialGradient(
            Gradient(colors: [.clear, dark.opacity(0.26)]),
            center: CGPoint(x: c.x, y: c.y + r * 0.35),
            startRadius: r * 0.3, endRadius: r * 1.1))
        // glossy rim highlight, upper-left
        ctx.fill(Path(ellipseIn: rect), with: .radialGradient(
            Gradient(colors: [.white.opacity(0.18), .clear]),
            center: CGPoint(x: c.x - r * 0.4, y: c.y - r * 0.5),
            startRadius: 0, endRadius: r * 0.72))
    }

    static func ellipse(_ ctx: inout GraphicsContext, _ cx: CGFloat, _ cy: CGFloat,
                        _ w: CGFloat, _ h: CGFloat, _ color: GraphicsContext.Shading) {
        ctx.fill(Path(ellipseIn: CGRect(x: cx - w, y: cy - h, width: w * 2, height: h * 2)), with: color)
    }

    static func circle(_ ctx: inout GraphicsContext, _ cx: CGFloat, _ cy: CGFloat,
                       _ r: CGFloat, _ color: Color) {
        ellipse(&ctx, cx, cy, r, r, .color(color))
    }

    /// Two big glossy eyes that blink. The lid closes with smoothstep easing (so
    /// the blink feels soft, not mechanical) and each eye gets an upper sheen plus
    /// two catchlights for a wet, alive look.
    static func eyes(_ ctx: inout GraphicsContext, _ cx: CGFloat, _ eyeY: CGFloat,
                     _ spacing: CGFloat, _ eyeR: CGFloat, _ a: CharAnim,
                     dark: Color = Color(white: 0.07)) {
        let e = smooth(a.blink)
        let openH = eyeR * CGFloat(max(0.08, 1 - e))
        let lid = CGFloat(min(0.6, a.drowsy * 0.6))      // sleepy upper-lid droop
        for side in [-1.0, 1.0] {
            let ex = cx + CGFloat(side) * spacing
            let cy = eyeY + openH * lid                  // visible eye slides under the lid
            let hh = openH * (1 - lid)
            ellipse(&ctx, ex, cy, eyeR, hh, .color(dark))
            if e < 0.6 && lid < 0.55 {
                // soft upper sheen across the top of the visible eye
                ctx.fill(Path(ellipseIn: CGRect(x: ex - eyeR * 0.82, y: cy - hh * 0.92,
                                                width: eyeR * 1.64, height: hh * 0.9)),
                         with: .linearGradient(Gradient(colors: [.white.opacity(0.16), .clear]),
                                               startPoint: CGPoint(x: ex, y: cy - hh),
                                               endPoint: CGPoint(x: ex, y: cy)))
                // catchlights
                circle(&ctx, ex - eyeR * 0.22, cy - hh * 0.5, eyeR * 0.26, .white.opacity(0.92))
                circle(&ctx, ex + eyeR * 0.28, cy + hh * 0.1, eyeR * 0.13, .white.opacity(0.5))
            }
        }
    }

    /// Rosy cheeks.
    static func blush(_ ctx: inout GraphicsContext, _ cx: CGFloat, _ cy: CGFloat,
                      _ spacing: CGFloat, _ r: CGFloat, _ hue: Color = .pink) {
        for side in [-1.0, 1.0] {
            ellipse(&ctx, cx + CGFloat(side) * spacing, cy, r, r * 0.62,
                    .color(hue.opacity(0.28)))
        }
    }

    /// A smile (closed) or a soft open mouth, by `a.mouth`.
    static func mouth(_ ctx: inout GraphicsContext, _ cx: CGFloat, _ cy: CGFloat,
                      _ w: CGFloat, _ a: CharAnim, color: Color = Color(white: 0.1)) {
        let m = smooth(a.mouth)             // eased openness, so lip-sync glides
        if m < 0.08 {
            var p = Path()
            let droop = w * CGFloat(0.9 + 0.5 * a.drowsy)   // deeper, contented smile when sleepy
            p.move(to: CGPoint(x: cx - w, y: cy))
            p.addQuadCurve(to: CGPoint(x: cx + w, y: cy),
                           control: CGPoint(x: cx, y: cy + droop))
            ctx.stroke(p, with: .color(color), lineWidth: max(1.4, w * 0.16))
        } else {
            let h = w * CGFloat(0.4 + m)
            ellipse(&ctx, cx, cy + h * 0.4, w * 0.7, h, .color(color))
            ellipse(&ctx, cx, cy + h * 0.55, w * 0.42, h * 0.5, .color(Color(red: 0.8, green: 0.4, blue: 0.45)))
        }
    }

    /// A little triangular nose.
    static func nose(_ ctx: inout GraphicsContext, _ cx: CGFloat, _ cy: CGFloat,
                     _ w: CGFloat, _ color: Color) {
        var p = Path()
        p.move(to: CGPoint(x: cx - w, y: cy))
        p.addLine(to: CGPoint(x: cx + w, y: cy))
        p.addLine(to: CGPoint(x: cx, y: cy + w))
        p.closeSubpath()
        ctx.fill(p, with: .color(color))
    }

    /// A filled triangle.
    static func tri(_ ctx: inout GraphicsContext, _ a: CGPoint, _ b: CGPoint,
                    _ c: CGPoint, _ color: Color) {
        var p = Path(); p.move(to: a); p.addLine(to: b); p.addLine(to: c)
        p.closeSubpath(); ctx.fill(p, with: .color(color))
    }

    /// Whiskers fanning from a muzzle point, `side` = -1 / +1.
    static func whiskers(_ ctx: inout GraphicsContext, _ cx: CGFloat, _ cy: CGFloat,
                         _ r: CGFloat, _ side: CGFloat, _ color: Color) {
        for k in -1...1 {
            var p = Path()
            p.move(to: CGPoint(x: cx + side * r * 0.18, y: cy + CGFloat(k) * r * 0.05))
            p.addLine(to: CGPoint(x: cx + side * r * 0.95,
                                  y: cy + CGFloat(k) * r * 0.16 - r * 0.02))
            ctx.stroke(p, with: .color(color.opacity(0.55)), lineWidth: max(1, r * 0.02))
        }
    }

    /// A pointed ear (triangle-ish), `side` = -1 left / +1 right.
    static func ear(_ ctx: inout GraphicsContext, _ c: CGPoint, _ r: CGFloat,
                    _ side: CGFloat, outer: Color, inner: Color,
                    spread: CGFloat = 0.62, up: CGFloat = 0.95, sz: CGFloat = 0.5) {
        let base = CGPoint(x: c.x + side * r * spread, y: c.y - r * up)
        var p = Path()
        p.move(to: CGPoint(x: base.x - r * sz * 0.5, y: base.y + r * sz * 0.4))
        p.addLine(to: CGPoint(x: base.x + side * r * sz * 0.2, y: base.y - r * sz))
        p.addLine(to: CGPoint(x: base.x + r * sz * 0.5, y: base.y + r * sz * 0.3))
        p.closeSubpath()
        ctx.fill(p, with: .color(outer))
        ctx.fill(p, with: .color(inner.opacity(0.0)))  // placeholder for inner-ear tint
    }
}
