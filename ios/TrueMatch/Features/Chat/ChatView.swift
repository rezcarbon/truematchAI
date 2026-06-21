//
//  ChatView.swift
//  TrueMatch
//
//  The conversational AI assistant. A scrolling transcript of user/assistant
//  bubbles, a composer pinned to the bottom, suggestion chips, and a sessions
//  drawer for switching between or starting conversations. The backend picks the
//  right role agent automatically, so this screen is shared across all roles.
//

import SwiftUI

struct ChatView: View {
    @StateObject private var viewModel = ChatViewModel()
    @StateObject private var speech = SpeechRecognizer()
    @State private var showSessions = false
    @FocusState private var inputFocused: Bool

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                transcript
                Divider()
                suggestionRow
                composer
            }
            .navigationTitle("Assistant")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        showSessions = true
                    } label: {
                        Image(systemName: "list.bullet.rectangle")
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        Task { await viewModel.newSession() }
                    } label: {
                        Image(systemName: "square.and.pencil")
                    }
                }
            }
            .sheet(isPresented: $showSessions) {
                ChatSessionsSheet(viewModel: viewModel)
            }
            .task {
                if viewModel.currentSessionId == nil {
                    await viewModel.startIfNeeded()
                }
            }
            .alert("Something went wrong",
                   isPresented: Binding(
                        get: { viewModel.errorMessage != nil },
                        set: { if !$0 { viewModel.errorMessage = nil } })) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }

    // MARK: - Transcript

    private var transcript: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    if viewModel.messages.isEmpty && !viewModel.isLoadingSession {
                        emptyState
                    }
                    ForEach(viewModel.messages) { bubble in
                        ChatBubbleView(bubble: bubble)
                            .id(bubble.id)
                    }
                    if viewModel.isSending {
                        TypingIndicator()
                            .id("typing")
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
            .onChange(of: viewModel.messages.count) { _, _ in
                withAnimation { proxy.scrollTo(lastAnchor, anchor: .bottom) }
            }
            .onChange(of: viewModel.isSending) { _, sending in
                if sending { withAnimation { proxy.scrollTo("typing", anchor: .bottom) } }
            }
        }
    }

    private var lastAnchor: String {
        viewModel.messages.last?.id ?? "typing"
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "sparkles")
                .font(.system(size: 40))
                .foregroundStyle(TrueMatchTheme.accentColor)
            Text("How can I help?")
                .font(.title3.weight(.semibold))
            Text("Ask about candidates, positions, assessments, or your hiring pipeline.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 60)
    }

    // MARK: - Suggestions

    @ViewBuilder
    private var suggestionRow: some View {
        if !viewModel.suggestions.isEmpty {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(viewModel.suggestions, id: \.self) { s in
                        Button {
                            viewModel.useSuggestion(s)
                            inputFocused = true
                        } label: {
                            Text(s)
                                .font(.caption)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 7)
                                .background(TrueMatchTheme.accentColor.opacity(0.12))
                                .foregroundStyle(TrueMatchTheme.accentColor)
                                .clipShape(Capsule())
                        }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
            }
        }
    }

    // MARK: - Composer

    private var composer: some View {
        HStack(alignment: .bottom, spacing: 10) {
            TextField(speech.isRecording ? "Listening…" : "Message", text: $viewModel.inputText, axis: .vertical)
                .lineLimit(1...5)
                .focused($inputFocused)
                .padding(.horizontal, 14)
                .padding(.vertical, 9)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                .onSubmit { Task { await viewModel.send() } }

            Button {
                speech.toggle()
            } label: {
                Image(systemName: speech.isRecording ? "mic.circle.fill" : "mic.circle")
                    .font(.system(size: 30))
                    .foregroundStyle(speech.isRecording ? Color.red : TrueMatchTheme.accentColor)
                    .symbolEffect(.pulse, isActive: speech.isRecording)
            }
            .accessibilityLabel(speech.isRecording ? "Stop dictation" : "Dictate message")

            Button {
                Task { await viewModel.send() }
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 30))
                    .foregroundStyle(viewModel.canSend ? TrueMatchTheme.accentColor : Color.secondary.opacity(0.4))
            }
            .disabled(!viewModel.canSend)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .onChange(of: speech.transcript) { _, text in
            if speech.isRecording || !text.isEmpty {
                viewModel.inputText = text
            }
        }
        .onChange(of: speech.errorMessage) { _, message in
            if let message { viewModel.errorMessage = message }
        }
        .onDisappear { speech.stop() }
    }
}

// MARK: - Bubble

struct ChatBubbleView: View {
    let bubble: ChatBubble

    private var isUser: Bool { bubble.role == .user }

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 40) }
            VStack(alignment: isUser ? .trailing : .leading, spacing: 6) {
                Text(bubble.content)
                    .font(.callout)
                    .foregroundStyle(isUser ? Color.white : Color.primary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        isUser ? TrueMatchTheme.accentColor : Color(.secondarySystemBackground)
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

                if !bubble.actions.isEmpty {
                    ForEach(bubble.actions) { action in
                        HStack(spacing: 6) {
                            Image(systemName: icon(for: action.status))
                                .font(.caption2)
                                .foregroundStyle(color(for: action.status))
                            Text(action.description)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            if !isUser { Spacer(minLength: 40) }
        }
    }

    private func icon(for status: String) -> String {
        switch status {
        case "completed": return "checkmark.circle.fill"
        case "failed": return "xmark.octagon.fill"
        default: return "clock.fill"
        }
    }

    private func color(for status: String) -> Color {
        switch status {
        case "completed": return .green
        case "failed": return .red
        default: return .orange
        }
    }
}

// MARK: - Typing indicator

struct TypingIndicator: View {
    @State private var phase = 0.0
    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3) { i in
                Circle()
                    .fill(Color.secondary.opacity(0.5))
                    .frame(width: 7, height: 7)
                    .scaleEffect(phase == Double(i) ? 1.0 : 0.5)
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .onAppear {
            withAnimation(.easeInOut(duration: 0.6).repeatForever()) { phase = 2 }
        }
    }
}

// MARK: - Sessions drawer

struct ChatSessionsSheet: View {
    @ObservedObject var viewModel: ChatViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                ForEach(viewModel.sessions) { session in
                    Button {
                        Task { await viewModel.selectSession(id: session.id) }
                        dismiss()
                    } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(session.title)
                                    .font(.subheadline)
                                    .foregroundStyle(.primary)
                                Text("\(session.messageCount) message\(session.messageCount == 1 ? "" : "s")")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            if session.id == viewModel.currentSessionId {
                                Image(systemName: "checkmark")
                                    .foregroundStyle(TrueMatchTheme.accentColor)
                            }
                        }
                    }
                }
                .onDelete { indexSet in
                    for index in indexSet {
                        let id = viewModel.sessions[index].id
                        Task { await viewModel.deleteSession(id: id) }
                    }
                }
            }
            .navigationTitle("Conversations")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        Task { await viewModel.newSession() }
                        dismiss()
                    } label: {
                        Label("New", systemImage: "square.and.pencil")
                    }
                }
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
