//
//  AppState.swift
//  TrueMatch
//

import SwiftUI
import Combine

// MARK: - Auth State

enum AuthenticationState: Equatable {
    case unauthenticated
    case onboarding
    case authenticated
}

// MARK: - App State

@MainActor
final class AppState: ObservableObject {
    private static let currentAssessmentIdKey = "current_assessment_id"

    @Published var authState: AuthenticationState = .unauthenticated
    @Published var currentAssessmentId: String? {
        didSet {
            // Persist so the assessment ID survives relaunch and is available to
            // non-SwiftUI consumers (e.g. PushNotificationManager).
            if let id = currentAssessmentId {
                UserDefaults.standard.set(id, forKey: Self.currentAssessmentIdKey)
            } else {
                UserDefaults.standard.removeObject(forKey: Self.currentAssessmentIdKey)
            }
        }
    }
    @Published var isOnline: Bool = true
    @Published var pendingOfflineActions: Int = 0

    private let networkMonitor = NetworkMonitor()
    private var cancellables = Set<AnyCancellable>()

    init() {
        setupNetworkMonitoring()
        restoreSession()
    }

    private func setupNetworkMonitoring() {
        networkMonitor.$isConnected
            .receive(on: DispatchQueue.main)
            .assign(to: &$isOnline)
    }

    private func restoreSession() {
        if SessionManager.shared.hasValidSession {
            authState = .authenticated
            currentAssessmentId = UserDefaults.standard.string(forKey: Self.currentAssessmentIdKey)
        }
    }

    /// Called after a successful sign-in of a returning user.
    func completeAuthentication() {
        authState = .authenticated
        currentAssessmentId = UserDefaults.standard.string(forKey: Self.currentAssessmentIdKey)
    }

    func signOut() {
        SessionManager.shared.clearSession()
        authState = .unauthenticated
        currentAssessmentId = nil
    }
}
