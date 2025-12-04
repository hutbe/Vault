#!/bin/bash

# Mosquitto SSL 证书生成脚本

CERTS_DIR="./certs/"
DAYS_VALID=3650  # 10年有效期

# 创建证书目录
mkdir -p $CERTS_DIR
cd $CERTS_DIR

echo "==================================="
echo "生成 Mosquitto SSL 证书"
echo "==================================="

# 1. 生成 CA 私钥
echo "1. 生成 CA 私钥..."
openssl genrsa -out ca.key 4096

# 2. 生成 CA 证书
echo "2. 生成 CA 证书..."
openssl req -new -x509 -days $DAYS_VALID -key ca.key -out ca.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=MyOrganization/OU=IT/CN=Mosquitto CA"

# 3. 生成服务器私钥
echo "3. 生成服务器私钥..."
openssl genrsa -out server.key 4096

# 4. 生成服务器证书签名请求 (CSR)
echo "4. 生成服务器 CSR..."
openssl req -new -key server.key -out server.csr \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=MyOrganization/OU=IT/CN=mosquitto.local"

# 5. 使用 CA 签名服务器证书
echo "5. 签名服务器证书..."
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out server.crt -days $DAYS_VALID

# 6. (可选) 生成客户端证书
echo "6. 生成客户端证书 (可选)..."
openssl genrsa -out client.key 4096
openssl req -new -key client.key -out client.csr \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=MyOrganization/OU=IT/CN=client"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out client.crt -days $DAYS_VALID

# 清理临时文件
rm server.csr client.csr

# 设置权限
chmod 644 *.crt
chmod 600 *.key

echo "==================================="
echo "证书生成完成!"
echo "==================================="
echo "CA 证书: ca.crt"
echo "服务器证书: server.crt"
echo "服务器私钥: server. key"
echo "客户端证书: client.crt (可选)"
echo "客户端私钥: client.key (可选)"
echo "==================================="

cd ..