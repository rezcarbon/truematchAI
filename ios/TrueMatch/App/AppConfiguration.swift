//
//  AppConfiguration.swift
//  TrueMatch
//

import Foundation

enum AppConfiguration {

    // MARK: - API

    enum API {
        static let baseURL: URL = {
            #if DEBUG
            return URL(string: "http://127.0.0.1:8000/api/v1")!
            #else
            return URL(string: "https://api.truematch.ai/api/v1")!
            #endif
        }()

        /// Base URL for WebSocket connections (ws:// in debug, wss:// in production).
        static let wsBase: URL? = {
            #if DEBUG
            return URL(string: "ws://127.0.0.1:8000/api/v1")
            #else
            return URL(string: "wss://api.truematch.ai/api/v1")
            #endif
        }()

        static let webSocketURL: URL = {
            #if DEBUG
            return URL(string: "ws://127.0.0.1:8000/api/v1")!
            #else
            return URL(string: "wss://api.truematch.ai/api/v1")!
            #endif
        }()

        static let apiVersion = "v1"
        static let timeout: TimeInterval = 30
    }

    // MARK: - Feature Flags

    enum Features {
        static let singpassEnabled = true
        static let offlineModeEnabled = true
        static let pushNotificationsEnabled = true
        static let jobMatchingEnabled = true
    }

    // MARK: - Background Tasks

    enum BackgroundTasks {
        static let syncIdentifier = "ai.truematch.app.sync"
        static let maintenanceIdentifier = "ai.truematch.app.maintenance"
        static let minimumSyncInterval: TimeInterval = 15 * 60 // 15 minutes
    }

    // MARK: - Deep Links

    enum DeepLinks {
        static let scheme = "truematch"
        static let host = "app"
    }

    // MARK: - Singpass OAuth

    enum Singpass {
        static let authorizeURL: URL = {
            #if DEBUG
            return URL(string: "https://stg-id.singpass.gov.sg/auth")!
            #else
            return URL(string: "https://id.singpass.gov.sg/auth")!
            #endif
        }()

        static let clientId = "TrueMatch_CLIENT" // Configured server-side
        static let redirectURI = "truematch://auth/callback"
        static let scope = "openid"
        static let callbackScheme = "truematch"
    }

    // MARK: - Storage

    enum Storage {
        static let maxCachedAssessments = 1000
        static let maxOfflineQueueSize = 50
        static let cacheExpiryDays = 90
    }

    // MARK: - Timeouts

    enum Timeouts {
        static let apiRequest: TimeInterval = 30
        static let webSocket: TimeInterval = 60
        static let authSession: TimeInterval = 120
        static let backgroundSync: TimeInterval = 25
    }
}
