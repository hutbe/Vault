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

// 配置信息
struct Configuration {
    // MQTT 配置
    static let mqttHost = "127.0.0.1" // 替换为你的 MQTT broker 地址
    static let mqttPort = 1883
    static let mqttClientId = "swift-mqtt-client-\(UUID().uuidString)"
    static let mqttTopic = "test/data" // 订阅的主题

    // MariaDB 配置
    static let dbHost = "127.0.0.1"
    static let dbPort = 3306
    static let dbUsername = "hut"
    static let dbPassword = "hut123456" // 替换为你的密码
    static let dbDatabase = "test"
}

// 启动应用
do {
    let app = try MQTTServerApp()
    try app.run()
} catch {
    logger.error("应用启动失败: \(error)")
    exit(1)
}
