//
//  CVAnalysisView.swift
//  TrueMatch
//
//  Candidate CV gap analysis: pick a resume + target role/seniority, run the
//  (multi-LLM-call) analysis, poll to completion, and render strengths, gaps,
//  improvement suggestions, and growth opportunities. Mirrors the web
//  /candidate/cv-analysis feature.
//

import SwiftUI

@MainActor
final class CVAnalysisViewModel: ObservableObject {
    @Published var resumes: [ResumeListItemDTO] = []
    @Published var selectedResumeId: String?
    @Published var targetRole = ""
    @Published var seniority = "senior"
    @Published var status = "idle"   // idle | pending | analyzing | completed | failed
    @Published var result: CVAnalysisResultDTO?
    @Published var errorMessage: String?

    private let api = APIClient.shared
    let seniorityLevels = ["junior", "mid", "senior", "lead"]

    var isRunning: Bool { status == "pending" || status == "analyzing" }
    var canRun: Bool {
        selectedResumeId != nil && targetRole.trimmingCharacters(in: .whitespaces).count >= 2 && !isRunning
    }

    func loadResumes() async {
        do {
            let resp = try await api.request(endpoint: .listResumes, type: ResumeListResponseDTO.self)
            resumes = resp.items
            if selectedResumeId == nil { selectedResumeId = resumes.first?.id }
        } catch {
            TrueMatchLogger.log(.error, "CV analysis: resume list failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    func run() async {
        guard let resumeId = selectedResumeId, canRun else { return }
        result = nil
        status = "pending"
        do {
            let start = try await api.request(
                endpoint: .startCVAnalysis(
                    CVAnalysisStartRequest(
                        resumeId: resumeId,
                        targetRole: targetRole.trimmingCharacters(in: .whitespaces),
                        targetSeniority: seniority
                    )
                ),
                type: CVAnalysisStartResponse.self
            )
            await poll(id: start.analysisId)
        } catch {
            status = "failed"
            errorMessage = error.localizedDescription
        }
    }

    private func poll(id: String) async {
        // The engine makes ~8 sequential LLM calls; allow several minutes.
        for _ in 0..<60 {
            if Task.isCancelled { return }
            do {
                let r = try await api.request(endpoint: .cvAnalysis(id: id), type: CVAnalysisResultDTO.self)
                status = r.status
                if r.status == "completed" {
                    result = r
                    return
                }
                if r.status == "failed" {
                    errorMessage = "Analysis failed. Please try again."
                    return
                }
            } catch {
                TrueMatchLogger.log(.warning, "CV analysis poll error: \(error)")
            }
            try? await Task.sleep(nanoseconds: 5_000_000_000)
        }
        if status != "completed" {
            status = "failed"
            errorMessage = "Timed out waiting for the analysis."
        }
    }
}

struct CVAnalysisView: View {
    @StateObject private var viewModel = CVAnalysisViewModel()

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
                Section("Target") {
                    TextField("Target role (e.g. Senior Backend Engineer)", text: $viewModel.targetRole)
                        .autocorrectionDisabled()
                    Picker("Seniority", selection: $viewModel.seniority) {
                        ForEach(viewModel.seniorityLevels, id: \.self) { Text($0.capitalized).tag($0) }
                    }
                    Button {
                        Task { await viewModel.run() }
                    } label: {
                        HStack {
                            if viewModel.isRunning { ProgressView().padding(.trailing, 4) }
                            Text(viewModel.isRunning ? "Analysing… (1–2 min)" : "Analyse my CV")
                        }
                    }
                    .disabled(!viewModel.canRun)
                }

                if let r = viewModel.result {
                    if let s = r.strengthSummary {
                        Section("Strengths") { Text(s).font(.subheadline) }
                    }
                    if let gaps = r.missingCapabilities, !gaps.isEmpty {
                        Section("Capability gaps") {
                            ForEach(gaps) { g in
                                VStack(alignment: .leading, spacing: 2) {
                                    HStack {
                                        Text(g.capability).font(.subheadline.weight(.semibold))
                                        Spacer()
                                        if let imp = g.importance {
                                            TMBadge(text: imp.capitalized,
                                                    kind: imp == "high" ? .error : imp == "medium" ? .warning : .neutral)
                                        }
                                    }
                                    if let how = g.howToImprove {
                                        Text(how).font(.caption).foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                    }
                    if let recs = r.improvementSuggestions, !recs.isEmpty {
                        Section("Improve your CV") {
                            ForEach(recs) { rec in
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(rec.suggestion).font(.subheadline)
                                    if let ex = rec.example {
                                        Text(ex).font(.caption).foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                    }
                    if let growth = r.growthOpportunities, !growth.isEmpty {
                        Section("Growth opportunities") {
                            ForEach(growth, id: \.self) { Text($0).font(.subheadline) }
                        }
                    }
                    if let traj = r.trajectoryAnalysis {
                        Section("Career trajectory") { Text(traj).font(.subheadline) }
                    }
                    if let jobs = r.topMatchingPositions, !jobs.isEmpty {
                        Section("Matching roles (\(r.totalMatchingJobs ?? jobs.count))") {
                            ForEach(jobs) { j in
                                HStack {
                                    Text(j.jobTitle).font(.subheadline)
                                    Spacer()
                                    Text("\(j.matchScore ?? 0)").font(.callout.weight(.bold))
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("CV Insights")
            .task { await viewModel.loadResumes() }
            .alert("Something went wrong",
                   isPresented: Binding(get: { viewModel.errorMessage != nil },
                                        set: { if !$0 { viewModel.errorMessage = nil } })) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: { Text(viewModel.errorMessage ?? "") }
        }
    }
}
