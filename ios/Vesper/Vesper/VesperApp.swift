//  VesperApp.swift
//  Vesper — native iOS app entry point.
//
//  A breath-paced meditation & sleep companion: procedural breath sound, a
//  breathing orb, and spoken sleep-lectures that keep playing with the screen
//  locked. The companion native build to the desktop (PySide6) Vesper.

import SwiftUI

@main
struct VesperApp: App {
    var body: some Scene {
        WindowGroup {
            RootView()
        }
    }
}
