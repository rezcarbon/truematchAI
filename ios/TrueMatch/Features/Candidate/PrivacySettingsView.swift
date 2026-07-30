//
//  PrivacySettingsView.swift
//  TrueMatch
//
//  Privacy settings view with 3 stealth mode levels: Hidden, Passive, Active.
//

import SwiftUI

struct PrivacySettingsView: View {
    @State private var privacyLevel: String = "passive"
    @State private var currentEmployer: String = "Your Company"
    @State private var blockedCompanies: [String] = []
    @State private var isLoading = false
    @State private var errorMessage: String?

    let privacyLevels = [
        ("hidden", "🔐", "Hidden", "Your profile is never shared. No recruiter spam."),
        ("passive", "👁️", "Passive", "Only exceptional matches see your profile."),
        ("active", "🟢", "Active", "Open to matches. Your profile is visible to all recruiters.")
    ]

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 8) {
                            Text("🔒")
                                .font(.title2)
                            Text("100% Stealth Mode")
                                .font(.headline)
                        }
                        Text("Control your visibility to recruiters")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(8)

                // Privacy Level Selection
                VStack(alignment: .leading, spacing: 12) {
                    Text("YOUR PRIVACY LEVEL")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.secondary)

                    ForEach(privacyLevels, id: \.0) { level, icon, label, description in
                        PrivacyLevelButton(
                            level: level,
                            icon: icon,
                            label: label,
                            description: description,
                            isSelected: privacyLevel == level,
                            action: {
                                withAnimation {
                                    privacyLevel = level
                                }
                            }
                        )
                    }
                }
                .padding()

                Divider()
                    .padding(.horizontal)

                // Protected Info
                VStack(alignment: .leading, spacing: 12) {
                    Text("🛡️ AUTOMATICALLY PROTECTED")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.secondary)

                    VStack(spacing: 8) {
                        HStack {
                            Text("Current employer blocked")
                                .font(.subheadline)
                            Spacer()
                            Text(currentEmployer)
                                .font(.caption)
                                .fontDesign(.monospaced)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color(.systemBackground))
                                .cornerRadius(4)
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(8)

                        if !blockedCompanies.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Blocked companies:")
                                    .font(.caption)
                                    .foregroundColor(.secondary)

                                FlowLayout(spacing: 8) {
                                    ForEach(blockedCompanies, id: \.self) { company in
                                        Text(company)
                                            .font(.caption)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background(Color.blue.opacity(0.1))
                                            .foregroundColor(.blue)
                                            .cornerRadius(4)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding()

                Divider()
                    .padding(.horizontal)

                // Privacy Guarantee
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 8) {
                        Text("✔️")
                            .font(.title3)
                        Text("Privacy Guaranteed")
                            .fontWeight(.semibold)
                    }
                    Text("Your profile, preferences, and career context are never shared with companies until you explicitly approve a match.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding()
                .background(Color.blue.opacity(0.05))
                .cornerRadius(8)

                if let error = errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.red)
                        .padding()
                }

                Spacer()
            }
            .padding()
        }
        .navigationTitle("Privacy Settings")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct PrivacyLevelButton: View {
    let level: String
    let icon: String
    let label: String
    let description: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Text(icon)
                    .font(.title3)

                VStack(alignment: .leading, spacing: 4) {
                    Text(label)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    Text(description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.blue)
                }
            }
            .padding()
            .background(isSelected ? Color.blue.opacity(0.1) : Color(.systemGray6))
            .cornerRadius(8)
            .foregroundColor(.primary)
        }
    }
}

struct FlowLayout: View {
    let spacing: CGFloat
    let content: [String]

    init(spacing: CGFloat = 8, _ content: [String] = []) {
        self.spacing = spacing
        self.content = content
    }

    var body: some View {
        VStack(alignment: .leading, spacing: spacing) {
            // Placeholder - will be replaced with actual flow layout
            HStack(spacing: spacing) {
                ForEach(content, id: \.self) { item in
                    Text(item)
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        PrivacySettingsView()
    }
}
