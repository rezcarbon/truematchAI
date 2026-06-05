//
//  ResumeCache.swift
//  TrueMatch
//

import Foundation
import SwiftData

/// Local record of an uploaded resume / supplementary submission. Lets the user
/// review and reuse previously submitted material without re-uploading.
@Model
final class ResumeCache {
    @Attribute(.unique) var id: String
    /// Backend file ID returned by POST /files/upload (nil while pending upload).
    var fileId: String?
    var fileName: String
    var mimeType: String
    /// Extracted or pasted plain text of the resume (optional).
    var extractedText: String?
    /// Free-text supplementary information supplied alongside the resume.
    var supplementary: String?
    var createdAt: Date
    var syncStatus: String // pending, synced, failed

    init(
        id: String = UUID().uuidString,
        fileId: String? = nil,
        fileName: String,
        mimeType: String,
        extractedText: String? = nil,
        supplementary: String? = nil,
        createdAt: Date = .now,
        syncStatus: String = "pending"
    ) {
        self.id = id
        self.fileId = fileId
        self.fileName = fileName
        self.mimeType = mimeType
        self.extractedText = extractedText
        self.supplementary = supplementary
        self.createdAt = createdAt
        self.syncStatus = syncStatus
    }
}
