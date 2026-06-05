//
//  SupplementaryInfoView.swift
//  TrueMatch
//

import SwiftUI

/// Optional free-text field for context the resume does not capture
/// (e.g. career gaps, side projects, motivations).
struct SupplementaryInfoView: View {
    @Binding var text: String
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxs) {
            TMTextField(
                label: "Supplementary information (optional)",
                placeholder: "Anything the resume doesn't capture — context, motivations, gaps...",
                text: $text,
                characterLimit: 2_000,
                isMultiLine: true,
                multiLineHeight: 120
            )
            Text("This helps the assessment see capability beyond keywords.")
                .font(theme.typography.chip)
                .foregroundStyle(Color.tmTextTertiary)
        }
    }
}

#Preview {
    SupplementaryInfoView(text: .constant(""))
        .padding()
}
