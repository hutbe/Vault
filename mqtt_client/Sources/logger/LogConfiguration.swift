//
//  LogConfiguration.swift
//  MQTTServerApp
//
//  Created by Hut on 2025/12/9.
//
import Logging
import Foundation

final class SafeLogConfiguration {
    private static let configureOnce:  Void = {
        let logsDirectory = URL(fileURLWithPath: "./logs")
        let logFileURL = logsDirectory.appendingPathComponent("server.log")
        
        print("🔧 配置日志系统，日志文件路径: \(logFileURL.path)")
        
        LoggingSystem.bootstrap { label in
            let fileHandler = try! AdvancedFileLogHandler(
                label: label,
                fileURL: logFileURL,
                maxFileSize: 50 * 1024 * 1024,
                maxBackupCount:  10
            )
            
            let consoleHandler = StreamLogHandler.standardOutput(label: label)
            return MultiplexLogHandler([fileHandler, consoleHandler])
        }
        
        print("✅ 日志系统已配置")
    }()
    
    static func configure() {
        _ = configureOnce  // 触发一次性初始化
    }
}
