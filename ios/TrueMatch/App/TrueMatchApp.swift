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

// MARK: - Main Tab View

struct MainTabView: View {
    var body: some View {
        TabView {
            ResumeUploadView()
                .tabItem {
                    Label("Assess", systemImage: "doc.badge.plus")
                }

            HistoryView()
                .tabItem {
                    Label("History", systemImage: "clock.arrow.circlepath")
                }

            JobMatchingView()
                .tabItem {
                    Label("Positions", systemImage: "briefcase")
                }

            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.crop.circle")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
        .tint(TrueMatchTheme.accentColor)
    }
}
