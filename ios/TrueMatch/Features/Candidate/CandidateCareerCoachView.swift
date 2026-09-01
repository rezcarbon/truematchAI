//
//  CandidateCareerCoachView.swift
//  TrueMatch
//
//  Chat interface for career guidance with structured responses, suggested
//  follow-ups, and WebSocket real-time communication.
//

import SwiftUI

struct CandidateCareerCoachView: View {
    @StateObject private var viewModel: CareerCoachViewModel
    @Environment(\.trueMatchTheme) var theme
    @FocusState private var inputFocused: Bool

    init(candidateId: String) {
        _viewModel = StateObject(wrappedValue: CareerCoachViewModel(candidateId: candidateId))
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Connection Status Bar
                if viewModel.connectionStatus != .connected {
                    HStack(spacing: theme.spacing.sm) {
                        ProgressView()
                            .scaleEffect(0.8)

                        Text(connectionStatusText())
                            .font(theme.typography.caption)

                        Spacer()
                    }
                    .padding(theme.spacing.xs)
                    .background(Color(.systemYellow).opacity(0.2))
                }

                // Transcript
                ScrollViewReader { proxy in
                    ScrollView {
                        if viewModel.messages.isEmpty {
                            EmptyCareerCoachStateView(theme: theme)
                                .frame(maxHeight: .infinity)
                        } else {
                            LazyVStack(alignment: .leading, spacing: theme.spacing.sm) {
                                ForEach(viewModel.messages) { message in
                                    CoachMessageView(message: message, theme: theme)
                                        .id(message.id)
                                }
                            }
                            .padding(theme.spacing.sm)
                        }
                    }
                    .onChange(of: viewModel.messages.count) { _, _ in
                        withAnimation {
                            proxy.scrollTo(viewModel.messages.last?.id, anchor: .bottom)
                        }
                    }
                }

                Divider()

                // Suggested Follow-ups
                if !viewModel.suggestedFollowUps.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: theme.spacing.xs) {
                            ForEach(viewModel.suggestedFollowUps, id: \.self) { suggestion in
                                Button {
                                    viewModel.useSuggestion(suggestion)
                                    inputFocused = true
                                } label: {
                                    Text(suggestion)
                                        .font(theme.typography.caption)
                                        .lineLimit(2)
                                        .padding(theme.spacing.xs)
                                        .background(Color(.systemGray6))
                                        .foregroundColor(.primary)
                                        .cornerRadius(theme.cornerRadii.sm)
                                }
                            }
                        }
                        .padding(.horizontal, theme.spacing.sm)
                    }
                    .padding(.vertical, theme.spacing.xs)

                    Divider()
                }

                // Message Composer
                HStack(spacing: theme.spacing.sm) {
                    TextField("Ask for career guidance...", text: $viewModel.inputText, axis: .vertical)
                        .font(theme.typography.body)
                        .lineLimit(1...5)
                        .focused($inputFocused)
                        .padding(theme.spacing.xs)
                        .background(Color(.systemGray6))
                        .cornerRadius(theme.cornerRadii.sm)
                        .accessibilityLabel("Career guidance message input")
                        .accessibilityHint("Type your question and press send")

                    Button {
                        Task {
                            await viewModel.send()
                        }
                    } label: {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 24))
                    }
                    .disabled(!viewModel.canSend)
                    .foregroundColor(viewModel.canSend ? theme.colors.primary : .gray)
                    .accessibilityLabel("Send message")
                    .accessibilityHint(viewModel.canSend ? "Send your message" : "Enter a message to send")
                }
                .padding(theme.spacing.sm)
            }
            .navigationTitle("Career Coach")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button {
                            viewModel.clearHistory()
                        } label: {
                            Label("Clear History", systemImage: "trash")
                        }

                        Button {
                            viewModel.disconnect()
                        } label: {
                            Label("Disconnect", systemImage: "wifi.slash")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .task {
                if viewModel.connectionStatus == .disconnected {
                    await viewModel.connectWebSocket()
                }
            }
            .onDisappear {
                viewModel.disconnect()
            }
            .alert("Error", isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }

    private func connectionStatusText() -> String {
        switch viewModel.connectionStatus {
        case .connecting:
            return "Connecting..."
        case .connected:
            return "Connected"
        case .disconnected:
            return "Disconnected"
        case .failed:
            return "Connection Failed"
        }
    }
}

// MARK: - Coach Message View

struct CoachMessageView: View {
    let message: CareerCoachMessage
    let theme: TrueMatchTheme
    @State private var expandedStepId: String?

    var isUser: Bool { message.role == "user" }

