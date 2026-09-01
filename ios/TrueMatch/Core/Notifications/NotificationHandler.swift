//
//  NotificationHandler.swift
//  TrueMatch
//

import Foundation
import UserNotifications

// MARK: - Push Notification Payload

struct PushNotificationPayload {
    let type: NotificationType
    let title: String
    let body: String
    let assessmentId: String?
    let decisionId: String?
    let deepLink: String?

    enum NotificationType: String {
        case assessmentReady = "assessment_ready"
        case decisionUpdate = "decision_update"
        // Autonomous agent events
        case cvIngested = "cv_ingested"
        case cvAwaitingReview = "cv_awaiting_review"
        case jdDraftReady = "jd_draft_ready"
        case jdDraftAnalysed = "jd_draft_analysed"
        case agentError = "agent_error"
        case unknown
    }

    init(userInfo: [AnyHashable: Any]) {
        self.type = NotificationType(rawValue: userInfo["type"] as? String ?? "") ?? .unknown
        self.title = userInfo["title"] as? String ?? ""
        self.body = userInfo["body"] as? String ?? ""
        self.assessmentId = userInfo["assessmentId"] as? String
        self.decisionId = userInfo["decisionId"] as? String
        self.deepLink = userInfo["deepLink"] as? String
    }
}

// MARK: - Notification Handler

final class NotificationHandler: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationHandler()

    private override init() {
        super.init()
        UNUserNotificationCenter.current().delegate = self
    }

    // MARK: - Foreground Presentation

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .badge, .sound])
    }

    // MARK: - Notification Tap / Action

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let content = response.notification.request.content
        let payload = PushNotificationPayload(userInfo: content.userInfo)
        handleAction(actionIdentifier: response.actionIdentifier, payload: payload)
        completionHandler()
    }

    // MARK: - Action Routing

    private func handleAction(actionIdentifier: String, payload: PushNotificationPayload) {
        Task { @MainActor in
            switch actionIdentifier {
            case UNNotificationDefaultActionIdentifier,
                 "open_action",
                 "view_results_action":
                routeToScreen(payload: payload)

            case "dismiss_action":
                PushNotificationManager.shared.clearBadge()

            default:
                TrueMatchLogger.log(.warning, "Unknown notification action: \(actionIdentifier)")
            }
        }
    }

    // MARK: - Screen Routing

    @MainActor
    private func routeToScreen(payload: PushNotificationPayload) {
        if let deepLink = payload.deepLink, let url = URL(string: deepLink) {
            DeepLinkHandler.shared.handle(url: url)
            return
        }

        switch payload.type {
        case .assessmentReady:
            if let assessmentId = payload.assessmentId {
                DeepLinkHandler.shared.handle(
                    url: URL(string: "truematch://assessment/\(assessmentId)")!
                )
            }
        case .decisionUpdate:
            if let assessmentId = payload.assessmentId {
                DeepLinkHandler.shared.handle(
                    url: URL(string: "truematch://assessment/\(assessmentId)")!
                )
            }
        // Agent autonomous events — route to the agent dashboard / queue.
        case .cvIngested, .cvAwaitingReview:
            DeepLinkHandler.shared.handle(url: URL(string: "truematch://agents/queue")!)
        case .jdDraftReady, .jdDraftAnalysed:
            DeepLinkHandler.shared.handle(url: URL(string: "truematch://agents/jd-review")!)
        case .agentError:
            DeepLinkHandler.shared.handle(url: URL(string: "truematch://agents/queue")!)
        case .unknown:
            break
        }
    }
}
