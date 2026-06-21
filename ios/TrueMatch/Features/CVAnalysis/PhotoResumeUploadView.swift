//
//  PhotoResumeUploadView.swift
//  TrueMatch
//
//  Multimodal intake: pick/snap a photo of a printed resume; the backend
//  transcribes it with Claude vision (`POST /files/resume/image`) and creates a
//  Resume from the extracted text.
//

import PhotosUI
import SwiftUI

struct PhotoResumeUploadView: View {
    var onUploaded: (() -> Void)? = nil

    @State private var pickedItem: PhotosPickerItem?
    @State private var imageData: Data?
    @State private var isUploading = false
    @State private var resultMessage: String?
    @State private var errorMessage: String?

    var body: some View {
        Form {
            Section("Resume photo") {
                PhotosPicker(selection: $pickedItem, matching: .images) {
                    Label(imageData == nil ? "Choose a photo" : "Choose a different photo",
                          systemImage: "photo.on.rectangle")
                }
                if let data = imageData, let ui = UIImage(data: data) {
                    Image(uiImage: ui)
                        .resizable()
                        .scaledToFit()
                        .frame(maxHeight: 220)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }
            }
            Section {
                Button {
                    Task { await upload() }
                } label: {
                    HStack {
                        if isUploading { ProgressView().padding(.trailing, 4) }
                        Text(isUploading ? "Transcribing with AI…" : "Upload & transcribe")
                    }
                }
                .disabled(imageData == nil || isUploading)
                if let msg = resultMessage {
                    Label(msg, systemImage: "checkmark.circle.fill").foregroundStyle(.green)
                }
            } footer: {
                Text("The photo is transcribed by AI vision into a structured resume you can assess against any role.")
            }
        }
        .navigationTitle("Photo Resume")
        .navigationBarTitleDisplayMode(.inline)
        .onChange(of: pickedItem) { _, item in
            guard let item else { return }
            Task {
                imageData = try? await item.loadTransferable(type: Data.self)
                resultMessage = nil
            }
        }
        .alert("Upload failed",
               isPresented: Binding(get: { errorMessage != nil },
                                    set: { if !$0 { errorMessage = nil } })) {
            Button("OK", role: .cancel) { errorMessage = nil }
        } message: { Text(errorMessage ?? "") }
    }

    private func upload() async {
        guard let data = imageData else { return }
        isUploading = true
        defer { isUploading = false }
        do {
            // JPEG-recompress to keep within the upload cap and normalize format.
            let payload: Data
            let mime: String
            if let ui = UIImage(data: data), let jpeg = ui.jpegData(compressionQuality: 0.85) {
                payload = jpeg
                mime = "image/jpeg"
            } else {
                payload = data
                mime = "image/png"
            }
            let resp = try await APIClient.shared.upload(
                endpoint: .uploadResumeImage,
                fileData: payload,
                fileName: "resume-photo.jpg",
                mimeType: mime,
                type: PhotoUploadResponse.self
            )
            resultMessage = "Resume created (\(String(resp.resumeId.prefix(8)))…)"
            onUploaded?()
        } catch {
            TrueMatchLogger.log(.error, "Photo resume upload failed: \(error)")
            errorMessage = error.localizedDescription
        }
    }
}

struct PhotoUploadResponse: Codable {
    let resumeId: String
    let fileId: String
    let fileType: String
}
