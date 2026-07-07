//
//  TMDecisionBadge.swift
//  TrueMatch
//
//  Prominent badge component for displaying hiring/matching decisions with
//  semantic meaning, confidence levels, and action indicators.
//

import SwiftUI

// MARK: - Decision Type

enum TMDecision: Equatable, Sendable {
    case recommended(confidence: Double) // 0–100
    case counterRecommended(reason: String = "")
    case pending
    case escalated(priority: EscalationPriority = .medium)
    case neutral(reason: String = "")

    enum EscalationPriority {
        case low
        case medium
        case high
        case critical

        func color(_ theme: TrueMatchTheme) -> Color {
            switch self {
            case .low:
                return theme.colors.info
            case .medium:
                return theme.colors.warning
            case .high:
                return theme.colors.error.opacity(0.8)
            case .critical:
                return theme.colors.error
            }
        }

        var icon: String {
            switch self {
            case .low:
                return "exclamationmark.circle"
            case .medium:
                return "exclamationmark.triangle"
            case .high:
                return "exclamationmark.octagon"
            case .critical:
                return "xmark.octagon.fill"
            }
        }
    }

    var backgroundColor: (color: Color, opacity: Double) {
        switch self {
        case .recommended(let confidence):
            let baseOpacity = 0.12 + (confidence / 100) * 0.08
            return (Color(hex: 0x38A169), baseOpacity)

        case .counterRecommended:
            return (Color(hex: 0xE53E3E), 0.15)

        case .pending:
            return (Color(hex: 0x718096), 0.1)

        case .escalated(let priority):
            return (priority.color(.init()), 0.12)

        case .neutral:
            return (Color(hex: 0xA0AEC0), 0.08)
        }
    }

    var foregroundColor: Color {
        switch self {
        case .recommended:
            return Color(hex: 0x22863A)

        case .counterRecommended:
            return Color(hex: 0xC53030)

        case .pending:
            return Color(hex: 0x4A5568)

        case .escalated(let priority):
            return priority.color(.init())

        case .neutral:
            return Color(hex: 0x718096)
        }
    }

    var icon: String {
        switch self {
        case .recommended:
            return "checkmark.circle.fill"

        case .counterRecommended:
            return "xmark.circle.fill"

        case .pending:
            return "hourglass"

        case .escalated(let priority):
            return priority.icon

        case .neutral:
            return "circle.dotted"
        }
    }

    var label: String {
        switch self {
        case .recommended(let confidence):
            if confidence >= 95 {
                return "Strongly Recommended"
            } else if confidence >= 80 {
                return "Recommended"
            } else if confidence >= 60 {
                return "Likely Match"
            } else {
                return "Potential Match"
            }

        case .counterRecommended:
            return "Counter-Recommended"

        case .pending:
            return "Under Review"

        case .escalated:
            return "Escalated"

        case .neutral:
            return "Neutral Match"
        }
    }

    var confidenceValue: Double? {
        switch self {
        case .recommended(let confidence):
            return confidence
        default:
            return nil
        }
    }
}

// MARK: - TMDecisionBadge

