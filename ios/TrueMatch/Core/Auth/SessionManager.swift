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

    // In-memory cache layered over the keychain. The keychain remains the
    // at-rest store (persists across launches on signed builds), but reads
    // prefer this process-lifetime cache so the session keeps working even when
    // a keychain write is unavailable — e.g. unsigned simulator builds without a
    // keychain-access-group entitlement, where SecItemAdd can silently fail.
    private var cachedAccessToken: String?
    private var cachedRefreshToken: String?

    // MARK: - Public API

    var accessToken: String? {
        cachedAccessToken ?? readKeychain(key: accessTokenKey)
    }

    var refreshToken: String? {
        cachedRefreshToken ?? readKeychain(key: refreshTokenKey)
    }

    var userId: String? {
        UserDefaults.standard.string(forKey: userIdKey)
    }

    /// The user's role ("candidate" | "recruiter" | "admin"), read from the
    /// `role` claim of the access-token JWT. Drives role-aware navigation.
    /// Not a trust boundary — the server authorizes every request.
    var role: String? {
        guard let token = accessToken else { return nil }
        let parts = token.split(separator: ".")
        guard parts.count >= 2,
              let data = SessionManager._b64urlDecode(String(parts[1])),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else { return nil }
        return json["role"] as? String
    }

    private static func _b64urlDecode(_ s: String) -> Data? {
        var b = s.replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")
        let pad = b.count % 4
        if pad > 0 { b += String(repeating: "=", count: 4 - pad) }
        return Data(base64Encoded: b)
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
        cachedAccessToken = accessToken
        cachedRefreshToken = refreshToken
        saveKeychain(key: accessTokenKey, value: accessToken)
        saveKeychain(key: refreshTokenKey, value: refreshToken)
        UserDefaults.standard.set(userId, forKey: userIdKey)
        UserDefaults.standard.set(
            Date().addingTimeInterval(TimeInterval(expiresIn)),
            forKey: expiryKey
        )
    }

    func clearSession() {
        cachedAccessToken = nil
        cachedRefreshToken = nil
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
