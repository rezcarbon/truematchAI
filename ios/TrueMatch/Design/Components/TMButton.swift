//
//  TMButton.swift
//  TrueMatch
//

import SwiftUI

// MARK: - Button Variant & Size

enum TMButtonVariant {
    case primary
    case secondary
    case ghost
    case destructive
}

enum TMButtonSize {
    case large      // 56pt
    case medium     // 44pt
    case compact    // 36pt

    var height: CGFloat {
        switch self {
        case .large: return 56
        case .medium: return 44
        case .compact: return 36
        }
    }

    var horizontalPadding: CGFloat {
        switch self {
        case .large: return 28
        case .medium: return 20
        case .compact: return 14
        }
    }

    var font: Font {
        switch self {
        case .large: return .system(size: 17, weight: .semibold)
        case .medium: return .system(size: 15, weight: .semibold)
        case .compact: return .system(size: 13, weight: .medium)
        }
    }
}

// MARK: - TMButton

struct TMButton: View {
    let title: String
    var icon: String? = nil
    var variant: TMButtonVariant = .primary
    var size: TMButtonSize = .medium
    var isLoading: Bool = false
    var isFullWidth: Bool = false
    var isDisabled: Bool = false
    let action: () -> Void

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        Button(action: action) {
            HStack(spacing: theme.spacing.xxs) {
                if isLoading {
                    ProgressView()
                        .tint(foregroundColor)
                        .controlSize(size == .compact ? .mini : .small)
                } else {
                    if let icon {
                        Image(systemName: icon)
                            .font(size.font)
                    }
                    Text(title)
                        .font(size.font)
                }
            }
            .foregroundStyle(foregroundColor)
            .frame(height: size.height)
            .frame(maxWidth: isFullWidth ? .infinity : nil)
            .padding(.horizontal, size.horizontalPadding)
            .background(backgroundView)
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm, style: .continuous))
            .overlay(overlayBorder)
        }
        .buttonStyle(TMPressStyle(animation: theme.animations.quick))
        .disabled(isLoading || isDisabled)
        .opacity(isDisabled ? 0.45 : 1.0)
        .frame(minWidth: 44, minHeight: 44) // Accessibility touch target
    }

    // MARK: - Variant Styling

    private var foregroundColor: Color {
        switch variant {
        case .primary: return .white
        case .secondary: return theme.colors.primary
        case .ghost: return theme.colors.primary
        case .destructive: return .white
        }
    }

    @ViewBuilder
    private var backgroundView: some View {
        switch variant {
        case .primary: theme.colors.primary
        case .secondary: Color.clear
        case .ghost: Color.clear
        case .destructive: theme.colors.error
        }
    }

    @ViewBuilder
    private var overlayBorder: some View {
        if variant == .secondary {
            RoundedRectangle(cornerRadius: theme.radii.sm, style: .continuous)
                .strokeBorder(theme.colors.primary, lineWidth: 1.5)
        }
    }
}

// MARK: - Press Button Style

private struct TMPressStyle: ButtonStyle {
    let animation: Animation

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
            .opacity(configuration.isPressed ? 0.85 : 1.0)
            .animation(animation, value: configuration.isPressed)
    }
}

// MARK: - Preview

#Preview("All Variants") {
    VStack(spacing: 16) {
        TMButton(title: "Primary Large", variant: .primary, size: .large, isFullWidth: true) {}
        TMButton(title: "Secondary", icon: "arrow.right", variant: .secondary) {}
        TMButton(title: "Ghost", variant: .ghost, size: .compact) {}
        TMButton(title: "Destructive", variant: .destructive) {}
        TMButton(title: "Loading...", variant: .primary, isLoading: true, isFullWidth: true) {}
        TMButton(title: "Disabled", isDisabled: true) {}
    }
    .padding()
}
