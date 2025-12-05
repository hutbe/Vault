// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "MQTTServerApp",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
        // MQTT 客户端库
        .package(url: "https://github.com/swift-server-community/mqtt-nio.git", from: "2.9.0"),
        // MySQL/MariaDB 客户端库
        .package(url: "https://github.com/vapor/mysql-nio.git", from: "1.7.0"),
        // Swift NIO 用于异步处理
        .package(url: "https://github.com/apple/swift-nio.git", from: "2.62.0"),
        // 日志
        .package(url: "https://github.com/apple/swift-log.git", from: "1.5.0"),
    ],
    targets: [
        . executableTarget(
            name: "MQTTServerApp",
            dependencies: [
                .product(name: "MQTTNIO", package: "mqtt-nio"),
                .product(name: "MySQLNIO", package: "mysql-nio"),
                .product(name: "NIO", package: "swift-nio"),
                .product(name: "Logging", package: "swift-log"),
            ]
        ),
    ]
)


// package(url: "https://github.com/vapor/mysql-kit.git", from: "4. 8.0")
