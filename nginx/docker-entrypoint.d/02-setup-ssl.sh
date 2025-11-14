#!/bin/sh
set -e

echo "Initializing ssl configuration..."
echo "SSL_ENABLED is:  ${SSL_ENABLED} DOMAIN_NAME: ${DOMAIN_NAME}"

if [ "${SSL_ENABLED}" = "true" ]; then
    echo "Setting up SSL certificates..."

    # 如果证书不存在，生成自签名证书
    if [ ! -f ${SSL_KEY_PATH} ]; then
      echo "SSL certificates not exist！Generating new certificates"
      openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
          -keyout ${SSL_KEY_PATH} \
          -out ${SSL_CERT_PATH} \
          -subj "/C=CN/ST=GuangDong/L=ShenZheng/O=Hut/CN=localhost"
      echo "Self-signed certificate generated"
    else
      # 执行条件为假时的命令
      echo "SSL certificates already exist！"
    fi

    # 设置正确的权限
    chmod 600 /etc/nginx/certs/server.key
    chmod 644 /etc/nginx/certs/server.crt
fi