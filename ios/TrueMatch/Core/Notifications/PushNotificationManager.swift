//
//  PushNotificationManager.swift
//  TrueMatch
//

import Foundation
import UserNotifications
import UIKit

@MainActor
final class PushNotificationManager: ObservableObject {
    static let shared = PushNotificationManager()

    @Published var deviceToken: String?
    @Published var hasPermission: Bool = false

    // MARK: - Notification Categories

    nonisolated static let assessmentReadyCategory = "assessment_ready"
    nonisolated static let decisionUpdateCategory = "decision_update"

    private init() {
        checkPermission()
    }

    // MARK: - Permission

    func requestPermission() async -> Bool {
        do {
            let granted = try await UNUserNotificationCenter.current()
                .requestAuthorization(options: [.alert, .badge, .sound])
            hasPermission = granted
            if granted {
                UIApplication.shared.registerForRemoteNotifications()
                registerCategories()
            }
            return granted
        } catch {
            TrueMatchLogger.log(.error, "Notification permission request failed: \(error.localizedDescription)")
            return false
        }
    }

    func checkPermission() {
        UNUserNotificationCenter.current().getNotificationSettings { [weak self] settings in
            Task { @MainActor in
                self?.hasPermission = settings.authorizationStatus == .authorized
            }
        }
    }

    // MARK: - Device Token

    func registerDeviceToken(_ token: String) {
        deviceToken = token
        TrueMatchLogger.log(.info, "Device token registered: \(token.prefix(8))...")
        sendTokenToBackend(token: token)
    }

    private func sendTokenToBackend(token: String) {
        Task {
            do {
                try await APIClient.shared.requestVoid(
                    endpoint: .registerPushToken(token: token)
                )
                TrueMatchLogger.log(.info, "Push token sent to backend")
            } catch {
                TrueMatchLogger.log(.error, "Failed to register push token: \(error.localizedDescription)")
            }
        }
    }

    // MARK: - Notification Categories & Actions

    func registerCategories() {
        // Assessment Ready: "View Results"
        let viewResultsAction = UNNotificationAction(
            identifier: "view_results_action",
            title: "View Results",
            options: [.foreground]
        )
        let assessmentReadyCategory = UNNotificationCategory(
            identifier: Self.assessmentReadyCategory,
            actions: [viewResultsAction],
            intentIdentifiers: [],
            options: []
        )

        // Decision Update: "Open"
        let openAction = UNNotificationAction(
            identifier: "open_action",
            title: "Open",
            options: [.foreground]
        )
        let dismissAction = UNNotificationAction(
            identifier: "dismiss_action",
            title: "Dismiss",
            options: [.destructive]
        )
        let decisionCategory = UNNotificationCategory(
            identifier: Self.decisionUpdateCategory,
            actions: [openAction, dismissAction],
            intentIdentifiers: [],
            options: []
        )

        UNUserNotificationCenter.current().setNotificationCategories([
            assessmentReadyCategory,
            decisionCategory,
        ])
    }

    // MARK: - Badge Management

    func clearBadge() {
        UNUserNotificationCenter.current().setBadgeCount(0) { error in
            if let error {
                TrueMatchLogger.log(.error, "Failed to clear badge: \(error.localizedDescription)")
            }
        }
    }

    // MARK: - Local Notifications

    func scheduleLocalNotification(
        title: String,
        body: String,
        identifier: String,
        categoryIdentifier: String? = nil,
        userInfo: [String: Any] = [:],
        delay: TimeInterval = 0
    ) {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        content.userInfo = userInfo
        if let categoryIdentifier {
            content.categoryIdentifier = categoryIdentifier
        }

        let trigger: UNNotificationTrigger?
        if delay > 0 {
            trigger = UNTimeIntervalNotificationTrigger(timeInterval: delay, repeats: false)
        } else {
            trigger = nil
        }

        let request = UNNotificationRequest(
            identifier: identifier,
            content: content,
            trigger: trigger
        )

        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                TrueMatchLogger.log(.error, "Failed to schedule notification: \(error)")
            }
        }
    }
}
