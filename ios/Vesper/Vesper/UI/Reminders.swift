//  Reminders.swift
//  Vesper — a gentle daily practice reminder via a local notification. No
//  account, no server; the user can revoke notification permission anytime in
//  iOS Settings. Permission is only requested when the reminder is turned on.

import Foundation
import UserNotifications

enum Reminders {
    private static let id = "vesper.daily"
    private static let windDownID = "vesper.winddown"

    /// Request permission (first time) and schedule a repeating daily reminder.
    static func enable(hour: Int, minute: Int) {
        let center = UNUserNotificationCenter.current()
        center.requestAuthorization(options: [.alert, .sound]) { granted, _ in
            guard granted else { return }
            let content = UNMutableNotificationContent()
            content.title = "A moment to breathe"
            content.body = "Take a few quiet minutes with Vesper."
            content.sound = .default

            var when = DateComponents()
            when.hour = hour
            when.minute = minute
            let trigger = UNCalendarNotificationTrigger(dateMatching: when, repeats: true)
            let request = UNNotificationRequest(identifier: id, content: content, trigger: trigger)

            center.removePendingNotificationRequests(withIdentifiers: [id])
            center.add(request)
        }
    }

    static func disable() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [id])
    }

    /// A nightly "time to wind down" nudge — a consistent pre-sleep buffer is a
    /// core CBT-I behaviour. Scheduled ~30 min before the prescribed bedtime.
    static func enableWindDown(hour: Int, minute: Int) {
        let center = UNUserNotificationCenter.current()
        center.requestAuthorization(options: [.alert, .sound]) { granted, _ in
            guard granted else { return }
            let content = UNMutableNotificationContent()
            content.title = "Time to wind down"
            content.body = "Dim the lights and let the day settle — bed will feel easier soon."
            content.sound = .default

            var when = DateComponents()
            when.hour = hour
            when.minute = minute
            let trigger = UNCalendarNotificationTrigger(dateMatching: when, repeats: true)
            let request = UNNotificationRequest(identifier: windDownID, content: content, trigger: trigger)

            center.removePendingNotificationRequests(withIdentifiers: [windDownID])
            center.add(request)
        }
    }

    static func disableWindDown() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [windDownID])
    }
}
