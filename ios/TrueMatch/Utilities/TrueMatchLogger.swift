//
//  TrueMatchLogger.swift
//  TrueMatch
//

import Foundation
import os.log

enum TrueMatchLogger {
    enum Level: String {
        case debug = "DEBUG"
        case info = "INFO"
        case warning = "WARNING"
        case error = "ERROR"
    }

    private static let logger = Logger(
        subsystem: "ai.truematch.app",
        category: "TrueMatch"
    )

    static func log(_ level: Level, _ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        let fileName = (file as NSString).lastPathComponent

        switch level {
        case .debug:
            logger.debug("[\(level.rawValue)] \(fileName):\(line) \(function) — \(message)")
        case .info:
            logger.info("[\(level.rawValue)] \(fileName):\(line) \(function) — \(message)")
        case .warning:
            logger.warning("[\(level.rawValue)] \(fileName):\(line) \(function) — \(message)")
        case .error:
            logger.error("[\(level.rawValue)] \(fileName):\(line) \(function) — \(message)")
        }

        #if DEBUG
        print("[\(level.rawValue)] \(fileName):\(line) \(function) — \(message)")
        #endif
    }
}