struct TMDecisionBadge: View {
    let decision: TMDecision
    var size: TMDecisionBadgeSize = .regular
    var showConfidence: Bool = true
    var showIcon: Bool = true
    var actionLabel: String? = nil
    var onAction: (() -> Void)? = nil

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .center, spacing: theme.spacing.xs) {
            HStack(spacing: theme.spacing.xs) {
                if showIcon {
                    Image(systemName: decision.icon)
                        .font(.system(size: size.iconSize, weight: .semibold))
                        .foregroundStyle(decision.foregroundColor)
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text(decision.label)
                        .font(size.labelFont(theme))
                        .fontWeight(.semibold)
                        .foregroundStyle(decision.foregroundColor)

                    if showConfidence, let confidence = decision.confidenceValue {
                        HStack(spacing: 4) {
                            Text("Confidence:")
                                .font(theme.typography.chip)
                                .foregroundStyle(Color.tmTextTertiary)

                            Text("\(Int(confidence))%")
                                .font(theme.typography.chip)
                                .foregroundStyle(decision.foregroundColor)
                                .monospacedDigit()
                        }
                    } else if case .counterRecommended(let reason) = decision, !reason.isEmpty {
                        Text(reason)
                            .font(theme.typography.chip)
                            .foregroundStyle(Color.tmTextSecondary)
                            .lineLimit(2)
                    } else if case .neutral(let reason) = decision, !reason.isEmpty {
                        Text(reason)
                            .font(theme.typography.chip)
                            .foregroundStyle(Color.tmTextSecondary)
                            .lineLimit(2)
                    }
                }

                Spacer()

                if case .recommended(let confidence) = decision, showConfidence {
                    ConfidenceIndicator(confidence: confidence)
                }
            }
            .padding(TMComponentTokens.DecisionBadge.padding)

            if let actionLabel, let onAction {
                Divider()
                    .padding(.horizontal, TMComponentTokens.DecisionBadge.padding.leading)

                Button(action: onAction) {
                    Text(actionLabel)
                        .font(theme.typography.chip)
                        .foregroundStyle(decision.foregroundColor)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, theme.spacing.xs)
                }
                .padding(TMComponentTokens.DecisionBadge.padding)
            }
        }
        .frame(minWidth: TMComponentTokens.DecisionBadge.minWidth)
        .background(decision.backgroundColor.color.opacity(decision.backgroundColor.opacity))
        .clipShape(RoundedRectangle(cornerRadius: TMComponentTokens.DecisionBadge.cornerRadius, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: TMComponentTokens.DecisionBadge.cornerRadius, style: .continuous)
                .strokeBorder(decision.foregroundColor.opacity(0.2), lineWidth: 1)
        )
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Decision: \(decision.label)")
        .accessibilityValue(
            decision.confidenceValue.map { "Confidence \(Int($0))%" } ?? ""
        )
    }
}

// MARK: - Confidence Indicator

struct ConfidenceIndicator: View {
    let confidence: Double
    var size: CGFloat = 48

    @Environment(\.trueMatchTheme) private var theme

    private var confidenceColor: Color {
        switch confidence {
        case 90...:
            return theme.colors.success
        case 75...:
            return theme.colors.warning
        default:
            return theme.colors.info
        }
    }

    var body: some View {
        ZStack {
            Circle()
                .fill(confidenceColor.opacity(0.1))

            Circle()
                .trim(from: 0, to: confidence / 100)
                .stroke(
                    confidenceColor,
                    style: StrokeStyle(lineWidth: 2, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))

            VStack(spacing: 0) {
                Text("\(Int(confidence))")
                    .font(.system(size: 11, weight: .bold, design: .rounded))
                    .foregroundStyle(confidenceColor)
                Text("%")
                    .font(.system(size: 8, weight: .semibold))
                    .foregroundStyle(confidenceColor.opacity(0.7))
            }
        }
        .frame(width: size, height: size)
    }
}

// MARK: - Size Variants

enum TMDecisionBadgeSize {
    case compact
    case regular
    case large

    func labelFont(_ theme: TrueMatchTheme) -> Font {
        switch self {
        case .compact:
            return theme.typography.caption
        case .regular:
            return theme.typography.headline
        case .large:
            return theme.typography.title
        }
    }

    var iconSize: CGFloat {
        switch self {
        case .compact:
            return 12
        case .regular:
            return 16
        case .large:
            return 24
        }
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 16) {
        TMDecisionBadge(
            decision: .recommended(confidence: 92),
            showConfidence: true
        )

        TMDecisionBadge(
            decision: .recommended(confidence: 72),
            showConfidence: true
        )

        TMDecisionBadge(
            decision: .counterRecommended(reason: "Skill mismatch in Python"),
            actionLabel: "View Analysis",
            onAction: {}
        )

        TMDecisionBadge(
            decision: .escalated(priority: .high),
            actionLabel: "Escalate",
            onAction: {}
        )

        TMDecisionBadge(
            decision: .neutral(reason: "Insufficient information"),
            size: .compact
        )

        TMDecisionBadge(
            decision: .pending,
            size: .large
        )
    }
    .padding()
}
