import Foundation
import MQTTNIO
import MySQLNIO
import NIO
import Logging

// 配置日志
LoggingSystem.bootstrap(StreamLogHandler.standardOutput)
let logger = Logger(label: "com.mqttserver.main")

// 配置信息
struct Configuration {
    // MQTT 配置
    static let mqttHost = "broker.emqx.io" // 替换为你的 MQTT broker 地址
    static let mqttPort = 1883
    static let mqttClientId = "swift-mqtt-client-\(UUID().uuidString)"
    static let mqttTopic = "sensor/data" // 订阅的主题

    // MariaDB 配置
    static let dbHost = "localhost"
    static let dbPort = 3306
    static let dbUsername = "root"
    static let dbPassword = "password" // 替换为你的密码
    static let dbDatabase = "mqtt_data"
}

// 启动应用
do {
    let app = try MQTTServerApp()
    try app.run()
} catch {
    logger. error("应用启动失败: \(error)")
    exit(1)
}