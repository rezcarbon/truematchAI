//
//  SingpassAuthManager.swift
//  TrueMatch
//

import Foundation
import AuthenticationServices

@MainActor
final class SingpassAuthManager: NSObject, ObservableObject {
    static let shared = SingpassAuthManager()

    @Published var isAuthenticating: Bool = false
    @Published var error: String?
    /// Flips to true when a sign-in completes successfully. Observers
    /// use this to transition the app to the authenticated state.
    @Published var didCompleteAuthentication: Bool = false

    private var authSession: ASWebAuthenticationSession?
    private var pendingState: String?

    private override init() {
        super.init()
    }

    // MARK: - Start Auth

    /// Entry point. Asks the backend to begin the OIDC transaction (it owns
    /// PKCE, state, and nonce), then opens the returned authorization URL.
    func startAuthentication() {
        guard !isAuthenticating else { return }
        isAuthenticating = true
        error = nil

        Task { @MainActor in
            do {
                let initResponse = try await APIClient.shared.request(
                    endpoint: .singpassInit,
                    type: SingpassInitResponse.self
                )
                self.pendingState = initResponse.state
                guard let authURL = URL(string: initResponse.authURL) else {
                    self.error = "Server returned an invalid authorization URL"
                    self.isAuthenticating = false
                    return
                }
                self.presentAuthSession(authURL: authURL)
            } catch {
                self.error = error.localizedDescription
                TrueMatchLogger.log(.error, "Singpass init error: \(error.localizedDescription)")
                self.isAuthenticating = false
            }
        }
    }

    private func presentAuthSession(authURL: URL) {
        let session = ASWebAuthenticationSession(
            url: authURL,
            callbackURLScheme: AppConfiguration.Singpass.callbackScheme
        ) { [weak self] callbackURL, authError in
            Task { @MainActor in
                guard let self else { return }

                if let authError {
                    if (authError as NSError).code == ASWebAuthenticationSessionError.canceledLogin.rawValue {
                        self.error = nil // User cancelled — not an error
                    } else {
                        self.error = authError.localizedDescription
                        TrueMatchLogger.log(.error, "Singpass auth error: \(authError.localizedDescription)")
                    }
                    self.isAuthenticating = false
                    return
                }

                guard let callbackURL else {
                    self.error = "No callback URL received"
                    self.isAuthenticating = false
                    return
                }

                do {
                    try await self.handleCallback(url: callbackURL)
                } catch {
                    self.error = error.localizedDescription
                    TrueMatchLogger.log(.error, "Singpass callback error: \(error.localizedDescription)")
                }
                self.isAuthenticating = false
            }
        }

        session.presentationContextProvider = self
        session.prefersEphemeralWebBrowserSession = false
        authSession = session

        if !session.start() {
            error = "Failed to start authentication session"
            isAuthenticating = false
        }
    }

    // MARK: - Handle Callback

    func handleCallback(url: URL) async throws {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let code = components.queryItems?.first(where: { $0.name == "code" })?.value,
              let state = components.queryItems?.first(where: { $0.name == "state" })?.value else {
            throw AuthError.tokenExchangeFailed
        }

        try await handleCallback(code: code, state: state)
    }

    func handleCallback(code: String, state: String) async throws {
        guard let savedState = pendingState, state == savedState else {
            throw AuthError.stateMismatch
        }

        let response = try await APIClient.shared.request(
            endpoint: .singpassCallback(code: code, state: state),
            type: AuthTokenResponse.self
        )

        SessionManager.shared.saveSession(
            accessToken: response.accessToken,
            refreshToken: response.refreshToken,
            userId: response.userId,
            expiresIn: response.expiresIn
        )

        pendingState = nil
        isAuthenticating = false
        didCompleteAuthentication = true
    }

    // MARK: - Sign Out

    func signOut() {
        authSession?.cancel()
        authSession = nil
        pendingState = nil
        isAuthenticating = false
        error = nil
        SessionManager.shared.clearSession()
    }
}

// MARK: - ASWebAuthenticationPresentationContextProviding

extension SingpassAuthManager: ASWebAuthenticationPresentationContextProviding {
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let window = windowScene.windows.first else {
            return ASPresentationAnchor()
        }
        return window
    }
}

// MARK: - Auth Error

enum AuthError: LocalizedError {
    case stateMismatch
    case tokenExchangeFailed
    case sessionExpired
    case userCancelled
    case invalidCredentials
    case networkError(String)
    case serverError(String)

    var errorDescription: String? {
        switch self {
        case .stateMismatch: return "Authentication state mismatch. Please try again."
        case .tokenExchangeFailed: return "Failed to exchange token. Please try again."
        case .sessionExpired: return "Your session has expired. Please sign in again."
        case .userCancelled: return "Authentication was cancelled."
        case .invalidCredentials: return "Incorrect email or password."
        case .networkError(let msg): return "Network error: \(msg)"
        case .serverError(let msg): return "Server error: \(msg)"
        }
    }
}
