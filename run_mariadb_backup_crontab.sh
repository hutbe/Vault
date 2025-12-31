#!/bin/bash

# 配置信息
source '/home/hut/passwords/db_passwords'

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

# 检查备份文件是否存在且不为空
if [ ! -s ${BACKUP_FILE} ]; then
    error_exit "备份文件为空或不存在"
fi

# 压缩备份文件
echo "📦 压缩备份文件..."
gzip -f ${BACKUP_FILE} || error_exit "压缩失败"

# 验证压缩文件是否创建成功
if [ ! -f "${BACKUP_FILE}.gz" ]; then
    error_exit "压缩文件创建失败"
fi

# 清理旧备份
echo "🧹 清理旧备份..."
find ${BACKUP_DIR} -name "all_databases_*.sql.gz" -type f -mtime +${KEEP_DAYS} -delete

# 显示结果（修复 ls 命令）
BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)

# 安全地统计备份文件数量
BACKUP_COUNT=$(find ${BACKUP_DIR} -name "all_databases_*.sql.gz" -type f 2>/dev/null | wc -l)

echo "✅ 备份完成!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 文件: ${BACKUP_FILE}.gz"
echo "📊 大小: ${BACKUP_SIZE}"
echo "📦 保留: ${BACKUP_COUNT} 个备份文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 列出所有备份文件（可选）
echo ""
echo "当前备份文件列表:"
find ${BACKUP_DIR} -name "all_databases_*.sql.gz" -type f -printf "%T+ %p (%s bytes)\n" 2>/dev/null | sort -r || ls -lht ${BACKUP_DIR}/all_databases_*.sql.gz 2>/dev/null | head -10