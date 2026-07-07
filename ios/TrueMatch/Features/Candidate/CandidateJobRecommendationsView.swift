//
//  CandidateJobRecommendationsView.swift
//  TrueMatch
//
//  Displays swipe-based job browsing with full-screen job cards, match scores,
//  skills radar, and save/apply/reject buttons.
//

import SwiftUI

struct CandidateJobRecommendationsView: View {
    @StateObject private var viewModel: JobRecommendationsViewModel
    @Environment(\.trueMatchTheme) var theme
    @State private var cardOffset: CGFloat = 0
    @State private var cardRotation: Double = 0

    init(candidateId: String) {
        _viewModel = StateObject(wrappedValue: JobRecommendationsViewModel(candidateId: candidateId))
    }

    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                LinearGradient(
                    gradient: Gradient(colors: [
                        Color(.systemBackground),
                        Color(.systemGray6)
                    ]),
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                VStack(spacing: 0) {
                    // Header
                    HStack {
                        Text("Job Matches")
                            .font(theme.typography.title)

                        Spacer()

                        if viewModel.jobsRemaining > 0 {
                            Text("\(viewModel.jobsRemaining) left")
                                .font(theme.typography.caption)
                                .foregroundColor(.gray)
                        }
                    }
                    .padding(theme.spacing.sm)

                    // Job Card Stack
                    ZStack {
                        if viewModel.jobs.isEmpty && !viewModel.isLoading {
                            EmptyJobStateView(theme: theme)
                        } else if let currentJob = viewModel.currentJob {
                            JobCardView(
                                job: currentJob,
                                isSaved: viewModel.savedJobs.contains(currentJob.id),
                                theme: theme
                            )
                            .offset(x: cardOffset)
                            .rotationEffect(.degrees(cardRotation))
                            .gesture(
                                DragGesture()
                                    .onChanged { gesture in
                                        withAnimation(.easeOut(duration: 0.1)) {
                                            cardOffset = gesture.translation.width
                                            cardRotation = Double(gesture.translation.width / 10)
                                        }
                                    }
                                    .onEnded { gesture in
                                        handleSwipe(with: gesture)
                                    }
                            )
                            .transition(.opacity.combined(with: .scale))
                        }
                    }
                    .frame(maxHeight: .infinity)
                    .padding(theme.spacing.sm)

                    // Action Buttons
                    if viewModel.currentJob != nil {
                        VStack(spacing: theme.spacing.sm) {
                            HStack(spacing: theme.spacing.sm) {
                                // Reject Button
                                Button {
                                    Task {
                                        withAnimation {
                                            await viewModel.rejectCurrentJob()
                                            resetCard()
                                        }
                                    }
                                } label: {
                                    HStack {
                                        Image(systemName: "xmark")
                                        Text("Pass")
                                    }
                                    .frame(maxWidth: .infinity)
                                    .padding(theme.spacing.sm)
                                    .background(Color(.systemGray6))
                                    .foregroundColor(.red)
                                    .cornerRadius(theme.cornerRadii.md)
                                }

                                // Save/Apply Button
                                Menu {
                                    Button {
                                        Task {
                                            await viewModel.saveCurrentJob()
                                            resetCard()
                                        }
                                    } label: {
                                        Label("Save", systemImage: "bookmark.fill")
                                    }

                                    Button {
                                        viewModel.applyForCurrentJob()
                                    } label: {
                                        Label("Apply", systemImage: "arrow.up.right")
                                    }
                                } label: {
                                    HStack {
                                        Image(systemName: "heart.fill")
                                        Text("Like")
                                    }
                                    .frame(maxWidth: .infinity)
                                    .padding(theme.spacing.sm)
                                    .background(theme.colors.primary)
                                    .foregroundColor(.white)
                                    .cornerRadius(theme.cornerRadii.md)
                                }
                            }

                            Text("← Swipe left to pass • Swipe right to like →")
                                .font(theme.typography.caption)
                                .foregroundColor(.gray)
                                .frame(maxWidth: .infinity, alignment: .center)
                        }
                        .padding(theme.spacing.sm)
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .task {
                if viewModel.jobs.isEmpty {
                    await viewModel.loadJobs()
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

    private func handleSwipe(with gesture: DragGesture.Value) {
        let threshold: CGFloat = 100

        withAnimation(.easeOut(duration: 0.3)) {
            if gesture.translation.width > threshold {
                // Swiped right - save
                Task {
                    await viewModel.handleSwipe(direction: .right)
                    resetCard()
                }
            } else if gesture.translation.width < -threshold {
                // Swiped left - reject
                Task {
                    await viewModel.handleSwipe(direction: .left)
                    resetCard()
                }
            } else {
                // Not swiped far enough - reset
                resetCard()
            }
        }
    }

    private func resetCard() {
        withAnimation(.easeOut(duration: 0.2)) {
            cardOffset = 0
            cardRotation = 0
        }
    }
}

// MARK: - Job Card

struct JobCardView: View {
    let job: JobRecommendation
    let isSaved: Bool
    let theme: TrueMatchTheme

    @State private var expandedSection: String?

    var body: some View {
        VStack(spacing: 0) {
            // Header
            VStack(alignment: .leading, spacing: theme.spacing.sm) {
                HStack {
                    VStack(alignment: .leading, spacing: theme.spacing.xs) {
                        Text(job.jobTitle)
                            .font(theme.typography.headline)

                        Text(job.company)
                            .font(theme.typography.body)
                            .foregroundColor(.gray)

                        HStack(spacing: theme.spacing.sm) {
                            Label(job.location, systemImage: "mappin.circle.fill")
                                .font(theme.typography.caption)
                                .foregroundColor(.gray)

                            Label(job.jobType, systemImage: "briefcase.fill")
                                .font(theme.typography.caption)
                                .foregroundColor(.gray)
                        }
                    }

                    Spacer()

                    VStack(alignment: .trailing, spacing: theme.spacing.xxxs) {
                        if isSaved {
                            Image(systemName: "bookmark.fill")
                                .foregroundColor(theme.colors.primary)
                        }

                        Text(String(format: "%.0f%%", job.matchScore))
                            .font(theme.typography.headline)
                            .foregroundColor(theme.colors.primary)

                        Text("match")
                            .font(theme.typography.caption)
                            .foregroundColor(.gray)
                    }
                }

                Divider()

                // Three Scores
                HStack(spacing: theme.spacing.sm) {
                    ScoreBarView(
                        label: "Traditional",
                        score: job.traditionalScore,
                        color: theme.colors.traditional
                    )

                    ScoreBarView(
                        label: "Semantic",
                        score: job.semanticScore,
                        color: theme.colors.primary
                    )

                    ScoreBarView(
                        label: "Capability",
                        score: job.capabilityScore,
                        color: theme.colors.capability
                    )
                }
            }
            .padding(theme.spacing.sm)

            // Scrollable Content
            ScrollView {
                VStack(spacing: theme.spacing.md) {
                    // Skills Match
                    CollapsibleSectionView(
                        title: "Skills Match",
                        isExpanded: expandedSection == "skills",
                        onTap: { expandedSection = expandedSection == "skills" ? nil : "skills" }
                    ) {
                        VStack(alignment: .leading, spacing: theme.spacing.sm) {
                            ForEach(job.requiredSkills.prefix(5)) { skill in
                                SkillMatchRowView(skill: skill, theme: theme)
                            }

                            if job.requiredSkills.count > 5 {
                                Text("+\(job.requiredSkills.count - 5) more skills")
                                    .font(theme.typography.caption)
                                    .foregroundColor(theme.colors.primary)
                            }
                        }
                    }

                    // Strengths Aligned
                    if !job.matchedStrengths.isEmpty {
                        CollapsibleSectionView(
                            title: "Your Strengths",
                            isExpanded: expandedSection == "strengths",
                            onTap: { expandedSection = expandedSection == "strengths" ? nil : "strengths" }
                        ) {
                            VStack(alignment: .leading, spacing: theme.spacing.xs) {
                                ForEach(job.matchedStrengths, id: \.self) { strength in
                                    HStack(spacing: theme.spacing.xs) {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(theme.colors.success)

                                        Text(strength)
                                            .font(theme.typography.caption)
                                    }
                                }
                            }
                        }
                    }

                    // Salary
                    if let salary = job.salaryRange {
                        CollapsibleSectionView(
                            title: "Salary & Benefits",
                            isExpanded: expandedSection == "salary",
                            onTap: { expandedSection = expandedSection == "salary" ? nil : "salary" }
                        ) {
                            VStack(alignment: .leading, spacing: theme.spacing.sm) {
                                HStack {
                                    Text("Base Salary")
                                        .font(theme.typography.body)

                                    Spacer()

                                    Text(String(format: "%@%,d - %@%,d",
                                               salary.currency, salary.min, salary.currency, salary.max))
                                        .font(theme.typography.headline)
                                }
                            }
                        }
                    }

                    // Job Description
                    CollapsibleSectionView(
                        title: "Job Description",
                        isExpanded: expandedSection == "description",
                        onTap: { expandedSection = expandedSection == "description" ? nil : "description" }
                    ) {
                        Text(job.jobDescription)
                            .font(theme.typography.body)
                            .lineSpacing(4)
                    }
                }
                .padding(theme.spacing.sm)
            }
        }
        .background(Color(.systemBackground))
        .cornerRadius(theme.cornerRadii.lg)
        .shadow(color: Color.black.opacity(0.1), radius: 12, x: 0, y: 4)
    }
}

// MARK: - Score Bar

struct ScoreBarView: View {
    let label: String
    let score: Double
    let color: Color
    @Environment(\.trueMatchTheme) var theme

    var body: some View {
        VStack(spacing: theme.spacing.xxxs) {
            Text(String(format: "%.0f%%", score))
                .font(theme.typography.caption)
                .fontWeight(.semibold)

            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    // Background
                    RoundedRectangle(cornerRadius: theme.cornerRadii.xs)
                        .fill(Color(.systemGray6))

                    // Progress
                    RoundedRectangle(cornerRadius: theme.cornerRadii.xs)
                        .fill(color)
                        .frame(width: geometry.size.width * CGFloat(score / 100))
                }
            }
            .frame(height: 4)

            Text(label)
                .font(theme.typography.caption)
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Skill Match Row

struct SkillMatchRowView: View {
    let skill: SkillMatch
    let theme: TrueMatchTheme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xs) {
            HStack {
                Text(skill.skillName)
                    .font(theme.typography.body)

                Spacer()

                HStack(spacing: theme.spacing.xs) {
                    Text(skill.candidateLevel)
                        .font(theme.typography.caption)
                        .foregroundColor(.gray)

                    Text("→")
                        .font(theme.typography.caption)
                        .foregroundColor(theme.colors.primary)

                    Text(skill.requiredLevel)
                        .font(theme.typography.caption)
                        .foregroundColor(theme.colors.primary)
                }
            }

            ProgressView(value: skill.matchPercentage / 100)
                .tint(skill.matchPercentage >= 75 ? theme.colors.success : theme.colors.warning)
        }
    }
}

// MARK: - Collapsible Section

struct CollapsibleSectionView<Content: View>: View {
    let title: String
    let isExpanded: Bool
    let onTap: () -> Void
    @ViewBuilder let content: () -> Content
    @Environment(\.trueMatchTheme) var theme

    var body: some View {
        VStack(spacing: 0) {
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    onTap()
                }
            } label: {
                HStack {
                    Text(title)
                        .font(theme.typography.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Image(systemName: "chevron.right")
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                        .foregroundColor(.gray)
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
        .cornerRadius(theme.cornerRadii.sm)
    }
}

// MARK: - Empty State

struct EmptyJobStateView: View {
    let theme: TrueMatchTheme

    var body: some View {
        VStack(spacing: theme.spacing.lg) {
            Image(systemName: "briefcase.circle.fill")
                .font(.system(size: 64))
                .foregroundColor(theme.colors.primary)

            VStack(spacing: theme.spacing.sm) {
                Text("No More Jobs")
                    .font(theme.typography.headline)

                Text("Check back later for new job matches")
                    .font(theme.typography.body)
                    .foregroundColor(.gray)
            }

            Button {
                // Refresh action
            } label: {
                HStack {
                    Image(systemName: "arrow.clockwise")
                    Text("Refresh")
                }
                .padding(theme.spacing.sm)
                .background(theme.colors.primary)
                .foregroundColor(.white)
                .cornerRadius(theme.cornerRadii.md)
            }
        }
        .frame(maxHeight: .infinity)
        .multilineTextAlignment(.center)
    }
}

#Preview {
    CandidateJobRecommendationsView(candidateId: "preview-candidate")
        .environment(\.trueMatchTheme, TrueMatchTheme())
}
