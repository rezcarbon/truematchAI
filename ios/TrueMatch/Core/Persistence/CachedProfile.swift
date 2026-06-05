//
//  CachedProfile.swift
//  TrueMatch
//

import Foundation
import SwiftData

/// Local cache of the signed-in user's profile, for fast offline rendering.
@Model
final class CachedProfile {
    @Attribute(.unique) var userId: String
    var displayName: String
    var email: String?
    var maskedNric: String?
    var lastSynced: Date

    init(
        userId: String,
        displayName: String,
        email: String? = nil,
        maskedNric: String? = nil,
        lastSynced: Date = .now
    ) {
        self.userId = userId
        self.displayName = displayName
        self.email = email
        self.maskedNric = maskedNric
        self.lastSynced = lastSynced
    }
}
