//
//  CandidateApplicationTrackingView.swift
//  TrueMatch
//
//  Displays application pipeline visualization, stage-based organization,
//  timeline events, interview prep, and offer details.
//

import SwiftUI

struct CandidateApplicationTrackingView: View {
    @StateObject private var viewModel: ApplicationTrackingViewModel
    @Environment(\.trueMatchTheme) var theme
    @State private var selectedApplication: ApplicationStatus?
    @State private var showApplicationDetail = false

    init(candidateId: String) {
        _viewModel = StateObject(wrappedValue: ApplicationTrackingViewModel(candidateId: candidateId))
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Pipeline Visualization
                PipelineStagesView(
                    stages: viewModel.stageOrder,
                    applicationsByStage: viewModel.applicationsByStage,
                    selectedStage: $viewModel.selectedStage,
                    theme: theme
                )
                .padding(theme.spacing.sm)

                // Stage Content
                ScrollView {
                    if viewModel.isLoading {
                        ProgressView()
                            .frame(maxHeight: .infinity)
                            .padding(theme.spacing.lg)
                    } else {
                        let stageApplications = viewModel.getApplicationsForStage(viewModel.selectedStage)

                        if stageApplications.isEmpty {
                            EmptyApplicationStateView(stage: viewModel.selectedStage, theme: theme)
                                .frame(maxHeight: .infinity)
                        } else {
                            LazyVStack(spacing: theme.spacing.sm) {
                                ForEach(stageApplications) { application in
                                    ApplicationCardView(
                                        application: application,
                                        theme: theme
                                    )
                                    .onTapGesture {
                                        selectedApplication = application
                                        showApplicationDetail = true
                                    }
                                }
                            }
                            .padding(theme.spacing.sm)
                        }
                    }
                }
            }
            .navigationTitle("Applications")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showApplicationDetail) {
                if let application = selectedApplication {
                    ApplicationDetailView(
                        application: application,
                        viewModel: viewModel,
                        theme: theme
                    )
                }
            }
            .task {
                if viewModel.applications.isEmpty {
                    await viewModel.loadApplications()
                }
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
}

// MARK: - Pipeline Stages View

struct PipelineStagesView: View {
    let stages: [String]
    let applicationsByStage: [String: [ApplicationStatus]]
    @Binding var selectedStage: String
    let theme: TrueMatchTheme

    var body: some View {
        VStack(spacing: theme.spacing.sm) {
            Text("Application Pipeline")
                .font(theme.typography.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: theme.spacing.sm) {
                    ForEach(stages, id: \.self) { stage in
                        VStack(spacing: theme.spacing.xs) {
                            VStack(spacing: theme.spacing.xxxs) {
                                Text(stage.capitalized)
                                    .font(theme.typography.caption)
                                    .foregroundColor(selectedStage == stage ? .white : .primary)

                                let count = applicationsByStage[stage]?.count ?? 0
                                Text("\(count)")
                                    .font(theme.typography.headline)
                                    .foregroundColor(selectedStage == stage ? .white : theme.colors.primary)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(theme.spacing.xs)
                            .background(selectedStage == stage ? theme.colors.primary : Color(.systemGray6))
                            .cornerRadius(theme.cornerRadii.sm)

                            if stage != stages.last {
                                HStack {
                                    Image(systemName: "chevron.right")
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                }
                            }
                        }
                        .onTapGesture {
                            withAnimation {
                                selectedStage = stage
                            }
                        }
                        .accessibilityElement()
                        .accessibilityLabel("\(stage.capitalized) stage")
                        .accessibilityValue("\(applicationsByStage[stage]?.count ?? 0) applications")
                        .accessibilityHint("Select to view \(stage) applications")
                    }
                }
            }
        }
        .padding(theme.spacing.sm)
        .background(Color(.systemGray6))
        .cornerRadius(theme.cornerRadii.md)
    }
}

// MARK: - Application Card

struct ApplicationCardView: View {
    let application: ApplicationStatus
    let theme: TrueMatchTheme

    var statusColor: Color {
        switch application.stage {
        case "applied": return theme.colors.info
        case "reviewing": return theme.colors.warning
        case "interviewing": return theme.colors.primary
        case "offer": return theme.colors.success
        case "rejected": return theme.colors.error
        default: return .gray
        }
    }

