//
//  ResumeUploadViewModel.swift
//  TrueMatch
//

import Foundation
import SwiftUI

@MainActor
final class ResumeUploadViewModel: ObservableObject {
    enum Phase: Equatable {
        case idle
        case uploading
        case creating
        case submitted(assessmentId: String)
        case failed(String)
    }

    @Published var phase: Phase = .idle
    @Published var selectedFileName: String?
    @Published var pastedResumeText: String = ""
    @Published var supplementary: String = ""
    @Published var jobDescription: String = ""

    private var fileData: Data?
    private var mimeType: String = "application/pdf"

    var canSubmit: Bool {
        (fileData != nil || !pastedResumeText.isBlank) && !jobDescription.isBlank
    }

    // MARK: - File Selection

    func selectFile(url: URL) {
        do {
            let data = try Data(contentsOf: url)
            self.fileData = data
            self.selectedFileName = url.lastPathComponent
            self.mimeType = Self.mimeType(for: url.pathExtension)
        } catch {
            phase = .failed("Could not read file: \(error.localizedDescription)")
        }
    }

    func clearFile() {
        fileData = nil
        selectedFileName = nil
    }

    // MARK: - Submit

    func submit() async {
        guard canSubmit else { return }
        HapticManager.submitted()

        do {
            let fileId: String

            if let fileData {
                phase = .uploading
                let upload = try await APIClient.shared.upload(
                    endpoint: .uploadFile,
                    fileData: fileData,
                    fileName: selectedFileName ?? "resume.pdf",
                    mimeType: mimeType,
                    type: FileUploadResponse.self
                )
                fileId = upload.id
            } else {
                // Pasted text path: upload the text as a .txt file.
                phase = .uploading
                let textData = Data(pastedResumeText.utf8)
                let upload = try await APIClient.shared.upload(
                    endpoint: .uploadFile,
                    fileData: textData,
                    fileName: "resume.txt",
                    mimeType: "text/plain",
                    type: FileUploadResponse.self
                )
                fileId = upload.id
            }

            phase = .creating
            let request = CreateAssessmentRequest(
                fileId: fileId,
                supplementary: supplementary.isBlank ? nil : supplementary,
                jobDescription: jobDescription.isBlank ? nil : jobDescription
            )
            let assessment = try await APIClient.shared.request(
                endpoint: .createAssessment(request),
                type: AssessmentResponse.self
            )
            phase = .submitted(assessmentId: assessment.id)
        } catch {
            HapticManager.error()
            phase = .failed(error.localizedDescription)
            TrueMatchLogger.log(.error, "Assessment submission failed: \(error.localizedDescription)")
        }
    }

    // MARK: - Helpers

    private static func mimeType(for ext: String) -> String {
        switch ext.lowercased() {
        case "pdf": return "application/pdf"
        case "doc": return "application/msword"
        case "docx": return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        case "txt": return "text/plain"
        default: return "application/octet-stream"
        }
    }
}
