//
//  ResumeUploadView.swift
//  TrueMatch
//

import SwiftUI

struct ResumeUploadView: View {
    @StateObject private var viewModel = ResumeUploadViewModel()
    @Environment(\.trueMatchTheme) private var theme
    @State private var showingPicker = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: theme.spacing.md) {
                    header

                    filePicker
                    ResumeTextInput(text: $viewModel.pastedResumeText)

                    Divider()

                    TMTextField(
                        label: "Job description",
                        placeholder: "Paste the job description to assess against...",
                        text: $viewModel.jobDescription,
                        characterLimit: 10_000,
                        isMultiLine: true,
                        multiLineHeight: 160
                    )

                    SupplementaryInfoView(text: $viewModel.supplementary)

                    submitArea
                }
                .padding(theme.spacing.lg)
            }
            .navigationTitle("New assessment")
            .navigationDestination(isPresented: submittedBinding) {
                if case .submitted(let id) = viewModel.phase {
                    AssessmentResultView(assessmentId: id)
                }
            }
            .sheet(isPresented: $showingPicker) {
                DocumentPicker { url in
                    viewModel.selectFile(url: url)
                }
                .ignoresSafeArea()
            }
        }
    }

    // MARK: - Sections

    private var header: some View {
        VStack(alignment: .leading, spacing: theme.spacing.xxs) {
            Text("Assess a candidate")
                .font(theme.typography.title)
            Text("Upload a resume and a job description. TrueMatch scores both keyword fit and demonstrated capability.")
                .font(theme.typography.body)
                .foregroundStyle(Color.tmTextSecondary)
        }
    }

    private var filePicker: some View {
        TMCard(style: .interactive, onTap: { showingPicker = true }) {
            HStack(spacing: theme.spacing.sm) {
                Image(systemName: viewModel.selectedFileName == nil ? "doc.badge.plus" : "doc.fill")
                    .font(.system(size: 28))
                    .foregroundStyle(theme.colors.primary)
                VStack(alignment: .leading, spacing: 2) {
                    Text(viewModel.selectedFileName ?? "Choose a resume file")
                        .font(theme.typography.headline)
                        .foregroundStyle(Color.tmTextPrimary)
                    Text("PDF, DOC, DOCX or TXT")
                        .font(theme.typography.caption)
                        .foregroundStyle(Color.tmTextSecondary)
                }
                Spacer()
                if viewModel.selectedFileName != nil {
                    Button {
                        viewModel.clearFile()
                    } label: {
                        Image(systemName: "xmark.circle.fill").foregroundStyle(Color.tmTextTertiary)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var submitArea: some View {
        switch viewModel.phase {
        case .uploading:
            TMInlineLoading(message: "Uploading resume...")
        case .creating:
            TMInlineLoading(message: "Creating assessment...")
        case .failed(let message):
            Text(message)
                .font(theme.typography.caption)
                .foregroundStyle(theme.colors.error)
        default:
            EmptyView()
        }

        TMButton(
            title: "Run assessment",
            icon: "sparkles",
            variant: .primary,
            size: .large,
            isLoading: isBusy,
            isFullWidth: true,
            isDisabled: !viewModel.canSubmit
        ) {
            Task { await viewModel.submit() }
        }
    }

    private var isBusy: Bool {
        switch viewModel.phase {
        case .uploading, .creating: return true
        default: return false
        }
    }

    private var submittedBinding: Binding<Bool> {
        Binding(
            get: { if case .submitted = viewModel.phase { return true } else { return false } },
            set: { _ in }
        )
    }
}

#Preview {
    ResumeUploadView()
}
