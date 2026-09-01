//
//  MatchTimelineView.swift
//  TrueMatch
//
//  Displays match status timeline showing when profile was sent, viewed, interviewed, etc.
//

import SwiftUI

struct MatchTimelineView: View {
    let events: [MatchTimelineEvent]
    let companyName: String

    var body: some View {
        if events.isEmpty {
            VStack(alignment: .center, spacing: 12) {
                Image(systemName: "clock.badge.questionmark")
                    .font(.title)
                    .foregroundColor(.secondary)

                Text("Waiting for updates from \(companyName)...")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(8)
        } else {
            VStack(alignment: .leading, spacing: 0) {
                ForEach(Array(events.sorted(by: { a, b in
                    (ISO8601DateFormatter().date(from: a.timestamp) ?? Date()) >
                    (ISO8601DateFormatter().date(from: b.timestamp) ?? Date())
                }).enumerated()), id: \.element.id) { index, event in
                    TimelineEventRow(
                        event: event,
                        isFirst: index == 0,
                        isLast: index == events.count - 1
                    )
                }
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(8)
            .border(Color(.systemGray4), width: 1)
        }
    }
}

struct MatchTimelineEvent: Identifiable {
    let id: String
    let status: String
    let message: String?
    let timestamp: String
    let emailSent: Bool
}

struct TimelineEventRow: View {
    let event: MatchTimelineEvent
    let isFirst: Bool
    let isLast: Bool

    var relativeTime: String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: event.timestamp) else { return event.timestamp }

        let calendar = Calendar.current
        let now = Date()
        let components = calendar.dateComponents([.year, .month, .day, .hour, .minute], from: date, to: now)

        if let day = components.day, day > 0 {
            return "\(day)d ago"
        } else if let hour = components.hour, hour > 0 {
            return "\(hour)h ago"
        } else if let minute = components.minute, minute > 0 {
            return "\(minute)m ago"
        } else {
            return "just now"
        }
    }

    var statusIcon: String {
        switch event.status {
        case "profile_sent": return "📤"
        case "profile_viewed": return "👁️"
        case "interview_scheduled": return "📅"
        case "interview_completed": return "✅"
        case "offer_received": return "🎉"
        case "rejected": return "📋"
        default: return "⏳"
        }
    }

    var statusLabel: String {
        switch event.status {
        case "profile_sent": return "Profile Sent"
        case "profile_viewed": return "Profile Viewed"
        case "interview_scheduled": return "Interview Scheduled"
        case "interview_completed": return "Interview Completed"
        case "offer_received": return "Offer Received"
        case "rejected": return "Position Filled"
        default: return "Status Update"
        }
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .center, spacing: 8) {
                Text(statusIcon)
                    .font(.title2)
                    .frame(width: 32, height: 32)
                    .background(isFirst ? Color.blue.opacity(0.2) : Color(.systemGray6))
                    .cornerRadius(16)

                if !isLast {
                    VStack(spacing: 0) {
                        ForEach(0..<3, id: \.self) { _ in
                            Rectangle()
                                .fill(Color(.systemGray4))
                                .frame(width: 1, height: 8)
                        }
                    }
                    .frame(height: 24)
                }
            }
            .frame(width: 32)

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(statusLabel)
                            .font(.subheadline)
                            .fontWeight(.semibold)

                        if let message = event.message {
                            Text(message)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    Spacer()

                    Text(relativeTime)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }

                if event.emailSent {
                    HStack(spacing: 4) {
                        Image(systemName: "envelope.fill")
                            .font(.caption2)
                            .foregroundColor(.green)
                        Text("Email sent")
                            .font(.caption2)
                            .foregroundColor(.green)
                    }
                }
            }
            .padding(.vertical, 8)
        }
    }
}

#Preview {
    VStack(spacing: 20) {
        MatchTimelineView(
            events: [
                MatchTimelineEvent(
                    id: "1",
                    status: "profile_sent",
                    message: "Your profile was sent to the hiring team",
                    timestamp: ISO8601DateFormatter().string(from: Date().addingTimeInterval(-3600)),
                    emailSent: true
                ),
                MatchTimelineEvent(
                    id: "2",
                    status: "profile_viewed",
                    message: "Hiring manager reviewed your profile",
                    timestamp: ISO8601DateFormatter().string(from: Date().addingTimeInterval(-1800)),
                    emailSent: true
                ),
                MatchTimelineEvent(
                    id: "3",
                    status: "interview_scheduled",
                    message: "Interview scheduled for next week",
                    timestamp: ISO8601DateFormatter().string(from: Date().addingTimeInterval(-600)),
                    emailSent: true
                )
            ],
            companyName: "TechCorp"
        )

        Divider()

        MatchTimelineView(events: [], companyName: "Acme Inc")
    }
    .padding()
}
