//
//  CapabilityTranslationView.swift
//  TrueMatch
//
//  Candidate Capability Translation: pick a resume + paste a target JD, run the
//  grounded ATS rewrite, poll to completion, and show the measured before→after
//  keyword + semantic lift with per-bullet grounding. Every line is traceable to
//  the candidate's real experience — nothing is fabricated. Mirrors the web
//  /candidate/capability-translation feature.
//

import SwiftUI

@MainActor
final class CapabilityTranslationViewModel: ObservableObject {
    @Published var resumes: [ResumeListItemDTO] = []
    @Published var selectedResumeId: String?
    @Published var targetRole = ""
    @Published var jdText = ""
    @Published var status = "idle"   // idle | pending | translating | completed | failed
    @Published var result: CapabilityTranslationResultDTO?
    @Published var errorMessage: String?

    private let api = APIClient.shared

    var isRunning: Bool { status == "pending" || status == "translating" }
    var canRun: Bool {
        selectedResumeId != nil
            && jdText.trimmingCharacters(in: .whitespacesAndNewlines).count >= 20
            && !isRunning
    }

    func loadResumes() async {
        do {
            let resp = try await api.request(endpoint: .listResumes, type: ResumeListResponseDTO.self)
            resumes = resp.items
            if selectedResumeId == nil { selectedResumeId = resumes.first?.id }
        } catch {
            TrueMatchLogger.log(.error, "Translation: resume list failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    func run() async {
        guard let resumeId = selectedResumeId, canRun else { return }
        result = nil
        status = "pending"
        do {
            let role = targetRole.trimmingCharacters(in: .whitespaces)
            let start = try await api.request(
                endpoint: .startCapabilityTranslation(
                    CapabilityTranslationStartRequest(
                        resumeId: resumeId,
                        jdText: jdText.trimmingCharacters(in: .whitespacesAndNewlines),
                        targetRole: role.isEmpty ? nil : role
                    )
                ),
                type: CapabilityTranslationStartResponse.self
            )
            await poll(id: start.translationId)
        } catch {
            status = "failed"
            errorMessage = error.localizedDescription
        }
    }

    private func poll(id: String) async {
        for _ in 0..<60 {
            if Task.isCancelled { return }
            do {
                let r = try await api.request(
                    endpoint: .capabilityTranslation(id: id),
                    type: CapabilityTranslationResultDTO.self
                )
                status = r.status
                if r.status == "completed" {
                    result = r
                    return
                }
                if r.status == "failed" {
                    errorMessage = r.error ?? "Translation failed. Please try again."
                    return
                }
            } catch {
                TrueMatchLogger.log(.warning, "Translation poll error: \(error)")
            }
            try? await Task.sleep(nanoseconds: 4_000_000_000)
        }
        if status != "completed" {
            status = "failed"
            errorMessage = "Timed out waiting for the translation."
        }
    }
}

struct CapabilityTranslationView: View {
    @Environment(\.trueMatchTheme) private var theme
    @StateObject private var viewModel = CapabilityTranslationViewModel()

    var body: some View {
        NavigationStack {
            Form {
                Section("Your resume") {
                    if viewModel.resumes.isEmpty {
                        NavigationLink(destination: PhotoResumeUploadView(onUploaded: {
                            Task { await viewModel.loadResumes() }
                        })) {
                            Label("No resumes yet — snap a photo", systemImage: "camera")
                        }
                    } else {
                        Picker("Resume", selection: $viewModel.selectedResumeId) {
                            ForEach(viewModel.resumes) { r in
                                Text(r.filename ?? "Resume \(String(r.id.prefix(8)))")
                                    .tag(Optional(r.id))
                            }
                        }
                    }
                }

                Section("Target role") {
                    TextField("Role title (optional)", text: $viewModel.targetRole)
                        .autocorrectionDisabled()
                    TextField("Paste the full job description…", text: $viewModel.jdText, axis: .vertical)
                        .lineLimit(4...10)
                    Button {
                        Task { await viewModel.run() }
                    } label: {
                        HStack {
                            if viewModel.isRunning { ProgressView().padding(.trailing, 4) }
                            Image(systemName: "sparkles")
                            Text(viewModel.isRunning ? "Translating… (1–2 min)" : "Translate my capability")
                        }
                    }
                    .disabled(!viewModel.canRun)
                }

                if let r = viewModel.result {
                    resultSections(r)
                }
            }
            .navigationTitle("Capability Translation")
            .task { await viewModel.loadResumes() }
            .alert("Something went wrong",
                   isPresented: Binding(get: { viewModel.errorMessage != nil },
                                        set: { if !$0 { viewModel.errorMessage = nil } })) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: { Text(viewModel.errorMessage ?? "") }
        }
    }

    @ViewBuilder
    private func resultSections(_ r: CapabilityTranslationResultDTO) -> some View {
        Section("What this role sees vs. what you can do") {
            ThreeSignalGapView(
                beforeKeyword: r.beforeKeywordScore ?? 0,
                afterKeyword: r.afterKeywordScore ?? 0,
                beforeSemantic: r.beforeSemanticScore ?? 0,
                afterSemantic: r.afterSemanticScore ?? 0,
                capability: r.capabilityScore
            )
            .padding(.vertical, 6)
        }

        if let summary = r.summary, !summary.isEmpty {
            Section("Rewritten summary") { Text(summary).font(.subheadline) }
        }

        if let skills = r.skills, !skills.isEmpty {
            Section("Skills (evidence-backed)") {
                Text(skills.joined(separator: " · ")).font(.subheadline)
            }
        }

        if let bullets = r.bullets, !bullets.isEmpty {
            Section("Experience — each line traced to your resume") {
                ForEach(bullets) { b in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(b.text).font(.subheadline)
                        HStack(spacing: 6) {
                            TMBadge(text: b.evidenceStrength,
                                    kind: b.evidenceStrength == "HIGH" ? .success
                                        : b.evidenceStrength == "WEAK" ? .warning : .neutral)
                            Text("grounded in: \(b.grounding)")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 2)
                }
            }
        }

        if (r.translationNotes?.isEmpty == false)
            || (r.droppedUngrounded ?? 0) > 0
            || (r.stillMissingKeywords?.isEmpty == false) {
            Section("What we did NOT add (we never fabricate)") {
                if let notes = r.translationNotes, !notes.isEmpty {
                    Text(notes).font(.caption)
                }
                if let dropped = r.droppedUngrounded, dropped > 0 {
                    Text("\(dropped) suggested line(s) dropped — unsupported by your resume.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                if let missing = r.stillMissingKeywords, !missing.isEmpty {
                    Text("Still not matched: \(missing.joined(separator: ", "))")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
        }
    }
}
