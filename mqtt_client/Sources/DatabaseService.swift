import Foundation
import MySQLNIO
import NIO
import Logging

class DatabaseService {
    private let logger = Logger(label: "com.mqttserver.database")
    private let eventLoopGroup: EventLoopGroup
    private var connection: MySQLConnection?
    private var healthCheckTask: RepeatedTask?
    private var isReconnecting = false
    
    // 重连配置
    private let initialReconnectDelay: TimeAmount = .seconds(1)
    private let maxReconnectDelay: TimeAmount = .seconds(30)
    private let maxReconnectAttempts = 10
    private let healthCheckInterval: TimeAmount = .seconds(30)
    private let healthCheckInitialDelay: TimeAmount = .seconds(10)
    
    init(eventLoopGroup: EventLoopGroup) throws {
        self.eventLoopGroup = eventLoopGroup
    }
    
    func connect() -> EventLoopFuture<Void> {
        return establishConnection()
    }
    
    /// 建立数据库连接
    private func establishConnection() -> EventLoopFuture<Void> {
        let eventLoop = eventLoopGroup.next()
        
        let address: SocketAddress
        do {
            address = try SocketAddress.makeAddressResolvingHost(
                Configuration.dbHost,
                port: Configuration.dbPort
            )
        } catch {
            return eventLoop.makeFailedFuture(error)
        }
        
        return MySQLConnection.connect(
            to: address,
            username: Configuration.dbUsername,
            database: Configuration.dbDatabase,
            password: Configuration.dbPassword,
            tlsConfiguration: nil,
            on: eventLoop
        ).map { connection in
            self.connection = connection
            self.logger.info("已连接到 MariaDB 数据库")
            self.isReconnecting = false
            // 连接成功后启动健康检查
            self.startHealthCheck()
        }.flatMapError { error in
            self.logger.error("数据库连接失败: \(error)")
            return eventLoop.makeFailedFuture(error)
        }
    }
    
    /// 启动定期健康检查
    private func startHealthCheck() {
        // 取消现有的健康检查任务
        self.healthCheckTask?.cancel()
        
        let eventLoop = eventLoopGroup.next()
        // 定期执行健康检查：初始延迟10秒，之后每30秒执行一次
        self.healthCheckTask = eventLoop.scheduleRepeatedTask(
            initialDelay: healthCheckInitialDelay,
            delay: healthCheckInterval
        ) { task in
            guard let conn = self.connection else {
                self.logger.warning("健康检查：无数据库连接，触发重连")
                self.triggerReconnect()
                return
            }
            
            // 执行轻量级查询检查连接状态
            conn.simpleQuery("SELECT 1").whenFailure { error in
                self.logger.warning("健康检查失败: \(error)，将尝试重连")
                self.triggerReconnect()
            }
        }
    }
    
    /// 触发重连机制
    private func triggerReconnect() {
        let eventLoop = eventLoopGroup.next()
        eventLoop.execute {
            // 确保只有一个重连循环在运行
            if self.isReconnecting {
                return
            }
            self.isReconnecting = true
            self.attemptReconnect(attempt: 1)
        }
    }
    
    /// 尝试重连（带指数退避）
    private func attemptReconnect(attempt: Int) {
        let eventLoop = eventLoopGroup.next()
        let delay = calculateBackoffDelay(for: attempt)
        
        self.logger.info("重连尝试 \(attempt)/\(maxReconnectAttempts)，将在 \(delay.nanoseconds / 1_000_000_000) 秒后重试")
        
        eventLoop.scheduleTask(deadline: .now() + delay) {
            self.establishConnection().whenComplete { result in
                switch result {
                case .success:
                    self.logger.info("重连成功（第 \(attempt) 次尝试）")
                case .failure(let error):
                    self.logger.error("重连失败（第 \(attempt) 次尝试）: \(error)")
                    if attempt < self.maxReconnectAttempts {
                        self.attemptReconnect(attempt: attempt + 1)
                    } else {
                        self.logger.error("达到最大重连次数 (\(self.maxReconnectAttempts))，将继续定期尝试")
                        // 达到最大次数后，使用最大延迟时间继续定期尝试
                        self.eventLoopGroup.next().scheduleTask(deadline: .now() + self.maxReconnectDelay) {
                            self.isReconnecting = false
                            self.triggerReconnect()
                        }
                    }
                }
            }
        }
    }
    
    /// 计算指数退避延迟时间
    private func calculateBackoffDelay(for attempt: Int) -> TimeAmount {
        // 指数退避：1s, 2s, 4s, 8s, 16s, 30s(最大)
        let multiplier = Double(1 << (max(0, attempt - 1)))
        let seconds = min(
            Double(initialReconnectDelay.nanoseconds) / 1_000_000_000.0 * multiplier,
            Double(maxReconnectDelay.nanoseconds) / 1_000_000_000.0
        )
        return .seconds(Int64(seconds))
    }
    
    func initializeDatabase() -> EventLoopFuture<Void> {
        guard let connection = connection else {
            triggerReconnect()
            return eventLoopGroup.next().makeFailedFuture(
                DatabaseError.notConnected
            )
        }
        
        let createTableSQL = """
        CREATE TABLE IF NOT EXISTS mqtt_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            topic VARCHAR(255) NOT NULL,
            payload TEXT NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_topic (topic),
            INDEX idx_received_at (received_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        return connection.simpleQuery(createTableSQL).map { _ in
            self.logger.info("数据库表初始化完成")
        }.flatMapError { error in
            self.logger.error("初始化数据库表失败: \(error)，触发重连")
            self.triggerReconnect()
            return self.eventLoopGroup.next().makeFailedFuture(error)
        }
    }
    
    func saveMessage(topic: String, payload: String) -> EventLoopFuture<Void> {
        guard let connection = connection else {
            triggerReconnect()
            return eventLoopGroup.next().makeFailedFuture(
                DatabaseError.notConnected
            )
        }
        
        let insertSQL = """
        INSERT INTO mqtt_messages (topic, payload) VALUES (?, ?)
        """
        
        return connection.query(insertSQL, [
            MySQLData(string: topic),
            MySQLData(string: payload)
        ]).map { _ in
            self.logger.debug("消息已插入数据库")
        }.flatMapError { error in
            self.logger.error("插入消息失败: \(error)，触发重连")
            self.triggerReconnect()
            return self.eventLoopGroup.next().makeFailedFuture(error)
        }
    }
    
    func close() -> EventLoopFuture<Void> {
        // 停止健康检查
        self.healthCheckTask?.cancel()
        self.healthCheckTask = nil
        
        guard let connection = connection else {
            return eventLoopGroup.next().makeSucceededVoidFuture()
        }
        
        self.connection = nil
        self.isReconnecting = false
        return connection.close()
    }
}

enum DatabaseError: Error {
    case notConnected
    case configurationError(String)
}
