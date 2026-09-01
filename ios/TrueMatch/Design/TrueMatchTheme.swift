//
//  TrueMatchTheme.swift
//  TrueMatch
//

import SwiftUI

// MARK: - Theme

struct TrueMatchTheme: Sendable {

    // MARK: - Colours

    struct Colors: Sendable {
        // Brand
        let primary = Color(hex: 0x4C51BF)      // indigo
        let secondary = Color(hex: 0x319795)    // teal
        let accent = Color(hex: 0xD69E2E)       // amber

        // Status
        let success = Color(hex: 0x38A169)
        let warning = Color(hex: 0xD69E2E)
        let error = Color(hex: 0xE53E3E)
        let info = Color(hex: 0x3182CE)

        // Score semantics
        let traditional = Color(hex: 0x718096)  // muted grey — the "old" score
        let capability = Color(hex: 0x4C51BF)    // brand — the embodied score
        let deltaPositive = Color(hex: 0x38A169)
        let deltaNegative = Color(hex: 0xE53E3E)

        // Governance status colours (DISPLAY-ONLY — mapped from backend status strings)
        let governancePass = Color(hex: 0x38A169)
        let governanceWatch = Color(hex: 0xD69E2E)
        let governanceFail = Color(hex: 0xE53E3E)

        // Brand gradient (primary -> secondary)
        var brandGradient: LinearGradient {
            LinearGradient(
                colors: [Color(hex: 0x4C51BF), Color(hex: 0x319795)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        }
    }

    // MARK: - Typography

    struct Typography: Sendable {
        let display: Font
        let title: Font
        let headline: Font
        let body: Font
        let caption: Font
        let chip: Font

        init(scale: CGFloat = 1.0) {
            func s(_ size: CGFloat) -> CGFloat { (size * scale).rounded() }
            display = .system(size: s(34), weight: .bold, design: .rounded)
            title = .system(size: s(22), weight: .bold)
            headline = .system(size: s(17), weight: .semibold)
            body = .system(size: s(15))
            caption = .system(size: s(13))
            chip = .system(size: s(12), weight: .medium)
        }
    }

    // MARK: - Spacing

    struct Spacing: Sendable {
        let xxxs: CGFloat = 4
        let xxs: CGFloat = 8
        let xs: CGFloat = 12
        let sm: CGFloat = 16
        let md: CGFloat = 20
        let lg: CGFloat = 24
        let xl: CGFloat = 32
        let xxl: CGFloat = 48
    }

    // MARK: - Corner Radii

    struct CornerRadii: Sendable {
        let xs: CGFloat = 6
        let sm: CGFloat = 10
        let md: CGFloat = 14
        let lg: CGFloat = 20
        let full: CGFloat = 999
    }

    // MARK: - Shadows

    struct Shadows: Sendable {
        func subtle() -> (color: Color, radius: CGFloat, x: CGFloat, y: CGFloat) {
            (Color.black.opacity(0.06), 4, 0, 2)
        }

        func medium() -> (color: Color, radius: CGFloat, x: CGFloat, y: CGFloat) {
            (Color.black.opacity(0.12), 8, 0, 4)
        }

        func strong() -> (color: Color, radius: CGFloat, x: CGFloat, y: CGFloat) {
            (Color.black.opacity(0.20), 16, 0, 8)
        }
    }

    // MARK: - Animation

    struct Animations: Sendable {
        let standard: Animation = .spring(response: 0.35, dampingFraction: 0.8)
        let quick: Animation = .spring(response: 0.2, dampingFraction: 0.85)
        let slow: Animation = .spring(response: 0.55, dampingFraction: 0.75)
    }

    // Instances
    let colors = Colors()
    let typography: Typography
    let spacing = Spacing()
    let radii = CornerRadii()
    let shadows = Shadows()
    let animations = Animations()

    /// Active text-size multiplier (drives `Typography`). 1.0 = standard.
    let textScale: CGFloat

    init(textScale: CGFloat = 1.0) {
        self.textScale = textScale
        self.typography = Typography(scale: textScale)
    }

    // MARK: - Static Convenience Accessors

    static let accentColor = Color(hex: 0x4C51BF)
    static let secondaryColor = Color(hex: 0x319795)
    static let brandAccent = Color(hex: 0xD69E2E)

    static let cornerRadiusMD: CGFloat = 14
    static let shadowLight = Color.black.opacity(0.06)
}

// MARK: - TMButtonStyle

struct TMButtonStyle: ButtonStyle {
    var tint: Color = TrueMatchTheme.accentColor

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 17, weight: .semibold))
            .foregroundStyle(.white)
            .padding(.vertical, 14)
            .padding(.horizontal, 24)
            .background(tint)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
            .opacity(configuration.isPressed ? 0.85 : 1.0)
            .animation(.spring(response: 0.2, dampingFraction: 0.85), value: configuration.isPressed)
    }
}

