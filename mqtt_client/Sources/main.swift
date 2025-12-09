import Foundation
import MQTTNIO
import MySQLNIO
import NIO
import Logging

// 配置日志
SafeLogConfiguration.configure()

let logger = Logger(label: "com.mqttserver.main")

// 设置运行模式：true = 测试模式, false = 生产模式
let isTestMode = false

if isTestMode {
    // 启动应用 - 测试用
    print("========== 测试模式 ==========")
    let app = TestApp()
    app.run()
} else {
    // 启动应用 - 生产模式
    do {
        let app = try MQTTServerApp()
        try app.run()
    } catch {
        logger.error("应用启动失败: \(error)")
        exit(1)
    }
}