    var statusIcon: String {
        switch application.stage {
        case "applied": return "paperclip.circle.fill"
        case "reviewing": return "magnifyingglass.circle.fill"
        case "interviewing": return "video.circle.fill"
        case "offer": return "star.circle.fill"
        case "rejected": return "xmark.circle.fill"
        default: return "questionmark.circle.fill"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.sm) {
            HStack {
                VStack(alignment: .leading, spacing: theme.spacing.xs) {
                    Text(application.jobTitle)
                        .font(theme.typography.headline)

                    Text(application.company)
                        .font(theme.typography.body)
                        .foregroundColor(.gray)

                    HStack(spacing: theme.spacing.xs) {
                        Image(systemName: statusIcon)
                            .foregroundColor(statusColor)

                        Text(application.stage.capitalized)
                            .font(theme.typography.caption)
                            .foregroundColor(statusColor)

                        Spacer()

                        Text(formatDate(application.appliedDate))
                            .font(theme.typography.caption)
                            .foregroundColor(.gray)
                    }
                }

                Spacer()

                VStack(alignment: .trailing, spacing: theme.spacing.xxxs) {
                    if let latestEvent = application.timeline.last {
                        Text("Latest Update")
                            .font(theme.typography.caption)
                            .foregroundColor(.gray)

                        Text(formatDate(latestEvent.timestamp))
                            .font(theme.typography.caption)
                    }
                }
            }

            // Timeline Preview
            if !application.timeline.isEmpty {
                VStack(spacing: theme.spacing.xs) {
                    Divider()

                    HStack(spacing: theme.spacing.xs) {
                        Image(systemName: "clock.fill")
                            .font(.caption)
                            .foregroundColor(.gray)

                        Text(application.timeline.last?.description ?? "")
                            .font(theme.typography.caption)
                            .lineLimit(2)
                            .foregroundColor(.gray)
                    }
                }
            }

            // Interview Sessions Preview
            if let upcomingInterview = application.interviewSessions.first(where: { $0.status == "scheduled" }) {
                HStack(spacing: theme.spacing.sm) {
                    Image(systemName: "calendar.circle.fill")
                        .foregroundColor(theme.colors.primary)

                    VStack(alignment: .leading, spacing: theme.spacing.xxxs) {
                        Text("Interview Scheduled")
                            .font(theme.typography.caption)

                        if let date = upcomingInterview.scheduledDate {
                            Text(formatDate(date))
                                .font(theme.typography.caption)
                                .foregroundColor(theme.colors.primary)
                        }
                    }

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                .padding(theme.spacing.xs)
                .background(Color(.systemGray6))
                .cornerRadius(theme.cornerRadii.sm)
            }

            // Offer Preview
            if let offer = application.offerDetails {
                HStack(spacing: theme.spacing.sm) {
                    Image(systemName: "star.circle.fill")
                        .foregroundColor(theme.colors.success)

                    VStack(alignment: .leading, spacing: theme.spacing.xxxs) {
                        Text("Offer Received")
                            .font(theme.typography.caption)

                        Text(String(format: "%s%,d", "$", offer.baseSalary))
                            .font(theme.typography.headline)
                            .foregroundColor(theme.colors.success)
                    }

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                .padding(theme.spacing.xs)
                .background(Color(.systemGray6))
                .cornerRadius(theme.cornerRadii.sm)
            }
        }
        .padding(theme.spacing.sm)
        .background(Color(.systemBackground))
        .cornerRadius(theme.cornerRadii.md)
        .overlay(
            RoundedRectangle(cornerRadius: theme.cornerRadii.md)
                .stroke(Color(.systemGray6), lineWidth: 1)
        )
    }

    private func formatDate(_ dateString: String) -> String {
        guard let date = ISO8601DateFormatter().date(from: dateString) else {
            return dateString
        }
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d"
        return formatter.string(from: date)
    }
}

// MARK: - Application Detail Modal

struct ApplicationDetailView: View {
    let application: ApplicationStatus
    let viewModel: ApplicationTrackingViewModel
    let theme: TrueMatchTheme
    @Environment(\.dismiss) var dismiss
    @State private var expandedSection: String?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: theme.spacing.lg) {
                    // Header
                    VStack(alignment: .leading, spacing: theme.spacing.sm) {
                        Text(application.jobTitle)
                            .font(theme.typography.title)

                        Text(application.company)
                            .font(theme.typography.headline)
                            .foregroundColor(.gray)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(theme.spacing.sm)

                    // Timeline Section
                    ExpandableDetailSection(
                        title: "Timeline",
                        isExpanded: expandedSection == "timeline",
                        onTap: { expandedSection = expandedSection == "timeline" ? nil : "timeline" }
                    ) {
                        TimelineView(events: application.timeline, theme: theme)
                    }

                    // Interview Sessions
                    if !application.interviewSessions.isEmpty {
                        ExpandableDetailSection(
                            title: "Interviews",
                            isExpanded: expandedSection == "interviews",
                            onTap: { expandedSection = expandedSection == "interviews" ? nil : "interviews" }
                        ) {
                            InterviewSessionsView(
                                sessions: application.interviewSessions,
                                application: application,
                                viewModel: viewModel,
                                theme: theme
                            )
                        }
                    }

                    // Offer Details
                    if let offer = application.offerDetails {
                        ExpandableDetailSection(
                            title: "Offer",
                            isExpanded: expandedSection == "offer",
                            onTap: { expandedSection = expandedSection == "offer" ? nil : "offer" }
                        ) {
                            OfferDetailView(offer: offer, application: application, viewModel: viewModel, theme: theme)
                        }
                    }

                    // Notes
                    if let notes = application.notes {
                        VStack(alignment: .leading, spacing: theme.spacing.sm) {
                            Text("Notes")
                                .font(theme.typography.headline)

                            Text(notes)
                                .font(theme.typography.body)
                                .padding(theme.spacing.sm)
                                .background(Color(.systemGray6))
                                .cornerRadius(theme.cornerRadii.sm)
                        }
                        .padding(theme.spacing.sm)
                    }
                }
                .padding(theme.spacing.sm)
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

// MARK: - Expandable Detail Section

struct ExpandableDetailSection<Content: View>: View {
    let title: String
    let isExpanded: Bool
    let onTap: () -> Void
    @ViewBuilder let content: () -> Content
    @Environment(\.trueMatchTheme) var theme

    var body: some View {
        VStack(spacing: 0) {
            Button {
                withAnimation {
                    onTap()
                }
            } label: {
                HStack {
                    Text(title)
                        .font(theme.typography.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Image(systemName: "chevron.right")
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                }
                .contentShape(Rectangle())
            }
            .padding(theme.spacing.sm)

            if isExpanded {
                Divider()
                    .padding(.horizontal, theme.spacing.sm)

                content()
                    .padding(theme.spacing.sm)
            }
        }
        .background(Color(.systemGray6))
        .cornerRadius(theme.cornerRadii.md)
        .padding(.horizontal, theme.spacing.sm)
    }
}

// MARK: - Timeline View

struct TimelineView: View {
    let events: [ApplicationEvent]
    let theme: TrueMatchTheme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.sm) {
            ForEach(Array(events.enumerated()), id: \.element.id) { index, event in
                HStack(spacing: theme.spacing.sm) {
                    VStack {
                        Circle()
                            .fill(theme.colors.primary)
                            .frame(width: 12, height: 12)

                        if index < events.count - 1 {
                            VStack(spacing: 0) {
                                ForEach(0..<2, id: \.self) { _ in
                                    RoundedRectangle(cornerRadius: 1)
                                        .fill(Color(.systemGray6))
                                        .frame(width: 2, height: 4)
                                }
                            }
                        }
                    }

                    VStack(alignment: .leading, spacing: theme.spacing.xs) {
                        Text(event.eventType.capitalized)
                            .font(theme.typography.headline)

                        Text(event.description)
                            .font(theme.typography.body)
                            .foregroundColor(.gray)

                        Text(formatDate(event.timestamp))
                            .font(theme.typography.caption)
                            .foregroundColor(.gray)
                    }

                    Spacer()
                }
            }
        }
    }

    private func formatDate(_ dateString: String) -> String {
        guard let date = ISO8601DateFormatter().date(from: dateString) else {
            return dateString
        }
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d, h:mm a"
        return formatter.string(from: date)
    }
}

// MARK: - Interview Sessions View

struct InterviewSessionsView: View {
    let sessions: [InterviewSession]
    let application: ApplicationStatus
    let viewModel: ApplicationTrackingViewModel
    let theme: TrueMatchTheme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.sm) {
            ForEach(sessions) { session in
                VStack(alignment: .leading, spacing: theme.spacing.sm) {
                    HStack {
                        VStack(alignment: .leading, spacing: theme.spacing.xs) {
                            Text(session.interviewType.capitalized)
                                .font(theme.typography.headline)

                            Text(session.status.capitalized)
                                .font(theme.typography.caption)
                                .foregroundColor(session.status == "scheduled" ? theme.colors.warning : theme.colors.success)
                        }

                        Spacer()

                        if session.status == "scheduled", let date = session.scheduledDate {
                            Button {
                                viewModel.rescheduleInterview(session)
                            } label: {
                                Label("Reschedule", systemImage: "calendar")
                                    .font(theme.typography.caption)
                            }
                            .buttonStyle(.bordered)
                        }
                    }

                    if let prepMaterials = session.prepMaterials, !prepMaterials.isEmpty {
                        VStack(alignment: .leading, spacing: theme.spacing.xs) {
                            Text("Preparation Materials")
                                .font(theme.typography.caption)
                                .foregroundColor(.gray)

                            ForEach(prepMaterials) { material in
                                HStack(spacing: theme.spacing.xs) {
                                    Image(systemName: "doc.fill")
                                        .font(.caption)
                                        .foregroundColor(theme.colors.primary)

                                    Text(material.title)
                                        .font(theme.typography.caption)
                                }
                            }
                        }
                    }
                }
                .padding(theme.spacing.sm)
                .background(Color(.systemBackground))
                .cornerRadius(theme.cornerRadii.sm)
            }
        }
    }
}

