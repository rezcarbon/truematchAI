//
//  OnboardingView.swift
//  TrueMatch
//

import SwiftUI

struct OnboardingView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        NavigationStack {
            welcome
                .navigationDestination(for: String.self) { destination in
                    switch destination {
                    case "signup":
                        SignUpView(onBack: {})
                    case "login":
                        LoginView(onBack: {})
                    default:
                        welcome
                    }
                }
        }
    }

    private var welcome: some View {
        VStack(spacing: theme.spacing.lg) {
            Spacer()

            Image(systemName: "person.text.rectangle")
                .font(.system(size: 72))
                .foregroundStyle(theme.colors.brandGradient)

            VStack(spacing: theme.spacing.xxs) {
                Text("TrueMatch")
                    .font(theme.typography.display)
                Text("See the candidate the keywords miss.")
                    .font(theme.typography.headline)
                    .foregroundStyle(Color.tmTextSecondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, theme.spacing.xl)

            Spacer()

            VStack(spacing: theme.spacing.xs) {
                NavigationLink(value: "signup") {
                    TMButton(title: "Create account", variant: .primary, size: .large, isFullWidth: true) {}
                }
                NavigationLink(value: "login") {
                    TMButton(title: "Log in", variant: .secondary, size: .large, isFullWidth: true) {}
                }
            }
            .padding(.horizontal, theme.spacing.lg)
            .padding(.bottom, theme.spacing.xl)
        }
        .background(TrueMatchTheme.Colors.backgroundAdaptive(for: .light))
    }
}

#Preview {
    OnboardingView()
        .environmentObject(AppState())
}
