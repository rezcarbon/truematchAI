//
//  LoginView.swift
//  TrueMatch
//

import SwiftUI

struct LoginView: View {
    var onBack: () -> Void = {}

    @EnvironmentObject var appState: AppState
    @Environment(\.trueMatchTheme) private var theme
    @StateObject private var auth = AuthStateManager()

    @State private var email = ""
    @State private var password = ""

    private var canSubmit: Bool {
        email.isValidEmail && !password.isBlank
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: theme.spacing.md) {
                Text("Welcome back")
                    .font(theme.typography.title)

                TMTextField(label: "Email", placeholder: "you@example.com", text: $email)
                TMTextField(label: "Password", placeholder: "Your password", text: $password, isSecure: true)

                if let error = auth.error {
                    Text(error).font(theme.typography.caption).foregroundStyle(theme.colors.error)
                }

                TMButton(title: "Log in", variant: .primary, size: .large,
                         isLoading: auth.isLoading, isFullWidth: true, isDisabled: !canSubmit) {
                    Task {
                        await auth.login(email: email, password: password)
                        if auth.isAuthenticated { appState.completeAuthentication() }
                    }
                }

                Divider().padding(.vertical, theme.spacing.xxs)

                TMButton(title: "Log in with Singpass", variant: .secondary, size: .large, isFullWidth: true) {
                    SingpassAuthManager.shared.startAuthentication()
                }
            }
            .padding(theme.spacing.lg)
        }
        .navigationTitle("Log in")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("Back", action: onBack)
            }
        }
        .onChange(of: SingpassAuthManager.shared.didCompleteAuthentication) { _, done in
            if done { appState.completeAuthentication() }
        }
    }
}

#Preview {
    NavigationStack { LoginView() }
        .environmentObject(AppState())
}
