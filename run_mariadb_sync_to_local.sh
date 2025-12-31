#!/bin/bash

# 配置信息
source '/Users/hut/passwords/db_password'

# 启用错误时退出
set -e

# 错误处理函数
error_exit() {
    echo "错误: $1" >&2
    exit 1
}

# 检查必需的环境变量
required_vars=(
    "SERVER_USER" "SERVER_IP" "SERVER_BACKUP_PATH"
    "LOCAL_DB_HOST" "LOCAL_DB_USER" "LOCAL_DB_PASS"
)
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_exit "缺少必需的环境变量: $var"
    fi
done

echo "正在查找最新备份..."
# 获取最新的备份文件
LATEST_BACKUP=$(ssh ${SERVER_USER}@${SERVER_IP}:${LOCAL_DB_PORT} "ls -t ${SERVER_BACKUP_PATH}/*.sql.gz 2>/dev/null | head -1") || error_exit "无法获取备份文件列表"

if [ -z "$LATEST_BACKUP" ]; then
    error_exit "未找到备份文件"
fi

echo "找到备份:  $LATEST_BACKUP"

# 下载备份文件
echo "正在下载备份文件..."
BACKUP_FILE=$(basename ${LATEST_BACKUP})
scp ${SERVER_USER}@${SERVER_IP}:${LATEST_BACKUP} /tmp/ || error_exit "下载失败"

# 解压
echo "正在解压..."
gunzip -f /tmp/${BACKUP_FILE} || error_exit "解压失败"
SQL_FILE="/tmp/${BACKUP_FILE%.gz}"

# 检查解压后的文件是否存在
if [ ! -f "$SQL_FILE" ]; then
    error_exit "解压后的 SQL 文件不存在"
fi

# 删除本地数据库并重新创建
echo "正在删除旧数据库..."
mariadb -h ${LOCAL_DB_HOST} -u ${LOCAL_DB_USER} -p${LOCAL_DB_PASS} << EOF || error_exit "删除数据库失败"
DROP DATABASE IF EXISTS home_db;
DROP DATABASE IF EXISTS image_db;
DROP DATABASE IF EXISTS vault_db;
EOF

# 导入数据
echo "正在导入数据..."
mariadb -h ${LOCAL_DB_HOST} -u ${LOCAL_DB_USER} -p${LOCAL_DB_PASS} < ${SQL_FILE} || error_exit "导入数据失败"

# 清理临时文件
echo "正在清理临时文件..."
rm -f ${SQL_FILE}

echo "✅ Database sync completed successfully!"