//
//  OnboardingFlowState.swift
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
    @Published var currentScreen: OnboardingScreen = .home {
        didSet {
            print("[DEBUG] currentScreen changed from \(oldValue) to \(currentScreen)")
        }
    }

    func goToLogin() {
        print("[DEBUG] goToLogin called, current: \(currentScreen)")
        currentScreen = .login
        print("[DEBUG] goToLogin completed, current is now: \(currentScreen)")
    }

    func goToSignUp() {
        print("[DEBUG] goToSignUp called, current: \(currentScreen)")
        currentScreen = .signup
        print("[DEBUG] goToSignUp completed, current is now: \(currentScreen)")
    }

    func goHome() {
        print("[DEBUG] goHome called, current: \(currentScreen)")
        currentScreen = .home
        print("[DEBUG] goHome completed, current is now: \(currentScreen)")
    }
}
