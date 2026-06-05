//
//  TMCard.swift
//  TrueMatch
//

import SwiftUI

// MARK: - Card Style

enum TMCardStyle {
    case standard
    case elevated
    case interactive
}

// MARK: - TMCard

struct TMCard<Content: View>: View {
    let style: TMCardStyle
    let onTap: (() -> Void)?
    @ViewBuilder let content: Content

    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.colorScheme) private var colorScheme

    init(
        style: TMCardStyle = .standard,
        onTap: (() -> Void)? = nil,
        @ViewBuilder content: () -> Content
    ) {
        self.style = style
        self.onTap = onTap
        self.content = content()
    }

    var body: some View {
        Group {
            if let onTap, style == .interactive {
                interactiveCard(action: onTap)
            } else {
                staticCard
            }
        }
    }

    private var staticCard: some View {
        content
            .padding(theme.spacing.sm)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(TrueMatchTheme.Colors.surfaceAdaptive(for: colorScheme))
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.md, style: .continuous))
            .shadow(color: shadowColor, radius: shadowRadius, x: 0, y: shadowY)
    }

    private func interactiveCard(action: @escaping () -> Void) -> some View {
        Button(action: action) {
            content
                .padding(theme.spacing.sm)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(TrueMatchTheme.Colors.surfaceAdaptive(for: colorScheme))
                .clipShape(RoundedRectangle(cornerRadius: theme.radii.md, style: .continuous))
                .shadow(color: shadowColor, radius: shadowRadius, x: 0, y: shadowY)
        }
        .buttonStyle(CardPressStyle(animation: theme.animations.quick))
    }

    private var shadowColor: Color {
        switch style {
        case .standard: return Color.black.opacity(0.06)
        case .elevated: return Color.black.opacity(0.16)
        case .interactive: return Color.black.opacity(0.08)
        }
    }

    private var shadowRadius: CGFloat {
        switch style {
        case .standard: return 4
        case .elevated: return 14
        case .interactive: return 6
        }
    }

    private var shadowY: CGFloat {
        switch style {
        case .standard: return 2
        case .elevated: return 6
        case .interactive: return 3
        }
    }
}

private struct CardPressStyle: ButtonStyle {
    let animation: Animation

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.975 : 1.0)
            .animation(animation, value: configuration.isPressed)
    }
}

// MARK: - Card with Header

struct TMCardHeader<Trailing: View>: View {
    let title: String
    var subtitle: String? = nil
    @ViewBuilder var trailing: Trailing

    @Environment(\.trueMatchTheme) private var theme

    init(
        title: String,
        subtitle: String? = nil,
        @ViewBuilder trailing: () -> Trailing = { EmptyView() }
    ) {
        self.title = title
        self.subtitle = subtitle
        self.trailing = trailing()
    }

    var body: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(theme.typography.headline)
                    .foregroundStyle(Color.tmTextPrimary)

                if let subtitle {
                    Text(subtitle)
                        .font(theme.typography.caption)
                        .foregroundStyle(Color.tmTextSecondary)
                }
            }

            Spacer()
            trailing
        }
    }
}

// MARK: - Preview

#Preview("Card Variants") {
    ScrollView {
        VStack(spacing: 20) {
            TMCard {
                VStack(alignment: .leading, spacing: 8) {
                    TMCardHeader(title: "Standard Card", subtitle: "Basic card style")
                    Text("This is some body content for the card.")
                        .font(.system(size: 15))
                        .foregroundStyle(.secondary)
                }
            }

            TMCard(style: .elevated) {
                TMCardHeader(title: "Elevated Card") {
                    Image(systemName: "star.fill").foregroundStyle(.yellow)
                }
            }

            TMCard(style: .interactive, onTap: {}) {
                TMCardHeader(title: "Interactive Card", subtitle: "Tap me!")
            }
        }
        .padding()
    }
}
