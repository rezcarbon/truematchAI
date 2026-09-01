//
//  DeepLinkHandler.swift
//  TrueMatch
//

import Foundation
import SwiftUI

@MainActor
final class DeepLinkHandler: ObservableObject {
    static let shared = DeepLinkHandler()

    @Published var pendingDeepLink: DeepLink?

    private init() {}

    enum DeepLink: Equatable {
        case assessment(id: String)
        case position(id: String)
        case authCallback(code: String, state: String)
        // Agent deep links
        case agentQueue
        case agentJDReview
    }

    func handle(url: URL) {
        guard url.scheme == AppConfiguration.DeepLinks.scheme else { return }

        let pathComponents = url.pathComponents.filter { $0 != "/" }

        switch url.host {
        case "auth":
            handleAuthCallback(url: url)
        case "assessment":
            if let assessmentId = pathComponents.first {
                pendingDeepLink = .assessment(id: assessmentId)
            }
        case "position":
            if let positionId = pathComponents.first {
                pendingDeepLink = .position(id: positionId)
            }
        case "agents":
            switch pathComponents.first {
            case "queue": pendingDeepLink = .agentQueue
            case "jd-review": pendingDeepLink = .agentJDReview
            default: pendingDeepLink = .agentQueue
            }
        default:
            TrueMatchLogger.log(.warning, "Unknown deep link: \(url)")
        }
    }

    private func handleAuthCallback(url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let code = components.queryItems?.first(where: { $0.name == "code" })?.value,
              let state = components.queryItems?.first(where: { $0.name == "state" })?.value else {
            TrueMatchLogger.log(.error, "Invalid auth callback URL")
            return
        }

        pendingDeepLink = .authCallback(code: code, state: state)

        Task {
            try? await SingpassAuthManager.shared.handleCallback(code: code, state: state)
        }
    }

    func clearPendingDeepLink() {
        pendingDeepLink = nil
    }
}
