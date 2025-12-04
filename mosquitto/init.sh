#!/bin/bash

# Mosquitto Docker 环境初始化脚本

echo "==================================="
echo "初始化 Mosquitto 环境"
echo "==================================="

# 1. 创建必要的目录
echo "1. 创建目录结构..."
mkdir -p config data log certs

# 2. 设置权限 (Mosquitto 容器使用 UID 1883)
echo "2. 设置目录权限..."
chmod -R 755 config data log certs

# 3. 生成 SSL 证书 如果没有公共证书,生成使用自签名证书
# echo "3. 生成 SSL 证书..."
bash generate-certs.sh

# 4. 启动 Docker 容器
echo "4.  启动 Mosquitto 容器..."
docker-compose up -d mosquitto

# 等待容器启动
echo "5. 等待容器启动..."
sleep 5

# 6. 创建默认用户
# echo "6.  创建默认用户..."
# docker exec -it mosquitto mosquitto_passwd -b -c /mosquitto/config/passwd admin admin123
# docker exec -it mosquitto mosquitto_passwd -b /mosquitto/config/passwd user1 password1
# docker exec -it mosquitto mosquitto_passwd -b /mosquitto/config/passwd device1 device123

# 7. 重启容器以应用配置
echo "7. 重启容器..."
docker-compose restart

echo "==================================="
echo "初始化完成!"
echo "==================================="
echo "MQTT 端口: 1883 (无SSL)"
echo "MQTT SSL 端口: 8883"
echo "WebSocket 端口: 9010"
echo ""
echo "默认用户:"
echo "  - admin/admin123 (管理员)"
echo "  - user1/password1 (普通用户)"
echo "  - device1/device123 (设备)"
echo "==================================="