//
//  CandidateTabView.swift
//  TrueMatch
//
//  Tab navigation structure for candidate-specific features:
//  1. Assessment Results
//  2. Job Recommendations
//  3. Career Coach
//  4. Application Tracking
//

import SwiftUI

struct CandidateTabView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) var theme

    private var candidateId: String {
        SessionManager.shared.userId ?? "candidate"
    }

    var body: some View {
        TabView {
            // Assessment Results Tab
            CandidateAssessmentResultsView(candidateId: candidateId)
                .tabItem {
                    Label("Assessment", systemImage: "chart.line.uptrend.xyaxis")
                }

            // Job Recommendations Tab
            CandidateJobRecommendationsView(candidateId: candidateId)
                .tabItem {
                    Label("Jobs", systemImage: "briefcase.fill")
                }

            // Career Coach Tab
            CandidateCareerCoachView(candidateId: candidateId)
                .tabItem {
                    Label("Coach", systemImage: "sparkles")
                }

            // Application Tracking Tab
            CandidateApplicationTrackingView(candidateId: candidateId)
                .tabItem {
                    Label("Applications", systemImage: "checkmark.circle.fill")
                }
        }
        .tint(theme.colors.primary)
    }
}

#Preview {
    CandidateTabView()
        .environmentObject(AppState())
        .environment(\.trueMatchTheme, TrueMatchTheme())
}
