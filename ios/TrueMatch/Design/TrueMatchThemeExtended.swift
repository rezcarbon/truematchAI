//
//  TrueMatchThemeExtended.swift
//  TrueMatch
//
//  Extended theme with semantic colors, layout patterns, component tokens,
//  and advanced typography for complex data visualization and decision surfaces.
//

import SwiftUI

// MARK: - Extended Theme Components

extension TrueMatchTheme.Colors {

    // MARK: - Semantic Decision Colors

    /// Color for positive/recommended decisions
    var decisionPositive: Color { Color(hex: 0x38A169) }

    /// Color for negative/counter-recommended decisions
    var decisionNegative: Color { Color(hex: 0xE53E3E) }

    /// Color for neutral/uncertain decisions
    var decisionNeutral: Color { Color(hex: 0xA0AEC0) }

    /// Color for requiring attention/escalation
    var decisionEscalation: Color { Color(hex: 0xD69E2E) }

    // MARK: - Skill Assessment Colors

    /// Color for high proficiency/mastery (80-100%)
    var skillMastery: Color { Color(hex: 0x22863A) }

    /// Color for strong proficiency (60-79%)
    var skillStrong: Color { Color(hex: 0x38A169) }

    /// Color for moderate proficiency (40-59%)
    var skillModerate: Color { Color(hex: 0xD69E2E) }

    /// Color for developing proficiency (20-39%)
    var skillDeveloping: Color { Color(hex: 0xE2A76F) }

    /// Color for foundational proficiency (0-19%)
    var skillFoundational: Color { Color(hex: 0xE53E3E) }

    // MARK: - Gradient Sets

    /// Positive to neutral gradient (used for score progression)
    var gradientPositive: LinearGradient {
        LinearGradient(
            colors: [
                Color(hex: 0x38A169),
                Color(hex: 0x48BB78)
            ],
            startPoint: .leading,
            endPoint: .trailing
        )
    }

    /// Warning to negative gradient (used for risk indicators)
    var gradientWarning: LinearGradient {
        LinearGradient(
            colors: [
                Color(hex: 0xD69E2E),
                Color(hex: 0xE2A76F)
            ],
            startPoint: .leading,
            endPoint: .trailing
        )
    }

    /// Error gradient (used for critical issues)
    var gradientError: LinearGradient {
        LinearGradient(
            colors: [
                Color(hex: 0xE53E3E),
                Color(hex: 0xF56565)
            ],
            startPoint: .leading,
            endPoint: .trailing
        )
    }

    /// Skill spectrum (foundational → mastery)
    var gradientSkillSpectrum: LinearGradient {
        LinearGradient(
            colors: [
                Color(hex: 0xE53E3E),
                Color(hex: 0xE2A76F),
                Color(hex: 0xD69E2E),
                Color(hex: 0x38A169),
                Color(hex: 0x22863A)
            ],
            startPoint: .leading,
            endPoint: .trailing
        )
    }
}

// MARK: - Extended Typography

extension TrueMatchTheme.Typography {

    /// Extra-large display text (for major KPIs)
    var displayLarge: Font {
        .system(size: 48, weight: .bold, design: .rounded)
    }

    /// Monospaced variant for scores and metrics
    var monospacedMetric: Font {
        .system(size: 15, weight: .semibold, design: .monospaced)
    }

    /// Larger body text with relaxed line height
    var bodyLarge: Font {
        .system(size: 16, weight: .regular)
    }

    /// Small helper text (smaller than caption)
    var helper: Font {
        .system(size: 11, weight: .regular)
    }
}

// MARK: - Extended Spacing

extension TrueMatchTheme.Spacing {
    /// Micro spacing for inline elements
    let micro: CGFloat = 2
}

// MARK: - Layout Patterns

struct TMLayoutPattern {

    /// Standard card padding (sides + top/bottom)
    static let cardPadding: EdgeInsets = .init(top: 16, leading: 16, bottom: 16, trailing: 16)

    /// Standard modal/full-sheet padding
    static let modalPadding: EdgeInsets = .init(top: 24, leading: 20, bottom: 24, trailing: 20)

    /// Compact list item padding (used in queues, logs)
    static let compactListPadding: EdgeInsets = .init(top: 12, leading: 16, bottom: 12, trailing: 16)

    /// Dense grid item padding
    static let gridItemPadding: EdgeInsets = .init(top: 8, leading: 8, bottom: 8, trailing: 8)
}

// MARK: - Component Tokens

struct TMComponentTokens {

    // Radar Chart
    struct Radar {
        static let axisStrokeWidth: CGFloat = 1.2
        static let gridStrokeWidth: CGFloat = 0.8
        static let dataPointRadius: CGFloat = 4
        static let gridLevelCount: Int = 5
        static let animationDuration: Double = 0.6
    }