// MARK: - Offer Detail View

struct OfferDetailView: View {
    let offer: OfferDetails
    let application: ApplicationStatus
    let viewModel: ApplicationTrackingViewModel
    let theme: TrueMatchTheme
    @State private var showingConfirmation = false

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.sm) {
            // Salary and Benefits
            VStack(alignment: .leading, spacing: theme.spacing.sm) {
                HStack {
                    Text("Base Salary")
                    Spacer()
                    Text(String(format: "$%,d", offer.baseSalary))
                        .font(theme.typography.headline)
                }

                if let bonus = offer.bonus {
                    HStack {
                        Text("Bonus")
                        Spacer()
                        Text(String(format: "$%,d", bonus))
                            .foregroundColor(theme.colors.success)
                    }
                }

                if let equity = offer.equity {
                    HStack {
                        Text("Equity")
                        Spacer()
                        Text(equity)
                    }
                }
            }

            if !offer.benefits.isEmpty {
                VStack(alignment: .leading, spacing: theme.spacing.sm) {
                    Text("Benefits")
                        .font(theme.typography.headline)

                    ForEach(offer.benefits, id: \.self) { benefit in
                        HStack(spacing: theme.spacing.xs) {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(theme.colors.success)

                            Text(benefit)
                                .font(theme.typography.body)
                        }
                    }
                }
            }

            // Start Date
            HStack {
                Text("Start Date")
                Spacer()
                Text(formatDate(offer.startDate))
            }

            // Response Deadline
            if let deadline = offer.responseDeadline {
                HStack {
                    Text("Respond by")
                    Spacer()
                    Text(formatDate(deadline))
                        .foregroundColor(theme.colors.warning)
                }
            }

            // Action Buttons
            if offer.status == "pending" {
                HStack(spacing: theme.spacing.sm) {
                    Button {
                        Task {
                            await viewModel.declineOffer(application)
                        }
                    } label: {
                        Text("Decline")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)

                    Button {
                        Task {
                            await viewModel.acceptOffer(application)
                        }
                    } label: {
                        Text("Accept")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
        }
    }

    private func formatDate(_ dateString: String) -> String {
        guard let date = ISO8601DateFormatter().date(from: dateString) else {
            return dateString
        }
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM d, yyyy"
        return formatter.string(from: date)
    }
}

// MARK: - Empty State

struct EmptyApplicationStateView: View {
    let stage: String
    let theme: TrueMatchTheme

    var body: some View {
        VStack(spacing: theme.spacing.lg) {
            Image(systemName: "tray.fill")
                .font(.system(size: 64))
                .foregroundColor(.gray)

            VStack(spacing: theme.spacing.sm) {
                Text("No Applications in \(stage.capitalized)")
                    .font(theme.typography.headline)

                Text("Your applications will appear here as you progress through the interview process")
                    .font(theme.typography.body)
                    .foregroundColor(.gray)
            }
            .multilineTextAlignment(.center)
        }
        .padding(theme.spacing.lg)
    }
}

#Preview {
    CandidateApplicationTrackingView(candidateId: "preview-candidate")
        .environment(\.trueMatchTheme, TrueMatchTheme())
}
