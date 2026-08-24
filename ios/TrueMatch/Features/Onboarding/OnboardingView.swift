//
//  OnboardingView.swift
//  TrueMatch
//

import SwiftUI

enum OnboardingScreen {
    case home
    case login
    case signup
}

struct OnboardingView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) private var theme
    @State private var currentScreen: OnboardingScreen = .home

    var body: some View {
        NavigationStack {
            Group {
                switch currentScreen {
                case .login:
                    LoginView(onBack: {
                        print("[DEBUG] LoginView onBack called")
                        currentScreen = .home
                    })
                case .signup:
                    SignUpView(onBack: {
                        print("[DEBUG] SignUpView onBack called")
                        currentScreen = .home
                    })
                case .home:
                    ZStack {
                        TrueMatchTheme.Colors.backgroundAdaptive(for: .light)
                            .ignoresSafeArea()

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
                                Button("Create account") {
                                    print("[DEBUG] Create account button tapped")
                                    currentScreen = .signup
                                }
                                .font(.system(size: 17, weight: .semibold))
                                .foregroundStyle(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .background(theme.colors.primary)
                                .cornerRadius(theme.radii.sm)

                                Button("Log in") {
                                    print("[DEBUG] Log in button tapped")
                                    currentScreen = .login
                                }
                                .font(.system(size: 17, weight: .semibold))
                                .foregroundStyle(theme.colors.primary)
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .overlay(
                                    RoundedRectangle(cornerRadius: theme.radii.sm, style: .continuous)
                                        .stroke(theme.colors.primary, lineWidth: 2)
                                )
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.horizontal, theme.spacing.lg)
                            .padding(.bottom, theme.spacing.xl)
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    OnboardingView()
        .environmentObject(AppState())
}
