//
//  OnboardingView.swift
//  TrueMatch
//

import SwiftUI

struct OnboardingView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) private var theme
    @State private var showLogin = false
    @State private var showSignUp = false

    var body: some View {
        if showLogin {
            LoginView(onBack: { showLogin = false })
        } else if showSignUp {
            SignUpView(onBack: { showSignUp = false })
        } else {
            welcome
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
                Button(action: { showSignUp = true }) {
                    Text("Create account")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundStyle(.white)
                        .frame(height: 56)
                        .frame(maxWidth: .infinity)
                        .background(theme.colors.primary)
                        .cornerRadius(theme.radii.sm)
                }
                .buttonStyle(.plain)

                Button(action: { showLogin = true }) {
                    Text("Log in")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundStyle(theme.colors.primary)
                        .frame(height: 56)
                        .frame(maxWidth: .infinity)
                        .background(
                            RoundedRectangle(cornerRadius: theme.radii.sm, style: .continuous)
                                .stroke(theme.colors.primary, lineWidth: 2)
                        )
                }
                .buttonStyle(.plain)
                .contentShape(Rectangle())
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
