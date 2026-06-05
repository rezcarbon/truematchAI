//
//  AuthState.swift
//  TrueMatch
//

import Foundation
import Combine
import UIKit

@MainActor
final class AuthStateManager: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var currentUserId: String?
    @Published var isLoading: Bool = false
    @Published var error: String?

    private let singpassManager = SingpassAuthManager.shared
    private var cancellables = Set<AnyCancellable>()
    private var tokenRefreshTimer: Timer?

    init() {
        checkInitialAuthState()
        observeAppLifecycle()
    }

    // MARK: - Initial State

    private func checkInitialAuthState() {
        isAuthenticated = SessionManager.shared.hasValidSession
        currentUserId = SessionManager.shared.userId
    }

    // MARK: - Email / Password

    func login(email: String, password: String) async {
        isLoading = true
        error = nil
        do {
            let response = try await APIClient.shared.request(
                endpoint: .login(LoginRequest(email: email, password: password)),
                type: AuthTokenResponse.self
            )
            persist(response)
        } catch {
            self.error = AuthError.invalidCredentials.errorDescription
            TrueMatchLogger.log(.warning, "Login failed: \(error.localizedDescription)")
        }
        isLoading = false
    }

    func signUp(email: String, password: String, displayName: String?) async {
        isLoading = true
        error = nil
        do {
            let response = try await APIClient.shared.request(
                endpoint: .signup(SignUpRequest(email: email, password: password, displayName: displayName)),
                type: AuthTokenResponse.self
            )
            persist(response)
        } catch {
            self.error = error.localizedDescription
            TrueMatchLogger.log(.warning, "Sign up failed: \(error.localizedDescription)")
        }
        isLoading = false
    }

    private func persist(_ response: AuthTokenResponse) {
        SessionManager.shared.saveSession(
            accessToken: response.accessToken,
            refreshToken: response.refreshToken,
            userId: response.userId,
            expiresIn: response.expiresIn
        )
        isAuthenticated = true
        currentUserId = response.userId
        scheduleTokenRefresh()
    }

    // MARK: - App Lifecycle

    private func observeAppLifecycle() {
        NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)
            .sink { [weak self] _ in
                Task { @MainActor in
                    await self?.handleAppForeground()
                }
            }
            .store(in: &cancellables)
    }

    private func handleAppForeground() async {
        guard isAuthenticated else { return }
        if SessionManager.shared.isTokenExpired {
            await attemptTokenRefresh()
        }
    }

    // MARK: - Deep Link Callback

    func handleAuthCallback(url: URL) async {
        isLoading = true
        do {
            try await singpassManager.handleCallback(url: url)
            isAuthenticated = true
            currentUserId = SessionManager.shared.userId
            scheduleTokenRefresh()
        } catch {
            isAuthenticated = false
            currentUserId = nil
            TrueMatchLogger.log(.error, "Auth callback failed: \(error.localizedDescription)")
        }
        isLoading = false
    }

    // MARK: - Token Refresh

    func attemptTokenRefresh() async {
        guard SessionManager.shared.isTokenExpired else { return }
        isLoading = true
        do {
            try await SessionManager.shared.refreshAccessToken()
            isAuthenticated = true
        } catch {
            isAuthenticated = false
            currentUserId = nil
            TrueMatchLogger.log(.warning, "Token refresh failed: \(error.localizedDescription)")
        }
        isLoading = false
    }

    func scheduleTokenRefresh() {
        tokenRefreshTimer?.invalidate()
        // Refresh 5 minutes before expiry
        tokenRefreshTimer = Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { [weak self] _ in
            Task { @MainActor in
                await self?.attemptTokenRefresh()
            }
        }
    }

    // MARK: - Logout

    func logout() async {
        tokenRefreshTimer?.invalidate()
        tokenRefreshTimer = nil
        try? await APIClient.shared.requestVoid(endpoint: .deleteSession)
        singpassManager.signOut()
        isAuthenticated = false
        currentUserId = nil
    }
}
