//
//  MultiplexLogHandler.swift
//  MQTTServerApp
//
//  Created by Hut on 2025/12/9.
//

import Logging

/// 多路复用日志处理器 - 同时输出到多个目标
public struct MultiplexLogHandler: LogHandler {
    private var handlers: [LogHandler]
    
    public var logLevel: Logger.Level {
        get { handlers[0].logLevel }
        set { handlers = handlers.map { var handler = $0; handler.logLevel = newValue; return handler } }
    }
    
    public var metadata:  Logger.Metadata {
        get { handlers[0].metadata }
        set { handlers = handlers.map { var handler = $0; handler.metadata = newValue; return handler } }
    }
    
    public subscript(metadataKey key: String) -> Logger.Metadata.Value? {
        get { handlers[0][metadataKey:  key] }
        set { handlers = handlers.map { var handler = $0; handler[metadataKey: key] = newValue; return handler } }
    }
    
    public init(_ handlers: [LogHandler]) {
        self.handlers = handlers
    }
    
    public func log(level: Logger.Level,
                    message: Logger.Message,
                    metadata: Logger.Metadata?,
                    source: String,
                    file: String,
                    function: String,
                    line: UInt) {
        for handler in handlers {
            handler.log(level: level, message: message, metadata: metadata,
                       source: source, file: file, function: function, line: line)
        }
    }
}
