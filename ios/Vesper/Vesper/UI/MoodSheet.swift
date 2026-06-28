//  MoodSheet.swift
//  Vesper — a gentle one-tap mood check after a session, logged to your practice
//  history so you can see how sitting changes how you feel.

import SwiftUI

struct MoodSheet: View {
    @ObservedObject var vm: SessionViewModel
    @Environment(\.dismiss) private var dismiss

    private let moods: [(Int, String, String)] = [
        (1, "😣", "Tense"), (2, "😕", "Restless"), (3, "😐", "Okay"),
        (4, "🙂", "Calm"), (5, "😌", "Serene"),
    ]

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            VStack(spacing: 20) {
                VStack(spacing: 4) {
                    Text("Well done.")
                        .font(.system(size: 20, weight: .semibold, design: .rounded))
                        .foregroundStyle(Theme.text)
                    Text("How do you feel?")
                        .font(.system(size: 13)).foregroundStyle(Theme.muted)
                }
                HStack(spacing: 8) {
                    ForEach(moods, id: \.0) { m in
                        Button {
                            vm.logMood(m.0); dismiss()
                        } label: {
                            VStack(spacing: 6) {
                                Text(m.1).font(.system(size: 28))
                                Text(m.2).font(.system(size: 9)).foregroundStyle(Theme.muted)
                            }
                            .frame(maxWidth: .infinity).padding(.vertical, 12)
                            .background(Theme.bgCard)
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Theme.border, lineWidth: 1))
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        .buttonStyle(.plain)
                    }
                }
                Button("Skip") { vm.dismissMood(); dismiss() }
                    .font(.system(size: 13)).foregroundStyle(Theme.muted)
            }
            .padding(22)
        }
        .preferredColorScheme(.dark)
        .presentationDetents([.height(250)])
        .presentationDragIndicator(.visible)
    }
}
