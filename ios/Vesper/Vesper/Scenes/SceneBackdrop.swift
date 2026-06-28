//  SceneBackdrop.swift
//  Vesper — ambient background scenes drawn BEHIND the breath orb. GPU shaders
//  (Shaders.metal) render a drifting night sky, aurora curtains, embers, a warm
//  hearth or a moonlit sea, with gentle CoreMotion tilt parallax. Falls back to
//  the original pure-Canvas scenes when Metal is unavailable, and honours
//  Reduce Motion by holding the animation still.

import SwiftUI
import Metal

enum SceneKind { case none, nightSky, embers, aurora, fireplace, ocean }

struct BackdropView: View {
    let kind: SceneKind

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    private static let metalOK = MTLCreateSystemDefaultDevice() != nil

    var body: some View {
        if kind == .none {
            Color.clear
        } else if Self.metalOK {
            GeometryReader { geo in
                TimelineView(.animation) { tl in
                    let raw = tl.date.timeIntervalSinceReferenceDate
                    let t = Float(reduceMotion ? 0 : raw.truncatingRemainder(dividingBy: 100000))
                    let off = reduceMotion ? .zero : MotionManager.shared.offset
                    Rectangle()
                        .fill(Color.white.opacity(0.0015))         // keep the layer rasterised
                        .colorEffect(shader(geo.size, t, off))
                }
            }
            .allowsHitTesting(false)
        } else {
            legacyCanvas
        }
    }

    private func shader(_ size: CGSize, _ t: Float, _ off: CGSize) -> Shader {
        let fn: ShaderFunction
        switch kind {
        case .nightSky:  fn = ShaderLibrary.nightSkyScene
        case .aurora:    fn = ShaderLibrary.auroraScene
        case .embers:    fn = ShaderLibrary.embersScene
        case .fireplace: fn = ShaderLibrary.fireplaceScene
        case .ocean:     fn = ShaderLibrary.oceanScene
        case .none:      fn = ShaderLibrary.nightSkyScene
        }
        return Shader(function: fn, arguments: [
            .float2(size), .float(t),
            .float2(Float(off.width), Float(off.height)),
        ])
    }

    // MARK: pure-Canvas fallback (the original scenes)

    private var legacyCanvas: some View {
        TimelineView(.animation) { tl in
            Canvas { ctx, size in
                let t = reduceMotion ? 0 : tl.date.timeIntervalSinceReferenceDate
                switch kind {
                case .nightSky:           Self.nightSky(ctx, size, t)
                case .embers, .fireplace: Self.embers(ctx, size, t)
                case .aurora, .ocean:     Self.aurora(ctx, size, t)
                case .none:               break
                }
            }
        }
        .allowsHitTesting(false)
    }

    // MARK: deterministic point fields

    private static func seededPoints(_ n: Int, seed: UInt64) -> [(x: Double, y: Double, a: Double, b: Double)] {
        var s = seed
        func rnd() -> Double {
            s = s &* 6364136223846793005 &+ 1442695040888963407
            return Double(s >> 33) / Double(UInt64(1) << 31)
        }
        return (0..<n).map { _ in (rnd(), rnd(), rnd(), rnd()) }
    }

    private static let stars = seededPoints(60, seed: 0x5EED01)
    private static let emberSeeds = seededPoints(28, seed: 0x5EED02)

    // MARK: scenes (Canvas fallback)

    private static func nightSky(_ ctx: GraphicsContext, _ size: CGSize, _ t: Double) {
        let mx = size.width * 0.78, my = size.height * 0.20, mr = 20.0
        ctx.fill(Path(ellipseIn: CGRect(x: mx - mr * 2, y: my - mr * 2, width: mr * 4, height: mr * 4)),
                 with: .radialGradient(Gradient(colors: [.white.opacity(0.18), .clear]),
                                       center: CGPoint(x: mx, y: my), startRadius: 0, endRadius: mr * 2.4))
        ctx.fill(Path(ellipseIn: CGRect(x: mx - mr * 0.6, y: my - mr * 0.6, width: mr * 1.2, height: mr * 1.2)),
                 with: .color(.white.opacity(0.5)))
        for p in stars {
            let x = p.x * size.width
            let y = p.y * size.height * 0.8
            let tw = 0.4 + 0.6 * (0.5 + 0.5 * sin(t * (0.5 + p.b) + p.a * 6))
            let r = 0.6 + p.a * 1.2
            ctx.fill(Path(ellipseIn: CGRect(x: x - r, y: y - r, width: r * 2, height: r * 2)),
                     with: .color(.white.opacity(tw * 0.5)))
        }
    }

    private static func embers(_ ctx: GraphicsContext, _ size: CGSize, _ t: Double) {
        for p in emberSeeds {
            let speed = 0.04 + p.b * 0.05
            let prog = (t * speed + p.a).truncatingRemainder(dividingBy: 1)
            let y = size.height * (1.0 - prog)
            let x = p.x * size.width + sin(t * 0.7 + p.a * 6) * 14
            let fade = sin(prog * .pi)
            let r = 1.0 + p.a * 1.5
            let col = Color(red: 1.0, green: 0.5 + 0.25 * p.a, blue: 0.15)
            ctx.fill(Path(ellipseIn: CGRect(x: x - r, y: y - r, width: r * 2, height: r * 2)),
                     with: .color(col.opacity(fade * 0.5)))
        }
    }

    private static func aurora(_ ctx: GraphicsContext, _ size: CGSize, _ t: Double) {
        let cols: [Color] = [
            Color(red: 0.2, green: 0.8, blue: 0.6),
            Color(red: 0.3, green: 0.55, blue: 0.9),
            Color(red: 0.5, green: 0.85, blue: 0.5),
        ]
        for (i, col) in cols.enumerated() {
            var path = Path()
            let baseY = size.height * (0.22 + Double(i) * 0.12)
            let amp = 26.0 + Double(i) * 8
            path.move(to: CGPoint(x: 0, y: baseY))
            var x = 0.0
            while x <= size.width {
                let y = baseY + sin(x / 90 + t * (0.3 + 0.1 * Double(i)) + Double(i)) * amp
                path.addLine(to: CGPoint(x: x, y: y))
                x += 12
            }
            path.addLine(to: CGPoint(x: size.width, y: size.height))
            path.addLine(to: CGPoint(x: 0, y: size.height))
            path.closeSubpath()
            ctx.fill(path, with: .linearGradient(
                Gradient(colors: [col.opacity(0.16), .clear]),
                startPoint: CGPoint(x: size.width / 2, y: baseY - amp),
                endPoint: CGPoint(x: size.width / 2, y: baseY + amp * 2)))
        }
    }
}
