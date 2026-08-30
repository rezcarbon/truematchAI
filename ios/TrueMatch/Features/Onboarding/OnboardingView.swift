//
//  OnboardingView.swift
//  TrueMatch
//

import SwiftUI

enum OnboardingScreen: Hashable {
    case home
    case login
    case signup
}

struct OnboardingView: View {
    @State private var navigationPath: [OnboardingScreen] = []

    var body: some View {
        NavigationStack(path: $navigationPath) {
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
                        navigationPath.append(OnboardingScreen.signup)
                    }) {
                        Text("Create account")
                            .frame(maxWidth: .infinity)
                            .frame(height: 50)
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(8)
                    }

                    Button(action: {
                        navigationPath.append(OnboardingScreen.login)
                    }) {
                        Text("Log in")
                            .frame(maxWidth: .infinity)
                            .frame(height: 50)
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
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.white.ignoresSafeArea())
            .navigationDestination(for: OnboardingScreen.self) { screen in
                switch screen {
                case .login:
                    LoginView(onBack: {
                        navigationPath.removeAll()
                    })
                case .signup:
                    SignUpView(onBack: {
                        navigationPath.removeAll()
                    })
                case .home:
                    EmptyView()
                }
            }
        }
    }
}

#Preview {
    OnboardingView()
}
