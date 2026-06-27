//  NowPlaying.swift
//  Vesper — lock-screen / Control-Center "Now Playing" info + remote commands.
//
//  With background audio, the user controls the session from the lock screen.
//  This sets the Now Playing metadata and routes the play/pause buttons back to
//  the session. Pure UIKit-free MediaPlayer; safe no-op if unavailable.

import Foundation
@preconcurrency import MediaPlayer

final class NowPlaying {
    private let center = MPNowPlayingInfoCenter.default()
    private let commands = MPRemoteCommandCenter.shared()
    private var configured = false

    /// Wire the lock-screen play/pause buttons to `toggle` (called once).
    func configure(toggle: @escaping () -> Void) {
        guard !configured else { return }
        configured = true
        let fire: (MPRemoteCommandEvent) -> MPRemoteCommandHandlerStatus = { _ in
            DispatchQueue.main.async { toggle() }
            return .success
        }
        commands.playCommand.addTarget(handler: fire)
        commands.pauseCommand.addTarget(handler: fire)
        commands.togglePlayPauseCommand.addTarget(handler: fire)
        commands.playCommand.isEnabled = true
        commands.pauseCommand.isEnabled = true
        commands.togglePlayPauseCommand.isEnabled = true
    }

    func update(title: String, subtitle: String, playing: Bool) {
        center.nowPlayingInfo = [
            MPMediaItemPropertyTitle: title,
            MPMediaItemPropertyArtist: subtitle,
            MPNowPlayingInfoPropertyPlaybackRate: playing ? 1.0 : 0.0,
        ]
    }

    func clear() { center.nowPlayingInfo = nil }
}
