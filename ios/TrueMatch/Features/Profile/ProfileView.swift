//
//  ProfileView.swift
//  TrueMatch
//
//  Skeleton profile screen.
//

import SwiftUI

struct ProfileView: View {
    @Environment(\.trueMatchTheme) private var theme
    @State private var profile: UserProfileResponse = PreviewData.sampleProfile

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: theme.spacing.md) {
                    Image(systemName: "person.crop.circle.fill")
                        .font(.system(size: 72))
                        .foregroundStyle(theme.colors.brandGradient)

                    Text(profile.displayName)
                        .font(theme.typography.title)

                    TMCard {
                        VStack(alignment: .leading, spacing: theme.spacing.xs) {
                            infoRow("Email", profile.email ?? "—")
                            Divider()
                            infoRow("Verified ID", profile.maskedNric ?? "Not linked")
                        }
                    }
                }
                .padding(theme.spacing.lg)
            }
            .navigationTitle("Profile")
            .task { await load() }
        }
    }

    private func infoRow(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label)
                .font(theme.typography.caption)
                .foregroundStyle(Color.tmTextSecondary)
            Spacer()
            Text(value)
                .font(theme.typography.body)
                .foregroundStyle(Color.tmTextPrimary)
        }
    }

    private func load() async {
        do {
            profile = try await APIClient.shared.request(endpoint: .profile, type: UserProfileResponse.self)
        } catch {
            TrueMatchLogger.log(.warning, "Falling back to preview profile: \(error.localizedDescription)")
        }
    }
}

#Preview {
    ProfileView()
}
