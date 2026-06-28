//  StatsView.swift
//  Vesper — a gentle practice summary sheet (sits · minutes · streak + the last
//  few sessions).

import SwiftUI

struct StatsView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        let entries = PracticeLog.entries.suffix(10).reversed()
        ZStack {
            Theme.bg.ignoresSafeArea()
            VStack(spacing: 18) {
                HStack {
                    Text("Your practice")
                        .font(.system(size: 20, weight: .semibold, design: .rounded))
                        .foregroundStyle(Theme.text)
                    Spacer()
                    Button("Done") { dismiss() }.tint(Theme.accent)
                }
                HStack(spacing: 12) {
                    stat("\(PracticeLog.totalSessions)", "sits")
                    stat("\(PracticeLog.totalMinutes)", "minutes")
                    stat("\(PracticeLog.streak)", "day streak")
                }
                if let mood = PracticeLog.averageMood {
                    let emoji = ["😣", "😕", "😐", "🙂", "😌"][max(0, min(4, Int(mood.rounded()) - 1))]
                    Text("Usual mood after sitting   \(emoji)   \(String(format: "%.1f", mood)) / 5")
                        .font(.system(size: 12)).foregroundStyle(Theme.muted)
                }
                if let badge = PracticeLog.badge {
                    Text(badge).font(.system(size: 14, weight: .medium))
                        .foregroundStyle(Theme.accentWarm)
                }
                if !entries.isEmpty {
                    VStack(spacing: 6) {
                        HStack {
                            Text("This month").font(.system(size: 12)).foregroundStyle(Theme.muted)
                            Spacer()
                            Text("\(PracticeLog.thisMonthMinutes) min")
                                .font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.text)
                        }
                        if let t = PracticeLog.bestTimeOfDay {
                            HStack {
                                Text("You practise most in the \(t).")
                                    .font(.system(size: 12)).foregroundStyle(Theme.muted)
                                Spacer()
                            }
                        }
                    }
                    heatmap
                }
                if entries.isEmpty {
                    Text("Complete a session to start your history.")
                        .font(.system(size: 13)).foregroundStyle(Theme.faint)
                        .padding(.top, 20)
                } else {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Recent").font(.system(size: 12, weight: .medium))
                            .foregroundStyle(Theme.muted)
                        ForEach(Array(entries.enumerated()), id: \.offset) { _, e in
                            HStack {
                                Text(e.day).font(.system(size: 13)).foregroundStyle(Theme.text)
                                Spacer()
                                Text("\(Int(e.minutes.rounded())) min")
                                    .font(.system(size: 13)).foregroundStyle(Theme.muted)
                            }
                        }
                    }
                    .padding(14)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Theme.bgCard)
                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(Theme.border, lineWidth: 1))
                    .clipShape(RoundedRectangle(cornerRadius: 14))
                }
                Spacer()
            }
            .padding(20)
        }
        .preferredColorScheme(.dark)
    }

    private func stat(_ value: String, _ label: String) -> some View {
        VStack(spacing: 4) {
            Text(value).font(.system(size: 26, weight: .light, design: .rounded))
                .foregroundStyle(Theme.accent)
            Text(label).font(.system(size: 11)).foregroundStyle(Theme.muted)
        }
        .frame(maxWidth: .infinity).padding(.vertical, 16)
        .background(Theme.bgCard)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Theme.border, lineWidth: 1))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    /// A 5-week (7×5) practice heatmap; brighter cells = more minutes that day.
    private var heatmap: some View {
        let cells = Array(PracticeLog.dailyMinutes(lastDays: 35).reversed())   // oldest → today
        return VStack(alignment: .leading, spacing: 5) {
            Text("Last 5 weeks").font(.system(size: 12, weight: .medium)).foregroundStyle(Theme.muted)
            VStack(spacing: 4) {
                ForEach(0..<5, id: \.self) { row in
                    HStack(spacing: 4) {
                        ForEach(0..<7, id: \.self) { col in
                            let idx = row * 7 + col
                            let v = idx < cells.count ? cells[idx] : 0
                            RoundedRectangle(cornerRadius: 3)
                                .fill(v <= 0 ? Theme.bg
                                             : Theme.accent.opacity(min(1.0, 0.3 + v / 30.0)))
                                .frame(height: 16)
                                .overlay(RoundedRectangle(cornerRadius: 3)
                                    .stroke(Theme.border, lineWidth: v <= 0 ? 1 : 0))
                        }
                    }
                }
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.bgCard)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Theme.border, lineWidth: 1))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}
