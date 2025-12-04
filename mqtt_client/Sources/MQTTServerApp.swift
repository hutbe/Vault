import Foundation
import MQTTNIO
import MySQLNIO
import NIO
import Logging

class MQTTServerApp {
    private let logger = Logger(label: "com. mqttserver.app")
    private let eventLoopGroup: MultiThreadedEventLoopGroup
    private var mqttClient: MQTTClient?
    private let databaseService: DatabaseService

    init() throws {
        // 创建事件循环组
        self.eventLoopGroup = MultiThreadedEventLoopGroup(numberOfThreads: System.coreCount)

        // 初始化数据库服务
        self. databaseService = try DatabaseService(eventLoopGroup: eventLoopGroup)

        logger.info("应用初始化成功")
    }

    func run() throws {
        // 初始化数据库表
        try databaseService.initializeDatabase(). wait()

        // 连接 MQTT Broker
        try connectMQTT()

        // 保持程序运行
        logger.info("服务器运行中...  按 Ctrl+C 退出")

        // 处理退出信号
        signal(SIGINT) { _ in
            print("\n正在关闭服务器...")
            exit(0)
        }

        RunLoop.main.run()
    }

    private func connectMQTT() throws {
        let eventLoop = eventLoopGroup.next()

        // 创建 MQTT 客户端
        self. mqttClient = MQTTClient(
            host: Configuration.mqttHost,
            port: Configuration.mqttPort,
            identifier: Configuration.mqttClientId,
            eventLoopGroupProvider: . shared(eventLoopGroup),
            logger: logger
        )

        guard let client = mqttClient else {
            throw NSError(domain: "MQTT", code: -1, userInfo: [NSLocalizedDescriptionKey: "无法创建 MQTT 客户端"])
        }

        // 连接到 broker
        client.connect(
            cleanSession: true,
            will: nil
        ).flatMap { _ -> EventLoopFuture<Void> in
            self.logger.info("已连接到 MQTT Broker: \(Configuration.mqttHost):\(Configuration.mqttPort)")

            // 订阅主题
            return client.subscribe(to: [
                MQTTSubscribeInfo(topicFilter: Configuration.mqttTopic, qos: .atLeastOnce)
            ])
        }. whenSuccess { _ in
            self. logger.info("已订阅主题: \(Configuration.mqttTopic)")
        }

        // 处理接收到的消息
        client.addPublishListener(named: "message-handler") { result in
            self.handleMQTTMessage(result: result)
        }
    }

    private func handleMQTTMessage(result: Result<MQTTPublishInfo, Error>) {
        switch result {
        case .success(let publishInfo):
            let topic = publishInfo.topicName
            let payload = publishInfo. payload

            // 将 ByteBuffer 转换为字符串
            var buffer = payload
            guard let messageString = buffer.readString(length: buffer. readableBytes) else {
                logger.error("无法解析消息内容")
                return
            }

            logger.info("收到消息 - 主题: \(topic), 内容: \(messageString)")

            // 保存到数据库
            databaseService.saveMessage(topic: topic, payload: messageString)
                .whenComplete { result in
                    switch result {
                    case .success:
                        self.logger.info("消息已保存到数据库")
                    case .failure(let error):
                        self.logger. error("保存消息失败: \(error)")
                    }
                }

        case .failure(let error):
            logger.error("接收消息时出错: \(error)")
        }
    }

    deinit {
        try? mqttClient?.disconnect(). wait()
        try? eventLoopGroup.syncShutdownGracefully()
    }
}