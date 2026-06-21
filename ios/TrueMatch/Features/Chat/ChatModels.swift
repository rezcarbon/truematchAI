//
//  ChatModels.swift
//  TrueMatch
//
//  DTOs for the conversational AI chat. Mirrors the backend `/chat` contract.
//  The APIClient decoder uses `.convertFromSnakeCase`, so snake_case fields on
//  the wire map to camelCase here (e.g. `message_count` → `messageCount`).
//  Timestamps are kept as `String` to avoid brittleness across the backend's
//  ISO-8601 fractional/offset variations.
//

import Foundation

// MARK: - Requests

struct CreateChatSessionRequest: Codable {
    let title: String
}

struct ChatSendRequest: Codable {
    let sessionId: String
    let message: String
}

// MARK: - Responses

struct ChatSessionResponse: Codable, Identifiable {
    let id: String
    let title: String
}

struct ChatSessionSummary: Codable, Identifiable {
    let id: String
    let title: String
    let messageCount: Int
    let lastMessageAt: String?
}

struct ChatActionDTO: Codable, Identifiable {
    let id: String
    let description: String
    let status: String
    let result: String?
}

struct ChatMessageDTO: Codable, Identifiable {
    let id: String
    let role: String
    let content: String
    let timestamp: String
    let actionsTaken: [ChatActionDTO]?
}

struct ChatSessionDetailResponse: Codable {
    let id: String
    let title: String
    let messages: [ChatMessageDTO]
}

struct ChatSendResponse: Codable {
    let response: String
    let actions: [ChatActionDTO]
    let suggestions: [String]
}

// MARK: - View model item

/// A single rendered chat bubble (user or assistant).
struct ChatBubble: Identifiable {
    enum Role { case user, assistant }
    let id: String
    let role: Role
    let content: String
    let actions: [ChatActionDTO]

    init(id: String = UUID().uuidString, role: Role, content: String, actions: [ChatActionDTO] = []) {
        self.id = id
        self.role = role
        self.content = content
        self.actions = actions
    }
}