    var body: some View {
        VStack(alignment: isUser ? .trailing : .leading, spacing: theme.spacing.sm) {
            if isUser {
                // User message
                Text(message.content)
                    .font(theme.typography.body)
                    .padding(theme.spacing.sm)
                    .background(theme.colors.primary)
                    .foregroundColor(.white)
                    .cornerRadius(theme.cornerRadii.md)
                    .frame(maxWidth: .infinity, alignment: .trailing)
            } else {
                // Assistant message
                VStack(alignment: .leading, spacing: theme.spacing.sm) {
                    // Main content
                    Text(message.content)
                        .font(theme.typography.body)
                        .lineSpacing(4)

                    // Structured content
                    if let structured = message.structuredContent {
                        if let steps = structured.steps, !steps.isEmpty {
                            VStack(alignment: .leading, spacing: theme.spacing.sm) {
                                Text("Steps:")
                                    .font(theme.typography.headline)

                                ForEach(steps) { step in
                                    ExpandableStepView(
                                        step: step,
                                        isExpanded: expandedStepId == step.id,
                                        onTap: {
                                            withAnimation {
                                                expandedStepId = expandedStepId == step.id ? nil : step.id
                                            }
                                        },
                                        theme: theme
                                    )
                                }
                            }
                            .padding(theme.spacing.sm)
                            .background(Color(.systemGray6))
                            .cornerRadius(theme.cornerRadii.sm)
                        }

                        if let resources = structured.resources, !resources.isEmpty {
                            VStack(alignment: .leading, spacing: theme.spacing.xs) {
                                Text("Resources:")
                                    .font(theme.typography.headline)

                                ForEach(resources) { resource in
                                    ResourceLinkView(resource: resource, theme: theme)
                                }
                            }
                        }

                        if let actionItems = structured.actionItems, !actionItems.isEmpty {
                            VStack(alignment: .leading, spacing: theme.spacing.xs) {
                                Text("Action Items:")
                                    .font(theme.typography.headline)

                                ForEach(actionItems, id: \.self) { item in
                                    HStack(spacing: theme.spacing.xs) {
                                        Image(systemName: "checkmark.circle")
                                            .foregroundColor(theme.colors.success)

                                        Text(item)
                                            .font(theme.typography.body)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(theme.spacing.sm)
                .background(Color(.systemGray6))
                .cornerRadius(theme.cornerRadii.md)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }
}

// MARK: - Expandable Step View

struct ExpandableStepView: View {
    let step: CoachingStep
    let isExpanded: Bool
    let onTap: () -> Void
    let theme: TrueMatchTheme

    var body: some View {
        VStack(spacing: 0) {
            Button {
                onTap()
            } label: {
                HStack(spacing: theme.spacing.sm) {
                    Text("\(step.stepNumber).")
                        .font(theme.typography.headline)
                        .foregroundColor(theme.colors.primary)

                    Text(step.title)
                        .font(theme.typography.body)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Image(systemName: "chevron.right")
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                        .foregroundColor(.gray)
                }
                .contentShape(Rectangle())
            }
            .padding(theme.spacing.xs)

            if isExpanded {
                Divider()

                VStack(alignment: .leading, spacing: theme.spacing.sm) {
                    Text(step.description)
                        .font(theme.typography.body)

                    if let resources = step.resources, !resources.isEmpty {
                        VStack(alignment: .leading, spacing: theme.spacing.xs) {
                            ForEach(resources) { resource in
                                ResourceLinkView(resource: resource, theme: theme)
                            }
                        }
                    }
                }
                .padding(theme.spacing.xs)
            }
        }
        .background(Color(.systemBackground))
        .cornerRadius(theme.cornerRadii.sm)
    }
}

// MARK: - Resource Link View

struct ResourceLinkView: View {
    let resource: CoachingResource
    let theme: TrueMatchTheme

    var body: some View {
        HStack(spacing: theme.spacing.sm) {
            Image(systemName: "link.circle.fill")
                .foregroundColor(theme.colors.primary)

            VStack(alignment: .leading, spacing: theme.spacing.xxxs) {
                Text(resource.title)
                    .font(theme.typography.body)

                if let duration = resource.duration {
                    Text("\(duration) min")
                        .font(theme.typography.caption)
                        .foregroundColor(.gray)
                }
            }

            Spacer()

            Image(systemName: "arrow.up.right")
                .font(.caption)
                .foregroundColor(theme.colors.primary)
        }
        .onTapGesture {
            if let url = URL(string: resource.url ?? "") {
                UIApplication.shared.open(url)
            }
        }
    }
}

// MARK: - Empty State

struct EmptyCareerCoachStateView: View {
    let theme: TrueMatchTheme

    var body: some View {
        VStack(spacing: theme.spacing.lg) {
            Image(systemName: "sparkles.rectangle.stack.fill")
                .font(.system(size: 64))
                .foregroundColor(theme.colors.primary)

            VStack(spacing: theme.spacing.sm) {
                Text("Career Coach")
                    .font(theme.typography.headline)

                Text("Ask for personalized career guidance, interview prep, skill development, and more")
                    .font(theme.typography.body)
                    .foregroundColor(.gray)
            }
            .multilineTextAlignment(.center)
        }
        .padding(theme.spacing.lg)
    }
}

#Preview {
    CandidateCareerCoachView(candidateId: "preview-candidate")
        .environment(\.trueMatchTheme, TrueMatchTheme())
}
