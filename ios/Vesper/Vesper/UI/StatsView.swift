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
}
