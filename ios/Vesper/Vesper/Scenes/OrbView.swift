//  OrbView.swift
//  Vesper — the breathing orb.
//
//  A fluid, self-lit GPU orb (Shaders.metal ▸ breathingOrb) whose core swells
//  with the breath, with a Canvas overlay for the faint guide ring, the
//  travelling cycle-guide dot and the session-progress arc. Falls back to a
//  pure-Canvas orb if Metal is unavailable (so it always renders).

import SwiftUI
import Metal

struct OrbView: View {
    let state: BreathState
    let progress: Double      // 0..1 session progress (for the arc)
    let animT: Double         // free-running time for shimmer / churn

    /// Metal present? (false on the rare device with no GPU → Canvas fallback.)
    private static let metalOK = MTLCreateSystemDefaultDevice() != nil

    var body: some View {
        GeometryReader { geo in
            ZStack {
                if Self.metalOK {
                    Rectangle()
                        .fill(Color.white.opacity(0.0015))     // keep the layer rasterised
                        .colorEffect(ShaderLibrary.breathingOrb(
                            .float2(geo.size),
                            .float(Float(animT.truncatingRemainder(dividingBy: 1000))),
                            .float(Float(state.volume)),
                            .color(Theme.phaseColor(state.phase, state.progress))))
                    guides(geo.size)
                } else {
                    legacyOrb(geo.size)
                }
            }
        }
        .allowsHitTesting(false)
    }

    // MARK: guide ring + cycle dot + progress arc (drawn over the shader)

    private func guides(_ size: CGSize) -> some View {
        Canvas { ctx, _ in
            let c = CGPoint(x: size.width / 2, y: size.height / 2)
            let base = min(size.width, size.height) * 0.34

            let ringRect = CGRect(x: c.x - base, y: c.y - base, width: base * 2, height: base * 2)
            ctx.stroke(Path(ellipseIn: ringRect),
                       with: .color(Theme.faint.opacity(0.30)), lineWidth: 1)

            let ang = state.cycleFrac * 2 * .pi - .pi / 2
            let dot = CGPoint(x: c.x + cos(ang) * base, y: c.y + sin(ang) * base)
            let dotR: CGFloat = 5
            ctx.fill(Path(ellipseIn: CGRect(x: dot.x - dotR, y: dot.y - dotR,
                                            width: dotR * 2, height: dotR * 2)),
                     with: .color(Theme.text.opacity(0.85)))

            if progress > 0 {
                var arc = Path()
                let ar = base * 1.22
                arc.addArc(center: c, radius: ar, startAngle: .degrees(-90),
                           endAngle: .degrees(-90 + 360 * progress), clockwise: false)
                ctx.stroke(arc, with: .color(Theme.accent.opacity(0.4)), lineWidth: 2)
            }
        }
    }

    // MARK: pure-Canvas fallback (the original orb)

    private func legacyOrb(_ size: CGSize) -> some View {
        Canvas { ctx, _ in
            let c = CGPoint(x: size.width / 2, y: size.height / 2)
            let base = min(size.width, size.height) * 0.34
            let vol = CGFloat(state.volume)
            let r = base * (0.38 + 0.62 * vol)
            let hue = Theme.phaseColor(state.phase, state.progress)

            for i in stride(from: 5, through: 1, by: -1) {
                let f = CGFloat(i)
                let rr = r * (1.0 + f * 0.16)
                let rect = CGRect(x: c.x - rr, y: c.y - rr, width: rr * 2, height: rr * 2)
                let shimmer = 0.04 * sin(animT * 0.8 + Double(i))
                let alpha = (0.10 + 0.02 * (5 - f)) + CGFloat(shimmer)
                ctx.fill(Path(ellipseIn: rect),
                         with: .radialGradient(
                            Gradient(colors: [hue.opacity(Double(alpha)), .clear]),
                            center: c, startRadius: rr * 0.2, endRadius: rr))
            }
            let coreRect = CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)
            ctx.fill(Path(ellipseIn: coreRect),
                     with: .radialGradient(
                        Gradient(colors: [hue.opacity(0.95), hue.opacity(0.45), hue.opacity(0.12)]),
                        center: CGPoint(x: c.x, y: c.y - r * 0.15),
                        startRadius: 0, endRadius: r))
            guidesInline(&ctx, size)
        }
    }

    private func guidesInline(_ ctx: inout GraphicsContext, _ size: CGSize) {
        let c = CGPoint(x: size.width / 2, y: size.height / 2)
        let base = min(size.width, size.height) * 0.34
        let ringRect = CGRect(x: c.x - base, y: c.y - base, width: base * 2, height: base * 2)
        ctx.stroke(Path(ellipseIn: ringRect),
                   with: .color(Theme.faint.opacity(0.35)), lineWidth: 1)
        let ang = state.cycleFrac * 2 * .pi - .pi / 2
        let dot = CGPoint(x: c.x + cos(ang) * base, y: c.y + sin(ang) * base)
        let dotR: CGFloat = 5
        ctx.fill(Path(ellipseIn: CGRect(x: dot.x - dotR, y: dot.y - dotR,
                                        width: dotR * 2, height: dotR * 2)),
                 with: .color(Theme.text.opacity(0.85)))
        if progress > 0 {
            var arc = Path()
            let ar = base * 1.22
            arc.addArc(center: c, radius: ar, startAngle: .degrees(-90),
                       endAngle: .degrees(-90 + 360 * progress), clockwise: false)
            ctx.stroke(arc, with: .color(Theme.accent.opacity(0.4)), lineWidth: 2)
        }
    }
}
