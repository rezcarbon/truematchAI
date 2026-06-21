//
//  CapabilityTranslationModels.swift
//  TrueMatch
//
//  DTOs for the candidate-facing Capability Translation feature: re-express
//  evidenced capability into ATS-legible, JD-targeted language and report the
//  measured before→after keyword + semantic lift. The backend already returns
//  camelCase keys; APIClient's keyDecodingStrategy passes them through.
//

import Foundation

struct CapabilityTranslationStartRequest: Codable {
    let resumeId: String
    let jdText: String
    let targetRole: String?
}

struct CapabilityTranslationStartResponse: Codable {
    let translationId: String
    let status: String
}

struct TranslationBulletDTO: Codable, Identifiable {
    var id: String { text }
    let text: String
    let grounding: String
    let evidenceStrength: String   // HIGH | MEDIUM | WEAK
}

struct CapabilityTranslationResultDTO: Codable {
    let translationId: String
    let status: String             // pending | translating | completed | failed
    let targetRole: String?
    let summary: String?
    let bullets: [TranslationBulletDTO]?
    let skills: [String]?
    let translationNotes: String?
    let droppedUngrounded: Int?
    let beforeKeywordScore: Int?
    let afterKeywordScore: Int?
    let beforeSemanticScore: Int?
    let afterSemanticScore: Int?
    let keywordLift: Int?
    let semanticLift: Int?
    let capabilityScore: Int?
    let capabilityDelta: Int?
    let matchedKeywordsAfter: [String]?
    let stillMissingKeywords: [String]?
    let error: String?
}
