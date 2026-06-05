//
//  ResumeTextInput.swift
//  TrueMatch
//

import SwiftUI

/// Lets the candidate paste resume text directly instead of uploading a file.
struct ResumeTextInput: View {
    @Binding var text: String
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxs) {
            TMTextField(
                label: "Or paste your resume text",
                placeholder: "Paste the full text of your resume here...",
                text: $text,
                characterLimit: 20_000,
                isMultiLine: true,
                multiLineHeight: 200
            )
        }
    }
}

#Preview {
    ResumeTextInput(text: .constant(""))
        .padding()
}
