//
//  GovernanceStatusView.swift
//  TrueMatch
//
//  DISPLAY-ONLY governance panel. Every value shown here — status strings,
//  scores, deltas, bias flags, audit id — is supplied verbatim by the backend.
//  The client performs NO threshold evaluation and computes NO status. It only
//  renders what the server returns.
//

import SwiftUI

struct GovernanceStatusView: View {
    let governance: Governance
    @Environment(\.trueMatchTheme) private var theme

    var body: some View {
        TMCard {
            VStack(alignment: .leading, spacing: theme.spacing.sm) {
                HStack(spacing: theme.spacing.xxs) {
                    Image(systemName: "checkmark.shield")
                        .foregroundStyle(theme.colors.primary)
                    Text("Governance")
                        .font(theme.typography.headline)
                        .foregroundStyle(Color.tmTextPrimary)
                    Spacer()
                }

                metricRow(
                    label: "Coherence",
                    status: governance.coherence.status,
                    detail: scoreText(governance.coherence.score)
                )
                metricRow(
                    label: "Consistency",
                    status: governance.consistency.status,
                    detail: deltaText(governance.consistency.delta)
                )
                metricRow(
                    label: "Fidelity",
                    status: governance.fidelity.status,
                    detail: scoreText(governance.fidelity.score)
                )

                if !governance.biasFlags.isEmpty {
                    Divider()
                    VStack(alignment: .leading, spacing: theme.spacing.xxs) {
                        Text("Bias flags")
                            .font(theme.typography.chip)
                            .foregroundStyle(Color.tmTextTertiary)
                        ForEach(governance.biasFlags, id: \.self) { flag in
                            TMBadge(text: flag, kind: .warning, icon: "exclamationmark.triangle")
                        }
                    }
                }

                Divider()
                HStack {
                    Text("Audit ID")
                        .font(theme.typography.chip)
                        .foregroundStyle(Color.tmTextTertiary)
                    Spacer()
                    Text(governance.auditId)
                        .font(theme.typography.chip)
                        .foregroundStyle(Color.tmTextSecondary)
                        .monospaced()
                        .textSelection(.enabled)
                }
            }
        }
    }

    private func metricRow(label: String, status: String, detail: String) -> some View {
        HStack {
            Text(label)
                .font(theme.typography.body)
                .foregroundStyle(Color.tmTextPrimary)
            Spacer()
            Text(detail)
                .font(theme.typography.caption)
                .foregroundStyle(Color.tmTextSecondary)
                .monospacedDigit()
            // Badge colour is purely a presentation mapping of the backend status.
            TMBadge.governance(status: status)
        }
    }

    private func scoreText(_ score: Double) -> String {
        // Display the backend-provided score as-is; no thresholding here.
        String(format: "%.2f", score)
    }

    private func deltaText(_ delta: Double) -> String {
        let sign = delta >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.2f", delta))"
    }
}

#Preview {
    ScrollView {
        GovernanceStatusView(governance: PreviewData.sampleAssessment.governance!)
            .padding()
    }
}
