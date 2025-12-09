//
//  File.swift
//  MQTTServerApp
//
//  Created by hut on 2025/12/5.
//

import Foundation

enum Configuration {
    // MQTT 配置
    static let mqttHost = ProcessInfo.processInfo.environment["MQTT_HOST"] ??  "mosquitto"
    static let mqttPort = Int(ProcessInfo.processInfo.environment["MQTT_PORT"] ?? "1883") ?? 1883
    static let mqttUsername = ProcessInfo.processInfo.environment["MQTT_USERNAME"] ?? "admin"
    static let mqttPassword = ProcessInfo.processInfo.environment["MQTT_PASSWORD"] ??  "hut123456"
    static let mqttClientId = ProcessInfo.processInfo.environment["MQTT_CLIENT_ID"] ?? "swift-mqtt-client-\(UUID().uuidString)"
    static let mqttTopic = ProcessInfo.processInfo.environment["MQTT_TOPIC"] ?? "test/data"
    // 支持多个主题，用逗号分隔，例如: "test/data,sensor/temperature,device/status"
    static let mqttTopics: [String] = {
        let topicsString = ProcessInfo.processInfo.environment["MQTT_TOPICS"] ?? mqttTopic
        return topicsString.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
    }()
    static let mqttUseSSL = ProcessInfo.processInfo.environment["MQTT_USE_SSL"] == "true"
    static let mqttKeepAlive = Int(ProcessInfo.processInfo.environment["MQTT_KEEP_ALIVE"] ?? "60") ?? 60
    
    // MariaDB 配置
    static let dbHost = ProcessInfo.processInfo.environment["DB_HOST"] ?? "mariadb"
    static let dbPort = Int(ProcessInfo.processInfo.environment["DB_PORT"] ?? "3306") ?? 3306
    static let dbUsername = ProcessInfo.processInfo.environment["DB_USERNAME"] ?? "hut"
    static let dbPassword = ProcessInfo.processInfo.environment["DB_PASSWORD"] ??  "hut123456"
    static let dbDatabase = ProcessInfo.processInfo.environment["DB_DATABASE"] ?? "home_db"
    
    // 打印配置（用于调试，注意不要打印敏感信息）
    static func printConfiguration() {
        logger.info("=== 配置信息 ===")
        logger.info("MQTT Broker: \(mqttHost):\(mqttPort)")
        logger.info("MQTT Username: \(mqttUsername.isEmpty ? "(未设置)" : "***")")
        logger.info("MQTT Password: \(mqttPassword.isEmpty ? "(未设置)" : "***")")
        logger.info("MQTT Use SSL: \(mqttUseSSL)")
        logger.info("MQTT Topics: \(mqttTopics.joined(separator: ", "))")
        logger.info("MQTT Client ID: \(mqttClientId)")
        logger.info("Database: \(dbUsername)@\(dbHost):\(dbPort)/\(dbDatabase)")
        logger.info("================")
    }
}
