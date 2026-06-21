//
//  TrueMatchApp.swift
//  TrueMatch
//

import SwiftUI
import SwiftData

@main
struct TrueMatchApp: App {
    @StateObject private var appState = AppState()
    @StateObject private var deepLinkHandler = DeepLinkHandler.shared
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            CachedAssessment.self,
            CachedProfile.self,
            ResumeCache.self,
            OfflineAction.self,
        ])
        let modelConfiguration = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false
        )
        do {
            return try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
                .environmentObject(deepLinkHandler)
                .environment(\.trueMatchTheme, TrueMatchTheme())
                .modelContainer(sharedModelContainer)
                .onOpenURL { url in
                    deepLinkHandler.handle(url: url)
                }
        }
    }
}

// MARK: - Root View

struct RootView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        Group {
            switch appState.authState {
            case .authenticated:
                MainTabView()
            case .onboarding:
                OnboardingView()
            case .unauthenticated:
                OnboardingView()
            }
        }
        .animation(.easeInOut, value: appState.authState)
    }
}

// MARK: - Main Tab View (role-aware)

struct MainTabView: View {
    /// Role from the access-token JWT — drives which workspace the user sees.
    private var role: String { SessionManager.shared.role ?? "candidate" }

    var body: some View {
        Group {
            switch role {
            case "recruiter": RecruiterTabs()
            case "admin": AdminTabs()
            default: CandidateTabs()
            }
        }
        .tint(TrueMatchTheme.accentColor)
    }
}

private struct CandidateTabs: View {
    var body: some View {
        TabView {
            ResumeUploadView().tabItem { Label("Assess", systemImage: "doc.badge.plus") }
            ChatView().tabItem { Label("Assistant", systemImage: "sparkles") }
            CVAnalysisView().tabItem { Label("CV Insights", systemImage: "chart.line.uptrend.xyaxis") }
            PositionsListView().tabItem { Label("Jobs", systemImage: "briefcase") }
            MoreHubView(title: "More", items: [
                .init(label: "Capability Translation", icon: "sparkles.rectangle.stack", destination: AnyView(CapabilityTranslationView())),
                .init(label: "Transition Pathways", icon: "arrow.up.right.circle", destination: AnyView(TransitionPathwaysView())),
                .init(label: "Assessment History", icon: "clock.arrow.circlepath", destination: AnyView(HistoryView())),
                .init(label: "Photo Resume Upload", icon: "camera", destination: AnyView(PhotoResumeUploadView())),
                .init(label: "Profile", icon: "person.crop.circle", destination: AnyView(ProfileView())),
                .init(label: "Settings", icon: "gearshape", destination: AnyView(SettingsView())),
            ]).tabItem { Label("More", systemImage: "ellipsis.circle") }
        }
    }
}

private struct RecruiterTabs: View {
    var body: some View {
        TabView {
            ReviewsView().tabItem { Label("Reviews", systemImage: "doc.text.magnifyingglass") }
            ChatView().tabItem { Label("Assistant", systemImage: "sparkles") }
            PositionsListView().tabItem { Label("Positions", systemImage: "briefcase") }
            RecruiterDashboardView().tabItem { Label("Dashboard", systemImage: "chart.bar") }
            MoreHubView(title: "More", items: [
                .init(label: "JD Simulation", icon: "wand.and.stars", destination: AnyView(JDSimulationView())),
                .init(label: "Decisions", icon: "checkmark.seal", destination: AnyView(DecisionsView())),
                .init(label: "Agent Control", icon: "cpu", destination: AnyView(AgentDashboardView())),
                .init(label: "Profile", icon: "person.crop.circle", destination: AnyView(ProfileView())),
                .init(label: "Settings", icon: "gearshape", destination: AnyView(SettingsView())),
            ]).tabItem { Label("More", systemImage: "ellipsis.circle") }
        }
    }
}

private struct AdminTabs: View {
    var body: some View {
        TabView {
            AdminDashboardView().tabItem { Label("Admin", systemImage: "gauge") }
            ChatView().tabItem { Label("Assistant", systemImage: "sparkles") }
            GovernanceReviewsView().tabItem { Label("Governance", systemImage: "checkmark.shield") }
            ComplianceView().tabItem { Label("Compliance", systemImage: "doc.badge.gearshape") }
            MoreHubView(title: "More", items: [
                .init(label: "Users", icon: "person.3", destination: AnyView(AdminUsersView())),
                .init(label: "Audit Trail", icon: "list.bullet.rectangle.portrait", destination: AnyView(AdminAuditView())),
                .init(label: "Analytics", icon: "chart.pie", destination: AnyView(AdminAnalyticsView())),
                .init(label: "Agent Control", icon: "cpu", destination: AnyView(AgentDashboardView())),
                .init(label: "Profile", icon: "person.crop.circle", destination: AnyView(ProfileView())),
                .init(label: "Settings", icon: "gearshape", destination: AnyView(SettingsView())),
            ]).tabItem { Label("More", systemImage: "ellipsis.circle") }
        }
    }
}

/// A simple hub that lists secondary features as navigation links.
struct MoreHubItem: Identifiable {
    let id = UUID()
    let label: String
    let icon: String
    let destination: AnyView
}

struct MoreHubView: View {
    let title: String
    let items: [MoreHubItem]
    var body: some View {
        NavigationStack {
            List(items) { item in
                NavigationLink(destination: item.destination) {
                    Label(item.label, systemImage: item.icon)
                }
            }
            .navigationTitle(title)
        }
    }
}
