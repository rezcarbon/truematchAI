//
//  RecruiterTabView.swift
//  TrueMatch
//
//  Tab navigation for recruiter mode with 5 tabs: Command Centre, Pipeline,
//  Search, Decisions, and Settings.
//

import SwiftUI

struct RecruiterTabView: View {
    @State var selectedTab: Int = 0
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        TabView(selection: $selectedTab) {
            // Command Centre
            RecruiterCommandCentreView()
                .tabItem {
                    Label("Command Centre", systemImage: "square.grid.2x2")
                }
                .tag(0)

            // Pipeline
            RecruiterPipelineView()
                .tabItem {
                    Label("Pipeline", systemImage: "rectangle.grid.1x2")
                }
                .tag(1)

            // Search
            RecruiterCandidateSearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
                .tag(2)

            // Decisions
            RecruiterDecisionView()
                .tabItem {
                    Label("Decisions", systemImage: "hand.thumbsup")
                }
                .tag(3)

            // Settings/Profile (placeholder)
            RecruiterSettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(4)
        }
        .tint(theme.colors.primary)
    }
}

// MARK: - Settings View (Placeholder)

private struct RecruiterSettingsView: View {
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        NavigationStack {
            List {
                Section("Recruiter Settings") {
                    HStack {
                        Text("Department")
                        Spacer()
                        Text("Engineering")
                            .foregroundStyle(.secondary)
                    }

                    HStack {
                        Text("Notifications")
                        Spacer()
                        Toggle("", isOn: .constant(true))
                    }

                    HStack {
                        Text("Auto-advance Pipeline")
                        Spacer()
                        Toggle("", isOn: .constant(false))
                    }
                }

                Section("About") {
                    HStack {
                        Text("App Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundStyle(.secondary)
                    }

                    Button(role: .destructive) {
                        // Logout action
                    } label: {
                        Label("Log Out", systemImage: "arrow.backward.circle")
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

// MARK: - Preview

#Preview {
    RecruiterTabView()
}
