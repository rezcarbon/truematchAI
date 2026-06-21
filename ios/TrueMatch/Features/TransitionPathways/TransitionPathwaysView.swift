import SwiftUI

@MainActor
final class TransitionPathwaysViewModel: ObservableObject {
    @Published var resumes: [ResumeListItemDTO] = []
    @Published var selectedResumeId: String?
    @Published var currentRole = ""
    @Published var target = ""
    @Published var status = "idle"   // idle | analyzing | completed | failed
    @Published var result: TransitionResultDTO?
    @Published var errorMessage: String?
    @Published var tracking = false
    @Published var trajectory: [TrajectoryPointDTO] = []

    private let api = APIClient.shared

    var isRunning: Bool { status == "pending" || status == "analyzing" }
    var canRun: Bool { selectedResumeId != nil && !isRunning }

    func loadResumes() async {
        do {
            let resp = try await api.request(endpoint: .listResumes, type: ResumeListResponseDTO.self)
            resumes = resp.items
            if selectedResumeId == nil { selectedResumeId = resumes.first?.id }
        } catch {
            TrueMatchLogger.log(.error, "Transition: resume list failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    func run() async {
        guard let resumeId = selectedResumeId, canRun else { return }
        result = nil
        status = "analyzing"
        do {
            let role = currentRole.trimmingCharacters(in: .whitespaces)
            let tgt = target.trimmingCharacters(in: .whitespaces)
            let start = try await api.request(
                endpoint: .startTransition(
                    TransitionStartRequest(
                        resumeId: resumeId,
                        currentRole: role.isEmpty ? nil : role,
                        target: tgt.isEmpty ? nil : tgt
                    )
                ),
                type: TransitionStartResponse.self
            )
            await poll(id: start.analysisId)
        } catch {
            status = "failed"
            errorMessage = error.localizedDescription
        }
    }

    private func poll(id: String) async {
        for _ in 0..<60 {
            if Task.isCancelled { return }
            do {
                let r = try await api.request(endpoint: .transition(id: id), type: TransitionResultDTO.self)
                status = r.status
                if r.status == "completed" { result = r; await loadTrajectory(); return }
                if r.status == "failed" {
                    errorMessage = r.error ?? "Analysis failed. Please try again."
                    return
                }
            } catch {
                TrueMatchLogger.log(.warning, "Transition poll error: \(error)")
            }
            try? await Task.sleep(nanoseconds: 4_000_000_000)
        }
        if status != "completed" {
            status = "failed"
            errorMessage = "Timed out waiting for the analysis."
        }
    }

    func enableTracking() async {
        guard let id = result?.analysisId else { return }
        do {
            let r = try await api.request(
                endpoint: .setTransitionTracking(id: id, TransitionTrackRequest(enabled: true)),
                type: TransitionTrackResponse.self
            )
            tracking = r.tracking
        } catch {
            TrueMatchLogger.log(.warning, "Transition tracking toggle failed: \(error)")
        }
    }

    func loadTrajectory() async {
        guard let resumeId = selectedResumeId else { return }
        do {
            trajectory = try await api.request(
                endpoint: .transitionTrajectory(resumeId: resumeId),
                type: [TrajectoryPointDTO].self
            )
        } catch {
            TrueMatchLogger.log(.warning, "Transition trajectory load failed: \(error)")
        }
    }
}

struct TransitionPathwaysView: View {
    @Environment(\.trueMatchTheme) private var theme
    @StateObject private var viewModel = TransitionPathwaysViewModel()

    var body: some View {
        NavigationStack {
            Form {
                Section("Your résumé") {
                    if viewModel.resumes.isEmpty {
                        NavigationLink(destination: PhotoResumeUploadView(onUploaded: {
                            Task { await viewModel.loadResumes() }
                        })) {
                            Label("No résumés yet — snap a photo", systemImage: "camera")
                        }
                    } else {
                        Picker("Résumé", selection: $viewModel.selectedResumeId) {
                            ForEach(viewModel.resumes) { r in
                                Text(r.filename ?? "Résumé \(String(r.id.prefix(8)))")
                                    .tag(Optional(r.id))
                            }
                        }
                    }
                }

                Section("Where you are") {
                    TextField("Current role (e.g. Senior Engineer)", text: $viewModel.currentRole)
                        .autocorrectionDisabled()
                    TextField("Target direction (optional)", text: $viewModel.target)
                    Button {
                        Task { await viewModel.run() }
                    } label: {
                        HStack {
                            if viewModel.isRunning { ProgressView().padding(.trailing, 4) }
                            Image(systemName: "arrow.up.right")
                            Text(viewModel.isRunning ? "Mapping pathways…" : "Map my pathways")
                        }
                    }
                    .disabled(!viewModel.canRun)
                }

                if let r = viewModel.result {
                    resultSections(r)
                }
            }
            .navigationTitle("Transition Pathways")
            .task { await viewModel.loadResumes() }
            .alert("Something went wrong",
                   isPresented: Binding(get: { viewModel.errorMessage != nil },
                                        set: { if !$0 { viewModel.errorMessage = nil } })) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: { Text(viewModel.errorMessage ?? "") }
        }
    }

    @ViewBuilder
    private func resultSections(_ r: TransitionResultDTO) -> some View {
        if let summary = r.readinessSummary, !summary.isEmpty {
            Section("Readiness") {
                if let cap = r.capabilityScore {
                    Text("Capability verdict: \(cap)/100").font(.caption).foregroundStyle(.secondary)
                }
                Text(summary).font(.subheadline)
            }
        }

        let options = r.transitionOptions ?? []
        if options.isEmpty {
            Section("Pathways") {
                Text("No pathway could be grounded in the current evidence. Adding more résumé detail surfaces more options — we don't invent them.")
                    .font(.caption).foregroundStyle(.secondary)
            }
        } else {
            ForEach(Array(options.enumerated()), id: \.offset) { _, o in
                optionSection(o)
            }
        }

        if let notes = r.honestyNotes, !notes.isEmpty {
            Section("Honest read") { Text(notes).font(.caption) }
        }

        Section("Track progress") {
            Button {
                Task { await viewModel.enableTracking() }
            } label: {
                HStack {
                    Image(systemName: viewModel.tracking ? "checkmark.circle.fill" : "calendar.badge.clock")
                    Text(viewModel.tracking ? "Tracking quarterly" : "Track my progress quarterly")
                }
            }
            .disabled(viewModel.tracking)
        }

        if viewModel.trajectory.count > 1 {
            Section("Your trajectory") {
                ForEach(Array(viewModel.trajectory.enumerated()), id: \.offset) { _, p in
                    HStack {
                        Text(String((p.date ?? "").prefix(10))).font(.caption).foregroundStyle(.secondary)
                        Spacer()
                        if let cap = p.capabilityScore {
                            Text("capability \(cap)").font(.caption.weight(.medium))
                        }
                        Text("· \(p.ready) ready").font(.caption2).foregroundStyle(theme.colors.capability)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func optionSection(_ o: TransitionOptionDTO) -> some View {
        Section {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 6) {
                    Image(systemName: o.direction == "upward" ? "arrow.up.right" : "arrow.right")
                        .foregroundStyle(theme.colors.capability)
                    Text(o.role).font(.subheadline.weight(.semibold))
                }
                HStack(spacing: 6) {
                    TMBadge(text: feasibilityLabel(o.feasibility), kind: feasibilityKind(o.feasibility))
                    TMBadge(text: "\(o.evidenceStrength) evidence",
                            kind: o.evidenceStrength == "HIGH" ? .success
                                : o.evidenceStrength == "WEAK" ? .warning : .neutral)
                }
                Text(o.rationale).font(.caption).foregroundStyle(.secondary)

                if let tl = o.timeline {
                    Label("Est. \(tl.monthsMin)–\(tl.monthsMax) months (\(tl.confidence) confidence)",
                          systemImage: "clock")
                        .font(.caption).foregroundStyle(.secondary)
                }

                if let strengths = o.transferableStrengths, !strengths.isEmpty {
                    Text("Carries over: \(strengths.joined(separator: " · "))")
                        .font(.caption2).foregroundStyle(.secondary)
                }

                ForEach(Array((o.upskillingGap ?? []).enumerated()), id: \.offset) { _, g in
                    VStack(alignment: .leading, spacing: 3) {
                        Text("• \(g.capability)").font(.caption.weight(.medium))
                        if let how = g.how, !how.isEmpty {
                            Text(how).font(.caption2).foregroundStyle(.secondary)
                        }
                        ForEach(Array((g.recommendedTraining ?? []).enumerated()), id: \.offset) { _, c in
                            HStack(spacing: 4) {
                                Image(systemName: "graduationcap").font(.system(size: 9))
                                Text(c.title).font(.caption2.weight(.medium))
                                Text("· \(c.provider)").font(.caption2).foregroundStyle(.secondary)
                            }
                        }
                    }
                    .padding(.leading, 4)
                }
            }
            .padding(.vertical, 2)
        }
    }

    private func feasibilityLabel(_ f: String) -> String {
        switch f {
        case "READY": return "Ready now"
        case "ASPIRATIONAL": return "Aspirational"
        default: return "Stretch"
        }
    }

    private func feasibilityKind(_ f: String) -> TMBadgeKind {
        switch f {
        case "READY": return .success
        case "ASPIRATIONAL": return .neutral
        default: return .warning
        }
    }
}