    // Decision Badge
    struct DecisionBadge {
        static let cornerRadius: CGFloat = 10
        static let padding: EdgeInsets = .init(top: 10, leading: 12, bottom: 10, trailing: 12)
        static let iconSize: CGFloat = 16
        static let minWidth: CGFloat = 120
    }

    // Score Gauge (Extended)
    struct Gauge {
        static let minSize: CGFloat = 100
        static let maxSize: CGFloat = 200
        static let defaultLineWidth: CGFloat = 14
        static let animationDelay: Double = 0.1
    }

    // Delta Bar (Extended)
    struct DeltaBar {
        static let markerAnimationDuration: Double = 0.5
        static let deltaHighlightAlpha: CGFloat = 0.3
    }
}

// MARK: - Rounded Rectangle Variants

extension TrueMatchTheme.CornerRadii {
    /// Extra-small (for tight UI)
    var xxs: CGFloat { 3 }

    /// Extra-large (for prominent surfaces)
    var xl: CGFloat { 24 }

    /// Pill-shaped (max roundness)
    var pill: CGFloat { 999 }
}

// MARK: - Shadow Variants

extension TrueMatchTheme.Shadows {

    /// Inset shadow (for embossed effect)
    func inset() -> (color: Color, radius: CGFloat, x: CGFloat, y: CGFloat) {
        (Color.black.opacity(0.15), 2, 0, -1)
    }

    /// Elevation shadow (for floating surfaces)
    func elevated() -> (color: Color, radius: CGFloat, x: CGFloat, y: CGFloat) {
        (Color.black.opacity(0.25), 20, 0, 12)
    }

    /// Soft focus shadow
    func softFocus() -> (color: Color, radius: CGFloat, x: CGFloat, y: CGFloat) {
        (Color.black.opacity(0.08), 12, 0, 6)
    }
}

// MARK: - Environment Key Extensions

extension EnvironmentValues {

    /// Access extended theme colors
    var tmColors: TrueMatchTheme.Colors {
        trueMatchTheme.colors
    }

    /// Access extended typography
    var tmTypography: TrueMatchTheme.Typography {
        trueMatchTheme.typography
    }

    /// Access layout patterns
    var tmLayout: TMLayoutPattern.Type {
        TMLayoutPattern.self
    }

    /// Access component tokens
    var tmTokens: TMComponentTokens.Type {
        TMComponentTokens.self
    }
}

// MARK: - Theme-aware View Modifiers

struct TMDecisionSurfaceModifier: ViewModifier {
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.colorScheme) private var colorScheme

    func body(content: Content) -> some View {
        let shadow = theme.shadows.elevated()
        content
            .padding(TMLayoutPattern.cardPadding)
            .background(TrueMatchTheme.Colors.surfaceAdaptive(for: colorScheme))
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.lg, style: .continuous))
            .shadow(color: shadow.color, radius: shadow.radius, x: shadow.x, y: shadow.y)
    }
}

struct TMDataVisualizationModifier: ViewModifier {
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.colorScheme) private var colorScheme

    func body(content: Content) -> some View {
        content
            .padding(theme.spacing.md)
            .background(TrueMatchTheme.Colors.surfaceAdaptive(for: colorScheme))
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.md, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: theme.radii.md, style: .continuous)
                    .strokeBorder(Color.gray.opacity(0.1), lineWidth: 1)
            )
    }
}

struct TMCompactListModifier: ViewModifier {
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.colorScheme) private var colorScheme

    func body(content: Content) -> some View {
        content
            .padding(TMLayoutPattern.compactListPadding)
            .background(TrueMatchTheme.Colors.surfaceAdaptive(for: colorScheme))
            .overlay(
                Divider().padding(.leading, TMLayoutPattern.compactListPadding.leading),
                alignment: .bottom
            )
    }
}

// MARK: - View Extensions

extension View {

    /// Apply decision surface styling (elevated, prominent)
    func tmDecisionSurface() -> some View {
        modifier(TMDecisionSurfaceModifier())
    }

    /// Apply data visualization styling
    func tmDataVisualization() -> some View {
        modifier(TMDataVisualizationModifier())
    }

    /// Apply compact list item styling
    func tmCompactList() -> some View {
        modifier(TMCompactListModifier())
    }

    /// Apply theme-aware monospaced styling for metrics
    func tmMonospacedMetric(_ theme: TrueMatchTheme) -> some View {
        self.font(theme.typography.monospacedMetric)
            .lineLimit(1)
            .monospacedDigit()
    }
}
