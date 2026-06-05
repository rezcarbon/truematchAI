//
//  LoadingView.swift
//  TrueMatch
//

import SwiftUI

// MARK: - Full-screen Loading Overlay

struct TMLoadingOverlay: View {
    var message: String = "Assessing..."

    @State private var isPulsing = false
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()

            VStack(spacing: theme.spacing.sm) {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.system(size: 48))
                    .foregroundStyle(theme.colors.primary)
                    .scaleEffect(isPulsing ? 1.12 : 0.92)
                    .animation(
                        .easeInOut(duration: 0.9).repeatForever(autoreverses: true),
                        value: isPulsing
                    )

                Text(message)
                    .font(theme.typography.headline)
                    .foregroundStyle(Color.tmTextPrimary)

                ProgressView()
                    .tint(theme.colors.primary)
            }
            .padding(theme.spacing.xl)
            .background(.ultraThinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.lg, style: .continuous))
        }
        .onAppear { isPulsing = true }
    }
}

// MARK: - Inline Loading

struct TMInlineLoading: View {
    var message: String = "Loading..."

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        HStack(spacing: theme.spacing.xxs) {
            ProgressView()
                .controlSize(.small)
                .tint(theme.colors.primary)

            Text(message)
                .font(theme.typography.caption)
                .foregroundStyle(Color.tmTextSecondary)
        }
    }
}

// MARK: - Skeleton Loading (Shimmer)

struct TMSkeletonView: View {
    var lineCount: Int = 3
    var lineHeight: CGFloat = 14

    @State private var isShimmering = false
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxs) {
            ForEach(0..<lineCount, id: \.self) { index in
                RoundedRectangle(cornerRadius: theme.radii.xs)
                    .fill(Color.gray.opacity(0.15))
                    .frame(
                        maxWidth: index == lineCount - 1 ? 180 : .infinity,
                        maxHeight: lineHeight
                    )
                    .overlay(shimmerOverlay)
            }
        }
        .onAppear { isShimmering = true }
    }

    private var shimmerOverlay: some View {
        GeometryReader { geo in
            let width = geo.size.width
            RoundedRectangle(cornerRadius: theme.radii.xs)
                .fill(
                    LinearGradient(
                        colors: [.clear, Color.white.opacity(0.35), .clear],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(width: width * 0.4)
                .offset(x: isShimmering ? width : -width * 0.4)
                .animation(
                    .linear(duration: 1.3).repeatForever(autoreverses: false),
                    value: isShimmering
                )
        }
        .clipped()
    }
}

// MARK: - Progress Loading (Determinate)

struct TMProgressLoading: View {
    let progress: Double // 0.0 ... 1.0
    var message: String? = nil

    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(spacing: theme.spacing.xxs) {
            if let message {
                HStack {
                    Text(message)
                        .font(theme.typography.caption)
                        .foregroundStyle(Color.tmTextSecondary)

                    Spacer()

                    Text("\(Int(progress * 100))%")
                        .font(theme.typography.chip)
                        .foregroundStyle(theme.colors.primary)
                        .monospacedDigit()
                }
            }

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: theme.radii.full)
                        .fill(Color.gray.opacity(0.15))
                        .frame(height: 8)

                    RoundedRectangle(cornerRadius: theme.radii.full)
                        .fill(theme.colors.primary)
                        .frame(width: geo.size.width * min(max(progress, 0), 1), height: 8)
                        .animation(theme.animations.standard, value: progress)
                }
            }
            .frame(height: 8)
        }
    }
}

// MARK: - Legacy alias

typealias LoadingView = TMLoadingOverlay

// MARK: - Previews

#Preview("Loading states") {
    VStack(spacing: 32) {
        TMInlineLoading(message: "Fetching assessment...")
        TMSkeletonView(lineCount: 4).padding()
        TMProgressLoading(progress: 0.65, message: "Analyzing capability").padding()
    }
    .padding()
}
