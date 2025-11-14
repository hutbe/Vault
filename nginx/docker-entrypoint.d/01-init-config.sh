#!/bin/sh
set -e

echo "Initializing nginx configuration..."

# 使用envsubst替换模板文件中的环境变量
#envsubst '${API_HOST} ${API_PORT}' < /tmp/nginx.conf.template > /etc/nginx/nginx.conf
#
## 创建必要的目录
#mkdir -p /var/log/nginx/custom
#mkdir -p /var/cache/nginx/custom
#
## 设置权限
#chmod 755 /var/log/nginx/custom

chmod +x /docker-entrypoint.d/*.sh