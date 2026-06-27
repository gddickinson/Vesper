//  OrbView.swift
//  Vesper — the breathing orb (port of gui/scenes.OrbScene).
//
//  A soft, layered glow whose radius follows the breath `volume`, a faint guide
//  ring, a travelling cycle-guide dot, and a thin session-progress arc. Drawn
//  with a SwiftUI Canvas so it stays smooth at 60fps and costs almost nothing.

import SwiftUI

struct OrbView: View {
    let state: BreathState
    let progress: Double      // 0..1 session progress (for the arc)
    let animT: Double         // free-running time for tiny shimmer

    var body: some View {
        Canvas { ctx, size in
            let c = CGPoint(x: size.width / 2, y: size.height / 2)
            let base = min(size.width, size.height) * 0.34
            let vol = CGFloat(state.volume)
            // radius eases between 38% (empty) and 100% (full)
            let r = base * (0.38 + 0.62 * vol)
            let hue = Theme.phaseColor(state.phase, state.progress)

            // faint guide ring at full extent
            let ringRect = CGRect(x: c.x - base, y: c.y - base, width: base * 2, height: base * 2)
            ctx.stroke(Path(ellipseIn: ringRect),
                       with: .color(Theme.faint.opacity(0.35)), lineWidth: 1)

            // layered soft glow (outer → inner)
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

            // the core orb
            let coreRect = CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)
            ctx.fill(Path(ellipseIn: coreRect),
                     with: .radialGradient(
                        Gradient(colors: [hue.opacity(0.95), hue.opacity(0.45), hue.opacity(0.12)]),
                        center: CGPoint(x: c.x, y: c.y - r * 0.15),
                        startRadius: 0, endRadius: r))

            // travelling cycle-guide dot around the guide ring
            let ang = state.cycleFrac * 2 * .pi - .pi / 2
            let dot = CGPoint(x: c.x + cos(ang) * base, y: c.y + sin(ang) * base)
            let dotR: CGFloat = 5
            ctx.fill(Path(ellipseIn: CGRect(x: dot.x - dotR, y: dot.y - dotR,
                                            width: dotR * 2, height: dotR * 2)),
                     with: .color(Theme.text.opacity(0.85)))

            // session-progress arc just outside the ring
            if progress > 0 {
                var arc = Path()
                let ar = base * 1.22
                arc.addArc(center: c, radius: ar, startAngle: .degrees(-90),
                           endAngle: .degrees(-90 + 360 * progress), clockwise: false)
                ctx.stroke(arc, with: .color(Theme.accent.opacity(0.4)), lineWidth: 2)
            }
        }
        .allowsHitTesting(false)
    }
}
