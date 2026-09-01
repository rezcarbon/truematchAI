//
//  TMTextField.swift
//  TrueMatch
//

import SwiftUI

struct TMTextField: View {
    let label: String
    let placeholder: String
    @Binding var text: String

    var errorMessage: String? = nil
    var characterLimit: Int? = nil
    var isMultiLine: Bool = false
    var multiLineHeight: CGFloat = 120
    var isSecure: Bool = false

    @FocusState private var isFocused: Bool
    @Environment(\.trueMatchTheme) private var theme
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxxs) {
            Text(label)
                .font(theme.typography.caption)
                .foregroundStyle(Color.tmTextSecondary)

            ZStack(alignment: .topTrailing) {
                if isMultiLine {
                    multiLineField
                } else {
                    singleLineField
                }

                if !text.isEmpty && isFocused && !isSecure {
                    Button {
                        text = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(Color.tmTextTertiary)
                            .font(.system(size: 16))
                    }
                    .padding(isMultiLine ? 10 : 0)
                    .padding(.trailing, isMultiLine ? 0 : 12)
                }
            }

            HStack {
                if let errorMessage, !errorMessage.isEmpty {
                    Text(errorMessage)
                        .font(theme.typography.chip)
                        .foregroundStyle(theme.colors.error)
                }

                Spacer()

                if let characterLimit {
                    Text("\(text.count)/\(characterLimit)")
                        .font(theme.typography.chip)
                        .foregroundStyle(
                            text.count > characterLimit
                                ? theme.colors.error
                                : Color.tmTextTertiary
                        )
                }
            }
        }
    }

    // MARK: - Single-line

    @ViewBuilder
    private var singleLineField: some View {
        Group {
            if isSecure {
                SecureField(placeholder, text: $text)
            } else {
                TextField(placeholder, text: $text)
            }
        }
        .font(theme.typography.body)
        .focused($isFocused)
        .padding(.horizontal, theme.spacing.xs)
        .frame(height: 48)
        .background(fieldBackground)
        .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm, style: .continuous))
        .overlay(fieldBorder)
        .onChange(of: text) { _, newValue in
            if let characterLimit, newValue.count > characterLimit {
                text = String(newValue.prefix(characterLimit))
            }
        }
    }

    // MARK: - Multi-line

    private var multiLineField: some View {
        TextEditor(text: $text)
            .font(theme.typography.body)
            .focused($isFocused)
            .scrollContentBackground(.hidden)
            .padding(theme.spacing.xxs)
            .frame(minHeight: multiLineHeight)
            .background(fieldBackground)
            .clipShape(RoundedRectangle(cornerRadius: theme.radii.sm, style: .continuous))
            .overlay(fieldBorder)
            .onChange(of: text) { _, newValue in
                if let characterLimit, newValue.count > characterLimit {
                    text = String(newValue.prefix(characterLimit))
                }
            }
    }

    // MARK: - Shared Styling

    private var hasError: Bool {
        errorMessage != nil && !(errorMessage?.isEmpty ?? true)
    }

    private var fieldBackground: Color {
        TrueMatchTheme.Colors.surfaceAdaptive(for: colorScheme)
    }

    private var fieldBorder: some View {
        RoundedRectangle(cornerRadius: theme.radii.sm, style: .continuous)
            .strokeBorder(borderColor, lineWidth: isFocused || hasError ? 1.5 : 1)
    }

    private var borderColor: Color {
        if hasError { return theme.colors.error }
        if isFocused { return theme.colors.primary }
        return Color.tmTextTertiary.opacity(0.3)
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 24) {
        TMTextField(label: "Email", placeholder: "you@example.com", text: .constant(""))
        TMTextField(label: "Password", placeholder: "••••••••", text: .constant("secret"), isSecure: true)
        TMTextField(
            label: "Supplementary info",
            placeholder: "Add context the resume doesn't capture...",
            text: .constant("Led a migration of..."),
            characterLimit: 2000,
            isMultiLine: true
        )
    }
    .padding()
}
