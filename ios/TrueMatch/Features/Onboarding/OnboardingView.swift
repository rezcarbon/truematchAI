//
//  OnboardingView.swift
//  TrueMatch
//

import SwiftUI

struct OnboardingView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) private var theme

    @State private var route: Route = .welcome

    enum Route {
        case welcome
        case signUp
        case login
    }

    var body: some View {
        NavigationStack {
            switch route {
            case .welcome:
                welcome
            case .signUp:
                SignUpView(onBack: { route = .welcome })
            case .login:
                LoginView(onBack: { route = .welcome })
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
                TMButton(title: "Create account", variant: .primary, size: .large, isFullWidth: true) {
                    route = .signUp
                }
                TMButton(title: "Log in", variant: .secondary, size: .large, isFullWidth: true) {
                    route = .login
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
