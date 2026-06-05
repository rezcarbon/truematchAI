//
//  SettingsView.swift
//  TrueMatch
//
//  Skeleton settings screen.
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) private var theme
    @StateObject private var auth = AuthStateManager()

    @State private var pushEnabled = true

    var body: some View {
        NavigationStack {
            Form {
                Section("Notifications") {
                    Toggle("Assessment-ready alerts", isOn: $pushEnabled)
                        .onChange(of: pushEnabled) { _, on in
                            if on {
                                Task { _ = await PushNotificationManager.shared.requestPermission() }
                            }
                        }
                }

                Section("About") {
                    LabeledContent("Version", value: appVersion)
                    LabeledContent("Environment", value: environmentName)
                }

                Section {
                    Button(role: .destructive) {
                        Task {
                            await auth.logout()
                            appState.signOut()
                        }
                    } label: {
                        Text("Sign out")
                    }
                }
            }
            .navigationTitle("Settings")
        }
    }

    private var appVersion: String {
        let v = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        let b = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
        return "\(v) (\(b))"
    }

    private var environmentName: String {
        #if DEBUG
        return "Staging"
        #else
        return "Production"
        #endif
    }
}

#Preview {
    SettingsView()
        .environmentObject(AppState())
}
