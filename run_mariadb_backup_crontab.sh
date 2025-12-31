#!/bin/bash

# 配置信息
source 'passwords/db_passwords'

# 备份配置
BACKUP_DIR="/home/hut/mariadb_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/all_databases_${DATE}.sql"
KEEP_DAYS=4

# 创建临时 MySQL 配置文件（避免密码暴露在命令行）
MYSQL_CONFIG=$(mktemp)
trap "rm -f ${MYSQL_CONFIG}" EXIT

cat > ${MYSQL_CONFIG} << EOF
[client]
host=${DB_HOST}
port=${DB_PORT}
user=${DB_USER}
password=${DB_PASSWORD}
EOF

chmod 600 ${MYSQL_CONFIG}

# 错误处理
set -e
error_exit() {
    echo "❌ 错误:  $1" >&2
    exit 1
}

# 创建备份目录
mkdir -p ${BACKUP_DIR} || error_exit "无法创建备份目录"

# 执行备份（使用配置文件，密码不会出现在进程列表中）
echo "🔄 开始备份数据库..."
mysqldump \
  --defaults-extra-file=${MYSQL_CONFIG} \
  --all-databases \
  --single-transaction \
  --quick \
  --lock-tables=false \
  --routines \
  --triggers \
  --events \
  --compress \
  > ${BACKUP_FILE} || error_exit "数据库备份失败"

# 压缩备份文件
echo "📦 压缩备份文件..."
gzip -f ${BACKUP_FILE}

# 清理旧备份
echo "🧹 清理旧备份..."
find ${BACKUP_DIR} -name "all_databases_*.sql.gz" -mtime +${KEEP_DAYS} -delete

# 显示结果
BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
BACKUP_COUNT=$(ls -1 ${BACKUP_DIR}/all_databases_*. sql.gz | wc -l)

echo "✅ 备份完成!  (大小: ${BACKUP_SIZE}, 保留: ${BACKUP_COUNT} 个文件)"