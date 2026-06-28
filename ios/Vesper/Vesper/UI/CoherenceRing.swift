//  CoherenceRing.swift
//  Vesper — a small ring that fills and warms from amber → green as the heart-
//  rhythm coherence score rises. Calm and subtle; used in the Meditate workspace.

import SwiftUI

struct CoherenceRing: View {
    let value: Double          // 0…1 coherence

    var body: some View {
        Canvas { ctx, size in
            let c = CGPoint(x: size.width / 2, y: size.height / 2)
            let r = min(size.width, size.height) / 2 - 4
            let rect = CGRect(x: c.x - r, y: c.y - r, width: r * 2, height: r * 2)
            // faint track
            ctx.stroke(Path(ellipseIn: rect), with: .color(Theme.border), lineWidth: 5)
            // filled arc
            let v = max(0, min(1, value))
            if v > 0.001 {
                var arc = Path()
                arc.addArc(center: c, radius: r, startAngle: .degrees(-90),
                           endAngle: .degrees(-90 + 360 * v), clockwise: false)
                ctx.stroke(arc, with: .color(Self.color(v)),
                           style: StrokeStyle(lineWidth: 5, lineCap: .round))
            }
        }
    }

    /// Amber (low) → green (high).
    static func color(_ v: Double) -> Color {
        // hue 0.09 (amber) → 0.34 (green)
        Color(hue: 0.09 + 0.25 * v, saturation: 0.7, brightness: 0.85)
    }
}
