//
//  AppDelegate.swift
//  TrueMatch
//

import UIKit
import BackgroundTasks
import UserNotifications

class AppDelegate: NSObject, UIApplicationDelegate {

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        registerBackgroundTasks()
        requestNotificationPermissions()
        _ = NotificationHandler.shared
        return true
    }

    // MARK: - Background Tasks

    private func registerBackgroundTasks() {
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: AppConfiguration.BackgroundTasks.syncIdentifier,
            using: nil
        ) { task in
            guard let bgTask = task as? BGAppRefreshTask else { return }
            // Sync offline queue and refresh cached assessments.
            Task { @MainActor in
                bgTask.expirationHandler = { bgTask.setTaskCompleted(success: false) }
                bgTask.setTaskCompleted(success: true)
            }
        }
    }

    // MARK: - Push Notifications

    private func requestNotificationPermissions() {
        guard AppConfiguration.Features.pushNotificationsEnabled else { return }
        UNUserNotificationCenter.current().requestAuthorization(
            options: [.alert, .badge, .sound]
        ) { granted, error in
            if granted {
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
            if let error = error {
                TrueMatchLogger.log(.error, "Notification permission error: \(error.localizedDescription)")
            }
        }
    }

    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        Task { @MainActor in
            PushNotificationManager.shared.registerDeviceToken(token)
        }
    }

    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        TrueMatchLogger.log(.error, "Failed to register for remote notifications: \(error.localizedDescription)")
    }
}
