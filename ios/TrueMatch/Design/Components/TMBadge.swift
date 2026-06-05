//
//  TMBadge.swift
//  TrueMatch
//
//  Small pill used for status, governance state, and counter-recommendation
//  flags. Governance badges are DISPLAY-ONLY: the colour is mapped from the
//  status string the backend returns — the client computes no thresholds.
//

import SwiftUI

enum TMBadgeKind {
    case neutral
    case success
    case warning
    case error
    case info

    func color(_ theme: TrueMatchTheme) -> Color {
        switch self {
        case .neutral: return theme.colors.traditional
        case .success: return theme.colors.success
        case .warning: return theme.colors.warning
        case .error: return theme.colors.error
        case .info: return theme.colors.info
        }
    }
}

struct TMBadge: View {
    let text: String
    var kind: TMBadgeKind = .neutral
    var icon: String? = nil

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        HStack(spacing: 4) {
            if let icon {
                Image(systemName: icon)
                    .font(.system(size: 10, weight: .bold))
            }
            Text(text)
                .font(theme.typography.chip)
        }
        .foregroundStyle(kind.color(theme))
        .padding(.horizontal, theme.spacing.xs)
        .padding(.vertical, theme.spacing.xxxs)
        .background(
            Capsule().fill(kind.color(theme).opacity(0.12))
        )
        .overlay(
            Capsule().strokeBorder(kind.color(theme).opacity(0.3), lineWidth: 1)
        )
    }
}

extension TMBadge {
    /// Maps a backend governance status string to a badge. The mapping is purely
    /// presentational — no thresholds or scoring logic live on the client.
    static func governance(status: String) -> TMBadge {
        switch status.lowercased() {
        case "pass", "ok", "coherent", "consistent", "high":
            return TMBadge(text: status.capitalized, kind: .success, icon: "checkmark.seal")
        case "watch", "warn", "partial", "medium":
            return TMBadge(text: status.capitalized, kind: .warning, icon: "exclamationmark.triangle")
        case "fail", "low", "incoherent", "inconsistent":
            return TMBadge(text: status.capitalized, kind: .error, icon: "xmark.octagon")
        default:
            return TMBadge(text: status.capitalized, kind: .neutral)
        }
    }
}

#Preview {
    VStack(alignment: .leading, spacing: 12) {
        TMBadge(text: "Completed", kind: .success, icon: "checkmark")
        TMBadge(text: "Processing", kind: .info)
        TMBadge(text: "Counter-recommended", kind: .warning, icon: "arrow.uturn.up")
        TMBadge.governance(status: "pass")
        TMBadge.governance(status: "watch")
        TMBadge.governance(status: "fail")
    }
    .padding()
}
