//  Theme.swift
//  Vesper — the soothing low-contrast night palette (port of gui/theme.py).

import SwiftUI

enum Theme {
    static let bg        = Color(red: 0.043, green: 0.063, blue: 0.094)   // deep night
    static let bgPanel   = Color(red: 0.075, green: 0.102, blue: 0.149)
    static let bgCard    = Color(red: 0.102, green: 0.133, blue: 0.184)
    static let border    = Color(red: 0.180, green: 0.220, blue: 0.290)
    static let text      = Color(red: 0.886, green: 0.910, blue: 0.945)
    static let muted     = Color(red: 0.600, green: 0.655, blue: 0.730)
    static let faint     = Color(red: 0.380, green: 0.430, blue: 0.510)
    static let accent    = Color(red: 0.525, green: 0.902, blue: 0.749)   // calm mint
    static let accentWarm = Color(red: 0.964, green: 0.776, blue: 0.486)  // warm amber

    /// Hue that drifts gently with the breath phase (cool inhale → warm exhale).
    static func phaseColor(_ phase: BreathPhase, _ progress: Double) -> Color {
        switch phase {
        case .inhale:    return blend(accent, accentWarm, progress * 0.4)
        case .holdFull:  return blend(accent, accentWarm, 0.4)
        case .exhale:    return blend(accentWarm, accent, progress * 0.4)
        case .holdEmpty: return accent
        }
    }

    static func blend(_ a: Color, _ b: Color, _ t: Double) -> Color {
        let tt = max(0, min(1, t))
        return Color(.sRGB,
            red: lerp(a, b, tt, \.r), green: lerp(a, b, tt, \.g),
            blue: lerp(a, b, tt, \.b), opacity: 1)
    }

    private static func lerp(_ a: Color, _ b: Color, _ t: Double,
                             _ kp: KeyPath<RGBA, Double>) -> Double {
        let ca = a.rgba, cb = b.rgba
        return ca[keyPath: kp] + (cb[keyPath: kp] - ca[keyPath: kp]) * t
    }
}

struct RGBA { let r: Double; let g: Double; let b: Double; let a: Double }

extension Color {
    var rgba: RGBA {
        #if canImport(UIKit)
        let ui = UIColor(self)
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        ui.getRed(&r, green: &g, blue: &b, alpha: &a)
        return RGBA(r: Double(r), g: Double(g), b: Double(b), a: Double(a))
        #else
        return RGBA(r: 0, g: 0, b: 0, a: 1)
        #endif
    }
}
