import Foundation
import MySQLNIO
import NIO
import Logging

class DatabaseService {
    private let logger = Logger(label: "com.mqttserver.database")
    private let eventLoopGroup: EventLoopGroup
    private var connection: MySQLConnection?
    
    init(eventLoopGroup: EventLoopGroup) throws {
        self.eventLoopGroup = eventLoopGroup
    }
    
    func connect() -> EventLoopFuture<Void> {
        print("数据库连接配置 dbHost: \(Configuration.dbHost) dbPort: \(Configuration.dbPort) dbUsername: \(Configuration.dbUsername) dbPassword: \(Configuration.dbPassword) dbDatabase: \(Configuration.dbDatabase)")
        // 创建数据库连接配置
        let address: SocketAddress
        do {
            address = try SocketAddress.makeAddressResolvingHost(
                Configuration.dbHost,
                port: Configuration.dbPort
            )
        } catch {
            return eventLoopGroup.next().makeFailedFuture(error)
        }
        
        return MySQLConnection.connect(
            to: address,
            username: Configuration.dbUsername,
            database: Configuration.dbDatabase,
            password: Configuration.dbPassword,
            tlsConfiguration: nil,
            on: eventLoopGroup.next()
        ).map { connection in
            self.connection = connection
            self.logger.info("已连接到 MariaDB 数据库")
        }.flatMapError { error in
            self.logger.error("数据库连接失败: \(error)")
            return self.eventLoopGroup.next().makeFailedFuture(error)
        }
    }
    
    func initializeDatabase() -> EventLoopFuture<Void> {
        guard let connection = connection else {
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
        }
    }
    
    func saveMessage(topic: String, payload: String) -> EventLoopFuture<Void> {
        guard let connection = connection else {
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
        }
    }
    
    func close() -> EventLoopFuture<Void> {
        guard let connection = connection else {
            return eventLoopGroup.next().makeSucceededVoidFuture()
        }
        return connection.close()
    }
}

enum DatabaseError: Error {
    case notConnected
    case configurationError(String)
}