// MARK: - Environment Key

private struct TrueMatchThemeKey: EnvironmentKey {
    static let defaultValue = TrueMatchTheme()
}

extension EnvironmentValues {
    var trueMatchTheme: TrueMatchTheme {
        get { self[TrueMatchThemeKey.self] }
        set { self[TrueMatchThemeKey.self] = newValue }
    }
}

// MARK: - Colour Helpers

extension Color {
    init(hex: UInt, opacity: Double = 1.0) {
        self.init(
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: opacity
        )
    }
}

// MARK: - Programmatic Adaptive Colours

extension TrueMatchTheme.Colors {
    static func backgroundAdaptive(for scheme: ColorScheme) -> Color {
        scheme == .dark ? Color(hex: 0x0F1117) : Color(hex: 0xFAFBFC)
    }

    static func surfaceAdaptive(for scheme: ColorScheme) -> Color {
        scheme == .dark ? Color(hex: 0x1A1D2E) : .white
    }

    static func textPrimaryAdaptive(for scheme: ColorScheme) -> Color {
        scheme == .dark ? .white : Color(hex: 0x1A202C)
    }

    static func textSecondaryAdaptive(for scheme: ColorScheme) -> Color {
        scheme == .dark ? Color.white.opacity(0.7) : Color(hex: 0x4A5568)
    }

    static func textTertiaryAdaptive(for scheme: ColorScheme) -> Color {
        scheme == .dark ? Color.white.opacity(0.45) : Color(hex: 0xA0AEC0)
    }
}

// MARK: - Adaptive Color Shorthands

extension Color {
    static var tmBackground: Color { TrueMatchTheme.Colors.backgroundAdaptive(for: .light) }
    static var tmSurface: Color { TrueMatchTheme.Colors.surfaceAdaptive(for: .light) }
    static var tmTextPrimary: Color { Color.primary }
    static var tmTextSecondary: Color { Color.secondary }
    static var tmTextTertiary: Color { Color.secondary.opacity(0.6) }
}

// MARK: - View Modifiers

struct TMCardModifier: ViewModifier {
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.colorScheme) private var colorScheme

    func body(content: Content) -> some View {
        let shadow = theme.shadows.subtle()
        content
            .padding(theme.spacing.sm)
            .background(TrueMatchTheme.Colors.surfaceAdaptive(for: colorScheme))
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.md, style: .continuous))
            .shadow(color: shadow.color, radius: shadow.radius, x: shadow.x, y: shadow.y)
    }
}

struct TMSectionHeaderModifier: ViewModifier {
    @Environment(\.trueMatchTheme) private var theme

    func body(content: Content) -> some View {
        content
            .font(theme.typography.title)
            .foregroundStyle(Color.tmTextPrimary)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.bottom, theme.spacing.xxs)
    }
}

extension View {
    func tmCard() -> some View {
        modifier(TMCardModifier())
    }

    func tmSectionHeader() -> some View {
        modifier(TMSectionHeaderModifier())
    }
}
