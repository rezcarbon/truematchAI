//
//  SessionManager.swift
//  TrueMatch
//

import Foundation
import Security

final class SessionManager {
    static let shared = SessionManager()

    private let keychainService = "ai.truematch.app"
    private let accessTokenKey = "access_token"
    private let refreshTokenKey = "refresh_token"
    private let userIdKey = "user_id"
    private let expiryKey = "token_expiry"
    private let displayNameKey = "user_display_name"
    private let maskedNricKey = "user_masked_nric"

    private init() {}

    // MARK: - Public API

    var accessToken: String? {
        readKeychain(key: accessTokenKey)
    }

    var refreshToken: String? {
        readKeychain(key: refreshTokenKey)
    }

    var userId: String? {
        UserDefaults.standard.string(forKey: userIdKey)
    }

    var displayName: String? {
        get { UserDefaults.standard.string(forKey: displayNameKey) }
        set { UserDefaults.standard.set(newValue, forKey: displayNameKey) }
    }

    var maskedNric: String? {
        get { UserDefaults.standard.string(forKey: maskedNricKey) }
        set { UserDefaults.standard.set(newValue, forKey: maskedNricKey) }
    }

    var hasValidSession: Bool {
        guard accessToken != nil else { return false }
        guard let expiry = UserDefaults.standard.object(forKey: expiryKey) as? Date else {
            return false
        }
        return expiry > Date()
    }

    var isTokenExpired: Bool {
        guard let expiry = UserDefaults.standard.object(forKey: expiryKey) as? Date else {
            return true
        }
        return expiry <= Date()
    }

    /// Returns the current access token, refreshing it first if expired.
    func validAccessToken() async throws -> String {
        if isTokenExpired {
            try await refreshAccessToken()
        }
        guard let token = accessToken else {
            throw AuthError.sessionExpired
        }
        return token
    }

    func saveSession(accessToken: String, refreshToken: String, userId: String, expiresIn: Int) {
        saveKeychain(key: accessTokenKey, value: accessToken)
        saveKeychain(key: refreshTokenKey, value: refreshToken)
        UserDefaults.standard.set(userId, forKey: userIdKey)
        UserDefaults.standard.set(
            Date().addingTimeInterval(TimeInterval(expiresIn)),
            forKey: expiryKey
        )
    }

    func clearSession() {
        deleteKeychain(key: accessTokenKey)
        deleteKeychain(key: refreshTokenKey)
        UserDefaults.standard.removeObject(forKey: userIdKey)
        UserDefaults.standard.removeObject(forKey: expiryKey)
        UserDefaults.standard.removeObject(forKey: displayNameKey)
        UserDefaults.standard.removeObject(forKey: maskedNricKey)
    }

    func refreshAccessToken() async throws {
        guard refreshToken != nil else {
            throw AuthError.sessionExpired
        }

        let response = try await APIClient.shared.request(
            endpoint: .refreshToken,
            type: AuthTokenResponse.self
        )

        saveSession(
            accessToken: response.accessToken,
            refreshToken: response.refreshToken,
            userId: response.userId,
            expiresIn: response.expiresIn
        )
    }

    // MARK: - Keychain Helpers

    private func saveKeychain(key: String, value: String) {
        guard let data = value.data(using: .utf8) else { return }
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
        var newQuery = query
        newQuery[kSecValueData as String] = data
        SecItemAdd(newQuery as CFDictionary, nil)
    }

    private func readKeychain(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private func deleteKeychain(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
