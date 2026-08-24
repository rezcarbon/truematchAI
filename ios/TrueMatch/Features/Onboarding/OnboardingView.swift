//
//  OnboardingView.swift
//  TrueMatch
//

import SwiftUI

struct OnboardingView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) private var theme
    @State private var showLogin = false {
        didSet {
            print("[DEBUG] showLogin changed: \(showLogin)")
        }
    }
    @State private var showSignUp = false {
        didSet {
            print("[DEBUG] showSignUp changed: \(showSignUp)")
        }
    }

    var body: some View {
        NavigationStack {
            if showLogin {
                LoginView(onBack: {
                    print("[DEBUG] LoginView onBack called")
                    showLogin = false
                })
            } else if showSignUp {
                SignUpView(onBack: {
                    print("[DEBUG] SignUpView onBack called")
                    showSignUp = false
                })
            } else {
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
                            Button(action: {
                                print("[DEBUG] Create account button tapped")
                                debugButtonTap("Create account")
                                showSignUp = true
                            }) {
                                Text("Create account")
                                    .font(.system(size: 17, weight: .semibold))
                                    .foregroundStyle(.white)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 56)
                                    .background(theme.colors.primary)
                                    .cornerRadius(theme.radii.sm)
                            }

                            Button(action: {
                                print("[DEBUG] Log in button tapped")
                                debugButtonTap("Log in")
                                showLogin = true
                            }) {
                                Text("Log in")
                                    .font(.system(size: 17, weight: .semibold))
                                    .foregroundStyle(theme.colors.primary)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 56)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: theme.radii.sm, style: .continuous)
                                            .stroke(theme.colors.primary, lineWidth: 2)
                                    )
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.horizontal, theme.spacing.lg)
                        .padding(.bottom, theme.spacing.xl)
                    }
                }
            }
        }
    }

    private func debugButtonTap(_ action: String) {
        print("[DEBUG] Button tapped: \(action)")
    }
}

#Preview {
    OnboardingView()
        .environmentObject(AppState())
}
