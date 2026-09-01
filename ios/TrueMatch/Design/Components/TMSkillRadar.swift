//
//  TMSkillRadar.swift
//  TrueMatch
//
//  Spider/radar chart for visualizing skill proficiency across multiple dimensions.
//  Used to compare candidate capabilities, job requirements, and skill progression.
//

import SwiftUI

// MARK: - Skill Dimension Model

struct SkillDimension: Identifiable, Equatable {
    let id: String
    let label: String
    let value: Double // 0–100
    let target: Double? = nil // Optional comparison value
    let category: SkillCategory = .technical

    enum SkillCategory {
        case technical
        case behavioral
        case domain
        case foundational

        func color(_ theme: TrueMatchTheme) -> Color {
            switch self {
            case .technical:
                return theme.colors.primary
            case .behavioral:
                return theme.colors.secondary
            case .domain:
                return theme.colors.accent
            case .foundational:
                return theme.colors.traditional
            }
        }
    }
}

// MARK: - TMSkillRadar

struct TMSkillRadar: View {
    let dimensions: [SkillDimension]
    var size: CGFloat = 240
    var showLegend: Bool = true
    var animationDuration: Double = 0.6
    var showGrid: Bool = true
    var gridLevels: Int = 5

    @Environment(\.trueMatchTheme) private var theme
    @State private var animationProgress: Double = 0

    private var sortedDimensions: [SkillDimension] {
        dimensions.sorted { $0.label < $1.label }
    }

    private var angleSlice: Double {
        guard !sortedDimensions.isEmpty else { return 0 }
        return (Double.pi * 2) / Double(sortedDimensions.count)
    }

    var body: some View {
        VStack(spacing: theme.spacing.sm) {
            // Radar Chart
            ZStack {
                // Grid
                if showGrid {
                    ForEach(1...gridLevels, id: \.self) { level in
                        let radius = (size / 2) * (Double(level) / Double(gridLevels))
                        Circle()
                            .stroke(
                                Color.gray.opacity(0.1),
                                style: StrokeStyle(lineWidth: TMComponentTokens.Radar.gridStrokeWidth)
                            )
                            .frame(width: radius * 2, height: radius * 2)
                    }

                    // Axes
                    ForEach(sortedDimensions.indices, id: \.self) { i in
                        let angle = angleSlice * Double(i) - .pi / 2
                        let endPoint = CGPoint(
                            x: cos(angle) * (size / 2),
                            y: sin(angle) * (size / 2)
                        )
                        Line(from: .zero, to: endPoint)
                            .stroke(
                                Color.gray.opacity(0.15),
                                style: StrokeStyle(lineWidth: TMComponentTokens.Radar.axisStrokeWidth)
                            )
                    }
                }

                // Target polygon (if any dimension has a target)
                if sortedDimensions.contains(where: { $0.target != nil }) {
                    radarPolygon(
                        values: sortedDimensions.map { $0.target ?? 0 },
                        color: theme.colors.capability.opacity(0.2),
                        fillOpacity: 0.1,
                        strokeWidth: 1.5
                    )
                }

                // Actual data polygon
                radarPolygon(
                    values: sortedDimensions.map { $0.value * animationProgress },
                    color: theme.colors.primary,
                    fillOpacity: 0.2,
                    strokeWidth: 2.5
                )

                // Data points
                ForEach(sortedDimensions.indices, id: \.self) { i in
                    let angle = angleSlice * Double(i) - .pi / 2
                    let fraction = (sortedDimensions[i].value * animationProgress) / 100
                    let radius = (size / 2) * fraction
                    let point = CGPoint(
                        x: cos(angle) * radius,
                        y: sin(angle) * radius
                    )

                    Circle()
                        .fill(theme.colors.primary)
                        .frame(width: TMComponentTokens.Radar.dataPointRadius * 2)
                        .position(point)
                }

                // Labels
                ForEach(sortedDimensions.indices, id: \.self) { i in
                    let angle = angleSlice * Double(i) - .pi / 2
                    let labelRadius = (size / 2) + 40
                    let labelPoint = CGPoint(
                        x: cos(angle) * labelRadius,
                        y: sin(angle) * labelRadius
                    )

                    VStack(spacing: 2) {
                        Text(sortedDimensions[i].label)
                            .font(theme.typography.chip)
                            .foregroundStyle(Color.tmTextPrimary)

                        Text("\(Int(sortedDimensions[i].value))")
                            .font(theme.typography.caption)
                            .foregroundStyle(Color.tmTextSecondary)
                            .monospacedDigit()
                    }
                    .position(labelPoint)
                }
            }
            .frame(width: size + 100, height: size + 100)

            // Legend
            if showLegend && !sortedDimensions.isEmpty {
                VStack(alignment: .leading, spacing: theme.spacing.xs) {
                    ForEach(sortedDimensions) { dimension in
                        HStack(spacing: theme.spacing.xs) {
                            Circle()
                                .fill(dimension.category.color(theme))
                                .frame(width: 8, height: 8)

                            Text(dimension.label)
                                .font(theme.typography.caption)
                                .foregroundStyle(Color.tmTextPrimary)

                            Spacer()

                            HStack(spacing: 4) {
                                Text("\(Int(dimension.value))")
                                    .font(theme.typography.chip)
                                    .foregroundStyle(Color.tmTextSecondary)
                                    .monospacedDigit()

                                if let target = dimension.target {
                                    Text("/ \(Int(target))")
                                        .font(theme.typography.chip)
                                        .foregroundStyle(Color.tmTextTertiary)
                                        .monospacedDigit()
                                }
                            }
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(theme.spacing.sm)
                .background(Color.gray.opacity(0.05))
                .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm))
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: animationDuration)) {
                animationProgress = 1.0
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Skill Radar Chart")
    }

    private func radarPolygon(
        values: [Double],
        color: Color,
        fillOpacity: Double,
        strokeWidth: CGFloat
    ) -> some View {
        Canvas { context in
            var path = Path()

            for (i, value) in values.enumerated() {
                let angle = angleSlice * Double(i) - .pi / 2
                let fraction = min(max(value / 100, 0), 1)
                let radius = (size / 2) * fraction
                let point = CGPoint(
                    x: cos(angle) * radius,
                    y: sin(angle) * radius
                )

                if i == 0 {
                    path.move(to: point)
                } else {
                    path.addLine(to: point)
                }
            }
            path.closeSubpath()

            var fillContext = context
            fillContext.fill(path, with: .color(color.opacity(fillOpacity)))

            context.stroke(
                path,
                with: .color(color),
                lineWidth: strokeWidth
            )
        }
    }
}

// MARK: - Helper Line View

struct Line: Shape {
    let from: CGPoint
    let to: CGPoint

    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: from)
        path.addLine(to: to)
        return path
    }
}

// MARK: - Preview

#Preview {
    let mockDimensions = [
        SkillDimension(id: "python", label: "Python", value: 85, target: 80, category: .technical),
        SkillDimension(id: "swift", label: "Swift", value: 72, target: 90, category: .technical),
        SkillDimension(id: "leadership", label: "Leadership", value: 78, category: .behavioral),
        SkillDimension(id: "communication", label: "Communication", value: 88, category: .behavioral),
        SkillDimension(id: "domain", label: "Domain Knowledge", value: 65, category: .domain),
        SkillDimension(id: "analytics", label: "Analytics", value: 92, category: .domain),
    ]

    VStack(spacing: 24) {
        Text("Skill Assessment")
            .font(.title2)
            .bold()

        TMSkillRadar(
            dimensions: mockDimensions,
            size: 220,
            showLegend: true
        )
    }
    .padding()
}
