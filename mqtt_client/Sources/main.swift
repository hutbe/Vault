import Foundation
import MQTTNIO
import MySQLNIO
import NIO
import Logging

// 配置日志
// 配置日志 - 使用闭包包装来符合 Sendable 要求
LoggingSystem.bootstrap { label in
    StreamLogHandler.standardOutput(label: label)
}
let logger = Logger(label: "com.mqttserver.main")

// 启动应用
do {
    let app = try MQTTServerApp()
    try app.run()
} catch {
    logger.error("应用启动失败: \(error)")
    exit(1)
}

// 启动应用 - 测试用
//let app = TestApp()
//app.run()
