# Mosquitto MQTT Broker with Docker

完整的 Mosquitto MQTT broker Docker 配置，包含 SSL/TLS 和用户认证。

## 目录结构

```
. 
├── docker-compose.yml      # Docker Compose 配置
├── init.sh                 # 初始化脚本
├── generate-certs.sh       # SSL 证书生成脚本
├── manage-users.sh         # 用户管理脚本
├── test-client.py          # Python 测试客户端
├── config/                 # 配置文件目录
│   ├── mosquitto.conf      # 主配置文件
│   ├── passwd              # 用户密码文件
│   └── acl.conf            # 访问控制列表
├── certs/                  # SSL 证书目录
│   ├── ca. crt              # CA 证书
│   ├── ca.key              # CA 私钥
│   ├── server.crt          # 服务器证书
│   └── server.key          # 服务器私钥
├── data/                   # 持久化数据目录
└── log/                    # 日志目录
```

## 快速开始

### 1.  初始化环境

```bash
chmod +x init.sh generate-certs.sh manage-users.sh test-client.py
./init.sh
```

这将自动完成：
- 创建目录结构
- 生成 SSL 证书
- 启动 Mosquitto 容器
- 创建默认用户

### 2. 验证服务

```bash
docker-compose ps
docker logs mosquitto
```

## 端口说明

- **1883**: MQTT (无 SSL，需要认证)
- **8883**: MQTT over SSL/TLS
- **9001**: WebSocket

## 用户管理

### 创建用户

```bash
./manage-users.sh create username password
```

### 删除用户

```bash
./manage-users.sh delete username
```

### 列出所有用户

```bash
./manage-users.sh list
```

### 重新加载配置

```bash
./manage-users.sh reload
# 或
docker-compose restart
```

## SSL 证书管理

### 重新生成证书

```bash
./generate-certs.sh
docker-compose restart
```

### 使用自定义域名

编辑 `generate-certs.sh`，修改 `-subj` 参数中的 `CN` 字段：

```bash
-subj "/C=CN/ST=Beijing/L=Beijing/O=MyOrganization/OU=IT/CN=your-domain.com"
```

## 测试连接

### 使用 Python 客户端

```bash
# 普通连接
python3 test-client.py --host localhost --port 1883 -u admin -p admin123

# SSL 连接
python3 test-client.py --host localhost --port 8883 --ssl -u admin -p admin123

# SSL 连接 (验证证书)
python3 test-client.py --host localhost --port 8883 --ssl --ca-cert ./certs/ca.crt -u admin -p admin123
```

### 使用 mosquitto_pub/sub

```bash
# 订阅 (无 SSL)
mosquitto_sub -h localhost -p 1883 -u admin -P admin123 -t "test/#" -v

# 发布 (无 SSL)
mosquitto_pub -h localhost -p 1883 -u admin -P admin123 -t "test/message" -m "Hello MQTT"

# 订阅 (SSL)
mosquitto_sub -h localhost -p 8883 -u admin -P admin123 -t "test/#" -v \
  --cafile ./certs/ca.crt

# 发布 (SSL)
mosquitto_pub -h localhost -p 8883 -u admin -P admin123 -t "test/message" -m "Hello MQTT" \
  --cafile ./certs/ca.crt
```

## ACL 配置

编辑 `config/acl.conf` 配置访问权限：

```conf
# 用户权限
user username
topic readwrite path/to/topic/#
topic read another/topic/#

# 模式匹配
pattern readwrite devices/%u/#
```

修改后重启容器：

```bash
docker-compose restart
```

## 常见问题

### 1. 权限错误

```bash
sudo chown -R 1883:1883 data log
```

### 2. SSL 证书验证失败

确保证书中的 CN (Common Name) 与连接的主机名匹配，或在测试时使用 `--insecure` 选项。

### 3. 查看日志

```bash
# 实时日志
docker logs -f mosquitto

# 日志文件
tail -f log/mosquitto.log
```

### 4. 重置所有数据

```bash
docker-compose down
rm -rf data/* log/* config/passwd
./init.sh
```

## 生产环境建议

1.  **修改默认密码**: 立即修改所有默认用户的密码
2. **禁用非 SSL 端口**: 在 `mosquitto.conf` 中注释掉 1883 端口监听器
3. **使用有效的 SSL 证书**: 从可信 CA 获取证书，而不是自签名证书
4. **配置防火墙**: 只开放必要的端口
5. **定期备份**: 备份 `data/` 和 `config/` 目录
6. **限制连接数**: 根据需要调整 `max_connections`
7. **启用日志轮转**: 防止日志文件过大

## 备份与恢复

### 备份

```bash
tar -czf mosquitto-backup-$(date +%Y%m%d).tar.gz config/ data/ certs/
```

### 恢复

```bash
tar -xzf mosquitto-backup-YYYYMMDD.tar.gz
docker-compose restart
```

## 监控

查看连接状态：

```bash
docker exec mosquitto mosquitto_sub -t '$SYS/#' -u admin -P admin123 -v
```

## 许可证

MIT License
```