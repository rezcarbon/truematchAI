//
//  Date+Extensions.swift
//  TrueMatch
//

import Foundation

extension Date {
    var relativeDescription: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .short
        return formatter.localizedString(for: self, relativeTo: .now)
    }

    var shortTimestamp: String {
        let calendar = Calendar.current
        if calendar.isDateInToday(self) {
            return formatted(date: .omitted, time: .shortened)
        } else if calendar.isDateInYesterday(self) {
            return "Yesterday \(formatted(date: .omitted, time: .shortened))"
        } else {
            return formatted(date: .abbreviated, time: .shortened)
        }
    }

    var iso8601String: String {
        ISO8601DateFormatter().string(from: self)
    }

    static func fromISO8601(_ string: String) -> Date? {
        ISO8601DateFormatter().date(from: string)
    }
}
