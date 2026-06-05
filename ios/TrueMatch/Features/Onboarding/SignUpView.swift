//
//  SignUpView.swift
//  TrueMatch
//

import SwiftUI

struct SignUpView: View {
    var onBack: () -> Void = {}

    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) private var theme
    @StateObject private var auth = AuthStateManager()

    @State private var displayName = ""
    @State private var email = ""
    @State private var password = ""

    private var canSubmit: Bool {
        email.isValidEmail && password.count >= 8
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: theme.spacing.md) {
                Text("Create your account")
                    .font(theme.typography.title)

                TMTextField(label: "Name", placeholder: "Your name", text: $displayName)
                TMTextField(label: "Email", placeholder: "you@example.com", text: $email,
                            errorMessage: email.isBlank || email.isValidEmail ? nil : "Enter a valid email")
                TMTextField(label: "Password", placeholder: "At least 8 characters", text: $password, isSecure: true)

                if let error = auth.error {
                    Text(error).font(theme.typography.caption).foregroundStyle(theme.colors.error)
                }

                TMButton(title: "Create account", variant: .primary, size: .large,
                         isLoading: auth.isLoading, isFullWidth: true, isDisabled: !canSubmit) {
                    Task {
                        await auth.signUp(email: email, password: password, displayName: displayName.isBlank ? nil : displayName)
                        if auth.isAuthenticated { appState.completeAuthentication() }
                    }
                }

                Divider().padding(.vertical, theme.spacing.xxs)

                TMButton(title: "Sign up with Singpass", variant: .secondary, size: .large, isFullWidth: true) {
                    SingpassAuthManager.shared.startAuthentication()
                }
            }
            .padding(theme.spacing.lg)
        }
        .navigationTitle("Sign up")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("Back", action: onBack)
            }
        }
    }
}

#Preview {
    NavigationStack { SignUpView() }
        .environmentObject(AppState())
}
