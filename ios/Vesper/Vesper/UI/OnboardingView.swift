//  OnboardingView.swift
//  Vesper — a short, calming first-run welcome (skippable). Re-openable from
//  Settings ▸ Show welcome screen.

import SwiftUI

struct OnboardingView: View {
    @ObservedObject var vm: SessionViewModel
    @State private var page = 0

    private let pages: [(symbol: String, title: String, body: String)] = [
        ("moon.stars.fill", "Welcome to Vesper",
         "Breathe, rest, and drift off — with sound and breath created live, just for this moment. Nothing to download, nothing online."),
        ("circle.hexagonpath", "Four ways to unwind",
         "Meditate, Breathwork, Relax, and Sleep. Tap a mode to begin; the breath, sound, and visuals adapt around it."),
        ("waveform", "Bedtime, narrated",
         "In Sleep, a calm neural voice tells gentle stories that slow and soften as you fall asleep — and keep playing with the screen locked."),
    ]

    var body: some View {
        ZStack {
            Theme.bg.ignoresSafeArea()
            VStack(spacing: 0) {
                TabView(selection: $page) {
                    ForEach(pages.indices, id: \.self) { i in
                        VStack(spacing: 20) {
                            Image(systemName: pages[i].symbol)
                                .font(.system(size: 54)).foregroundStyle(Theme.accent)
                                .padding(.bottom, 6)
                            Text(pages[i].title)
                                .font(.system(size: 25, weight: .semibold, design: .rounded))
                                .foregroundStyle(Theme.text)
                            Text(pages[i].body)
                                .font(.system(size: 15)).foregroundStyle(Theme.muted)
                                .multilineTextAlignment(.center)
                                .fixedSize(horizontal: false, vertical: true)
                                .padding(.horizontal, 34)
                        }
                        .tag(i)
                    }
                }
                .tabViewStyle(.page(indexDisplayMode: .always))

                Button(page < pages.count - 1 ? "Next" : "Begin") {
                    if page < pages.count - 1 { withAnimation { page += 1 } }
                    else { vm.finishOnboarding() }
                }
                .font(.system(size: 16, weight: .semibold)).foregroundStyle(Theme.bg)
                .frame(maxWidth: .infinity).padding(.vertical, 14)
                .background(Theme.accent).clipShape(Capsule())
                .padding(.horizontal, 40)

                Button("Skip") { vm.finishOnboarding() }
                    .font(.system(size: 13)).foregroundStyle(Theme.muted)
                    .padding(.vertical, 14)
            }
            .padding(.vertical, 30)
        }
        .preferredColorScheme(.dark)
        .interactiveDismissDisabled()
    }
}
