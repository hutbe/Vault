# Swift MQTT Server Application

一个使用 Swift 编写的服务器端应用，用于订阅 MQTT broker 的消息并将其存储到 MariaDB 数据库。

## 功能特性

- ✅ 连接到 MQTT Broker 并订阅主题
- ✅ 接收和处理 MQTT 消息
- ✅ 将消息持久化到 MariaDB 数据库
- ✅ 异步处理，高性能
- ✅ 完整的日志记录

## 环境要求

- Swift 5.9+
- macOS 13+ 或 Linux
- MariaDB 10.5+ 或 MySQL 8.0+
- MQTT Broker (例如: Mosquitto, EMQX)

## 安装步骤

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd MQTTServerApp
```

### 2. 启动数据库和 MQTT Broker (使用 Docker)

```bash
docker-compose up -d
```

### 3. 配置应用

编辑 `Sources/MQTTServerApp/main.swift` 中的 `Configuration` 结构体，设置你的连接信息。

### 4. 构建项目

```bash
swift build
```

### 5. 运行应用

```bash
swift run
```

## 配置说明

在 `main.swift` 中修改以下配置：

```swift
struct Configuration {
    // MQTT 配置
    static let mqttHost = "localhost"
    static let mqttPort = 1883
    static let mqttTopic = "sensor/data"
    
    // MariaDB 配置
    static let dbHost = "localhost"
    static let dbPort = 3306
    static let dbUsername = "root"
    static let dbPassword = "password"
    static let dbDatabase = "mqtt_data"
}
```

## 数据库结构

```sql
CREATE TABLE mqtt_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    payload TEXT NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_topic (topic),
    INDEX idx_received_at (received_at)
);
```

## 测试

使用 MQTT 客户端发送测试消息：

```bash
# 使用 mosquitto_pub 发送消息
mosquitto_pub -h localhost -t "sensor/data" -m '{"temperature": 25.5, "humidity": 60}'
```

## 生产部署

### 使用 systemd (Linux)

创建服务文件 `/etc/systemd/system/mqtt-server.service`:

```ini
[Unit]
Description=Swift MQTT Server
After=network. target mariadb.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/MQTTServerApp
ExecStart=/path/to/MQTTServerApp/. build/release/MQTTServerApp
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable mqtt-server
sudo systemctl start mqtt-server
sudo systemctl status mqtt-server
```

## 许可证

MIT License


Swift Command Line

```
# 清理之前的构建
swift package clean

# 更新依赖
swift package update

# 构建
swift build

# 运行
swift run
```
