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
        try connectToDatabase()
    }

    private func connectToDatabase() throws {
        let config = MySQLConnection.Configuration(
            serverAddress: . makeAddressResolvingHost(
                Configuration.dbHost,
                port: Configuration.dbPort
            ),
            username: Configuration.dbUsername,
            password: Configuration.dbPassword,
            database: Configuration.dbDatabase
        )

        MySQLConnection.connect(
            to: config,
            on: eventLoopGroup.next()
        ).whenComplete { result in
            switch result {
            case .success(let connection):
                self.connection = connection
                self.logger. info("已连接到 MariaDB 数据库")
            case . failure(let error):
                self.logger.error("数据库连接失败: \(error)")
            }
        }
    }

    func initializeDatabase() -> EventLoopFuture<Void> {
        guard let connection = connection else {
            return eventLoopGroup.next().makeFailedFuture(
                NSError(domain: "Database", code: -1, userInfo: [NSLocalizedDescriptionKey: "数据库未连接"])
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

        return connection.query(createTableSQL).map { _ in
            self.logger.info("数据库表初始化完成")
        }
    }

    func saveMessage(topic: String, payload: String) -> EventLoopFuture<Void> {
        guard let connection = connection else {
            return eventLoopGroup.next(). makeFailedFuture(
                NSError(domain: "Database", code: -1, userInfo: [NSLocalizedDescriptionKey: "数据库未连接"])
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

    deinit {
        try? connection?.close(). wait()
    }
}