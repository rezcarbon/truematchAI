//
//  JDSimulationView.swift
//  TrueMatch
//
//  Recruiter JD simulation: paste a JD, run a requirement-fit simulation, and
//  see quality score, requirement creep, and wording suggestions. Polls the
//  async backend job to completion.
//

import SwiftUI

@MainActor
final class JDSimulationViewModel: ObservableObject {
    @Published var jdText = ""
    @Published var status = "idle"      // idle | analyzing | completed | failed
    @Published var result: JDSimResultDTO?
    @Published var errorMessage: String?

    private let api = APIClient.shared
    private var pollTask: Task<Void, Never>?

    var isRunning: Bool { status == "analyzing" || status == "pending" }
    var canRun: Bool { jdText.count >= 20 && !isRunning }

    func run() async {
        guard canRun else { return }
        result = nil
        status = "analyzing"
        do {
            let start = try await api.request(
                endpoint: .startJDSimulation(JDSimRequest(jdText: jdText, simulationType: "requirement_fit")),
                type: JDSimStartResponse.self
            )
            await poll(id: start.simulationId)
        } catch {
            status = "failed"
            errorMessage = error.localizedDescription
        }
    }

    private func poll(id: String) async {
        for _ in 0..<40 {
            if Task.isCancelled { return }
            do {
                let r = try await api.request(endpoint: .jdSimulation(id: id), type: JDSimResultDTO.self)
                status = r.status
                if r.status == "completed" {
                    result = r
                    return
                }
                if r.status == "failed" {
                    errorMessage = "Simulation failed."
                    return
                }
            } catch {
                // transient — keep polling a few more times
                TrueMatchLogger.log(.warning, "JD sim poll error: \(error)")
            }
            try? await Task.sleep(nanoseconds: 5_000_000_000)
        }
        if status != "completed" {
            status = "failed"
            errorMessage = "Timed out waiting for the simulation."
        }
    }
}

struct JDSimulationView: View {
    @StateObject private var viewModel = JDSimulationViewModel()
    @FocusState private var editorFocused: Bool

    var body: some View {
        NavigationStack {
            Form {
                Section("Job description") {
                    TextEditor(text: $viewModel.jdText)
                        .frame(height: 160)
                        .focused($editorFocused)
                    Button {
                        editorFocused = false
                        Task { await viewModel.run() }
                    } label: {
                        HStack {
                            if viewModel.isRunning { ProgressView().padding(.trailing, 4) }
                            Text(viewModel.isRunning ? "Analysing…" : "Run simulation")
                        }
                    }
                    .disabled(!viewModel.canRun)
                }

                if let r = viewModel.result {
                    Section("Quality") {
                        LabeledContent("Quality score", value: "\(r.qualityScore ?? 0)")
                        LabeledContent("Requirement difficulty", value: "\(r.requirementDifficultyScore ?? 0)")
                        if let m = r.marketPositioning { LabeledContent("Market", value: m) }
                        if let a = r.bestArchetypeFit { LabeledContent("Best archetype", value: a) }
                    }
                    if let creep = r.creepWarnings, !creep.isEmpty {
                        Section("Requirement creep") {
                            ForEach(creep) { c in
                                VStack(alignment: .leading, spacing: 2) {
                                    Label(c.issue, systemImage: "exclamationmark.triangle.fill")
                                        .foregroundStyle(.orange)
                                        .font(.subheadline)
                                    if let s = c.suggestion {
                                        Text(s).font(.caption).foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                    }
                    if let wording = r.capabilityVerbiageSuggestions, !wording.isEmpty {
                        Section("Wording suggestions") {
                            ForEach(wording) { w in
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(w.capabilityArea).font(.subheadline.weight(.semibold))
                                    Text(w.reasoning).font(.caption).foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("JD Simulation")
            .alert("Simulation error",
                   isPresented: Binding(get: { viewModel.errorMessage != nil },
                                        set: { if !$0 { viewModel.errorMessage = nil } })) {
                Button("OK", role: .cancel) { viewModel.errorMessage = nil }
            } message: { Text(viewModel.errorMessage ?? "") }
        }
    }
}
