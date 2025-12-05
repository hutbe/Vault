//
//  File.swift
//  MQTTServerApp
//
//  Created by hut on 2025/12/5.
//

import Foundation
import MQTTNIO
import MySQLNIO
import NIO
import NIOSSL
import Logging

class MQTTServerApp {
    private let logger = Logger(label: "com.mqttserver.app")
    private let eventLoopGroup: MultiThreadedEventLoopGroup
    private var mqttClient: MQTTClient?
    private let databaseService: DatabaseService
    
    init() throws {
        // 创建事件循环组
        self.eventLoopGroup = MultiThreadedEventLoopGroup(numberOfThreads: System.coreCount)
        
        // 初始化数据库服务
        self.databaseService = try DatabaseService(eventLoopGroup: eventLoopGroup)
        
        logger.info("应用初始化成功")
        
        Configuration.printConfiguration()
    }
    
    func run() throws {
        // 连接数据库并初始化表
        try databaseService.connect().flatMap { _ in
            return self.databaseService.initializeDatabase()
        }.wait()
        
        // 连接 MQTT Broker
        try connectMQTT()
        
        // 保持程序运行
        logger.info("服务器运行中... 按 Ctrl+C 退出")
        
        // 处理退出信号
        signal(SIGINT) { _ in
            print("\n正在关闭服务器...")
            exit(0)
        }
        
        RunLoop.main.run()
    }
    
    private func connectMQTT() throws {
        // 配置 TLS（如果需要）
//        let tlsConfiguration: TLSConfiguration?  = Configuration.mqttUseSSL ?
//            TLSConfiguration.makeClientConfiguration() : nil
        
        // 创建 MQTT 客户端配置
        let clientConfiguration = MQTTClient.Configuration(
            keepAliveInterval:.seconds(Int64(Configuration.mqttKeepAlive)),
            userName:Configuration.mqttPassword,
            password: Configuration.mqttUsername
        )
        
        // 创建 MQTT 客户端
        self.mqttClient = MQTTClient(
            host: Configuration.mqttHost,
            port: Configuration.mqttPort,
            identifier: Configuration.mqttClientId,
            eventLoopGroupProvider: .shared(eventLoopGroup),
            logger: logger,
            configuration: clientConfiguration
        )
        
        guard let client = mqttClient else {
            throw MQTTError.clientCreationFailed
        }
        
        // 连接到 broker
        let connectFuture = client.connect()
        
        connectFuture.whenSuccess { _ in
            self.logger.info("已连接到 MQTT Broker: \(Configuration.mqttHost):\(Configuration.mqttPort)")
            
            // 订阅主题
            let subscribeFuture = client.subscribe(to: [
                MQTTSubscribeInfo(topicFilter: Configuration.mqttTopic, qos: .atLeastOnce)
            ])
            
            subscribeFuture.whenSuccess { suback in
                self.logger.info("已订阅主题: \(Configuration.mqttTopic)")
                self.logger.debug("订阅响应: \(suback)")
            }
            
            subscribeFuture.whenFailure { error in
                self.logger.error("订阅失败: \(error)")
            }
        }
        
        connectFuture.whenFailure { error in
            self.logger.error("连接 MQTT Broker 失败: \(error)")
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
            let payload = publishInfo.payload
            
            // 将 ByteBuffer 转换为字符串
            var buffer = payload
            guard let messageString = buffer.readString(length: buffer.readableBytes) else {
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
                        self.logger.error("保存消息失败: \(error)")
                    }
                }
            
        case .failure(let error):
            logger.error("接收消息时出错: \(error)")
        }
    }
    
    deinit {
        try? mqttClient?.disconnect().wait()
        try? databaseService.close().wait()
        try? eventLoopGroup.syncShutdownGracefully()
    }
}

enum MQTTError: Error {
    case clientCreationFailed
    case connectionFailed(String)
    case subscriptionFailed(String)
}
