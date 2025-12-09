//
//  AdvancedFileLogHandler.swift
//  MQTTServerApp
//
//  Created by Hut on 2025/12/9.
//

import Logging
import Foundation

/// 支持日志轮转的文件日志处理器
public final class AdvancedFileLogHandler: LogHandler {
    private var fileHandle: FileHandle?
    private let fileURL: URL
    private let label: String
    private let maxFileSize: UInt64 // 字节
    private let maxBackupCount: Int
    private let queue = DispatchQueue(label: "com.fileloghandler.queue")
    
    public var logLevel: Logger.Level = .info
    public var metadata = Logger.Metadata()
    
    public subscript(metadataKey key: String) -> Logger.Metadata.Value? {
        get { metadata[key] }
        set { metadata[key] = newValue }
    }
    
    public init(label: String,
                fileURL: URL,
                maxFileSize: UInt64 = 10 * 1024 * 1024, // 默认 10MB
                maxBackupCount: Int = 5) throws {
        self.label = label
        self.fileURL = fileURL
        self.maxFileSize = maxFileSize
        self.maxBackupCount = maxBackupCount
        
        try setupLogFile()
    }
    
    private func setupLogFile() throws {
        let directory = fileURL.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        
        if !FileManager.default.fileExists(atPath: fileURL.path) {
            FileManager.default.createFile(atPath: fileURL.path, contents: nil)
        }
        
        fileHandle = try FileHandle(forWritingTo: fileURL)
        fileHandle?.seekToEndOfFile()
    }
    
    public func log(level: Logger.Level,
                    message: Logger.Message,
                    metadata: Logger.Metadata?,
                    source: String,
                    file: String,
                    function: String,
                    line: UInt) {
        queue.async { [self] in
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd HH:mm:ss.SSS"
            let timestamp = formatter.string(from: Date())
            
            let mergedMetadata = self.metadata.merging(metadata ?? [:]) { $1 }
            let metadataString = mergedMetadata.isEmpty ? "" : " \(mergedMetadata)"
            
            let logString = "[\(timestamp)] [\(level.rawValue.uppercased())] [\(label)] \(message)\(metadataString)\n"
            
            if let data = logString.data(using: .utf8) {
                fileHandle?.write(data)
                
                // 检查是否需要轮转
                try?  rotateLogIfNeeded()
            }
        }
    }
    
    private func rotateLogIfNeeded() throws {
        guard let attributes = try?  FileManager.default.attributesOfItem(atPath: fileURL.path),
              let fileSize = attributes[.size] as? UInt64,
              fileSize >= maxFileSize else {
            return
        }
        
        // 关闭当前文件
        try? fileHandle?.close()
        
        // 删除最旧的备份
        let oldestBackup = fileURL.appendingPathExtension("\(maxBackupCount)")
        try?  FileManager.default.removeItem(at: oldestBackup)
        
        // 重命名现有备份
        for i in (1..<maxBackupCount).reversed() {
            let source = fileURL.appendingPathExtension("\(i)")
            let destination = fileURL.appendingPathExtension("\(i + 1)")
            try? FileManager.default.moveItem(at: source, to: destination)
        }
        
        // 重命名当前日志文件
        let backup = fileURL.appendingPathExtension("1")
        try? FileManager.default.moveItem(at: fileURL, to: backup)
        
        // 创建新文件
        try setupLogFile()
    }
    
    deinit {
        try? fileHandle?.close()
    }
}
