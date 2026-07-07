//
//  ApplicationTrackingViewModel.swift
//  TrueMatch
//
//  Manages application tracking with pipeline organization, stage filtering,
//  timeline events, and interview preparation.
//

import Foundation
import SwiftUI
import Combine

@MainActor
final class ApplicationTrackingViewModel: ObservableObject {
    @Published var applications: [ApplicationStatus] = []
    @Published var applicationsByStage: [String: [ApplicationStatus]] = [:]
    @Published var selectedStage: String = "applied"
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var selectedApplication: ApplicationStatus?

    private let api = APIClient.shared
    private let candidateId: String

    let stageOrder = ["applied", "reviewing", "interviewing", "offer", "closed"]

    init(candidateId: String) {
        self.candidateId = candidateId
    }

    // MARK: - Loading

    func loadApplications() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let request = GetApplicationsRequest(candidateId: candidateId)
            applications = try await api.request(
                endpoint: .candidateApplications(request: request),
                type: [ApplicationStatus].self
            )

            organizeByStage()
            trackViewing()
        } catch {
            TrueMatchLogger.log(.error, "ApplicationTracking: load failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    private func organizeByStage() {
        var staged: [String: [ApplicationStatus]] = [:]

        for stage in stageOrder {
            staged[stage] = applications.filter { $0.stage == stage }
                .sorted { $0.lastUpdateDate > $1.lastUpdateDate }
        }

        applicationsByStage = staged
    }

    private func trackViewing() {
        TrueMatchLogger.log(.info, "ApplicationTracking: viewed \(applications.count) applications")
    }

    // MARK: - Navigation

    func selectApplication(_ application: ApplicationStatus) {
        selectedApplication = application
        TrueMatchLogger.log(.info, "ApplicationTracking: selected application \(application.id)")
    }

    func getApplicationsForStage(_ stage: String) -> [ApplicationStatus] {
        applicationsByStage[stage] ?? []
    }

    // MARK: - Actions

    func rescheduleInterview(_ session: InterviewSession) {
        TrueMatchLogger.log(.info, "ApplicationTracking: reschedule interview \(session.id)")
        // Navigate to calendar or show reschedule sheet
    }

    func acceptOffer(_ application: ApplicationStatus) async {
        TrueMatchLogger.log(.info, "ApplicationTracking: accept offer for \(application.id)")

        do {
            try await api.requestVoid(
                endpoint: .candidateAcceptOffer(applicationId: application.id)
            )

            if let index = applications.firstIndex(where: { $0.id == application.id }) {
                applications[index].offerDetails?.status = "accepted"
            }
            organizeByStage()
        } catch {
            TrueMatchLogger.log(.error, "ApplicationTracking: accept offer failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    func declineOffer(_ application: ApplicationStatus) async {
        TrueMatchLogger.log(.info, "ApplicationTracking: decline offer for \(application.id)")

        do {
            try await api.requestVoid(
                endpoint: .candidateDeclineOffer(applicationId: application.id)
            )

            if let index = applications.firstIndex(where: { $0.id == application.id }) {
                applications[index].offerDetails?.status = "declined"
            }
            organizeByStage()
        } catch {
            TrueMatchLogger.log(.error, "ApplicationTracking: decline offer failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }
}
