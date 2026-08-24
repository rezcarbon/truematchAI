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

@MainActor
final class OnboardingFlowState: ObservableObject {
    @Published var currentScreen: OnboardingScreen = .home

    func goToLogin() {
        currentScreen = .login
    }

    func goToSignUp() {
        currentScreen = .signup
    }

    func goHome() {
        currentScreen = .home
    }
}

struct OnboardingView: View {
    @StateObject private var flowState = OnboardingFlowState()

    var body: some View {
        if flowState.currentScreen == .login {
            LoginView(onBack: {
                flowState.goHome()
            })
        } else if flowState.currentScreen == .signup {
            SignUpView(onBack: {
                flowState.goHome()
            })
        } else {
            ZStack {
                Color.white.ignoresSafeArea()

                VStack(spacing: 40) {
                    Spacer()

                    VStack(spacing: 16) {
                        Image(systemName: "person.text.rectangle")
                            .font(.system(size: 64))
                            .foregroundStyle(.blue)

                        VStack(spacing: 8) {
                            Text("TrueMatch")
                                .font(.system(size: 40, weight: .bold))
                            Text("See the candidate the keywords miss.")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundStyle(.gray)
                                .multilineTextAlignment(.center)
                        }
                    }

                    Spacer()

                    VStack(spacing: 12) {
                        Button(action: {
                            flowState.goToSignUp()
                        }) {
                            Text("Create account")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(8)
                        }

                        Button(action: {
                            flowState.goToLogin()
                        }) {
                            Text("Log in")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.clear)
                                .foregroundColor(.blue)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color.blue, lineWidth: 1)
                                )
                        }
                    }
                    .padding()
                }
                .padding()
            }
        }
    }
}

#Preview {
    OnboardingView()
}
