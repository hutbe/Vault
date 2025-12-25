#!/bin/bash

# 设置脚本在遇到错误时退出
set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# 日志文件路径
LOG_FILE="$PROJECT_ROOT/logs/weather_getter.log"
mkdir -p "$PROJECT_ROOT/logs"

# 记录开始时间
echo "========== $(date '+%Y-%m-%d %H:%M:%S') ==========" >> "$LOG_FILE"

# 激活虚拟环境
source "$PROJECT_ROOT/venv/bin/activate"

# 加载 .env 文件中的环境变量
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    echo "Environment variables loaded from .env" >> "$LOG_FILE"
else
    echo "Warning: .env file not found" >> "$LOG_FILE"
fi

# 运行 Python 脚本
cd "$PROJECT_ROOT"
python vault/app/blueprints/smart_clock/weather_data_getter.py >> "$LOG_FILE" 2>&1

# 记录结束状态
if [ $? -eq 0 ]; then
    echo "Script executed successfully" >> "$LOG_FILE"
else
    echo "Script execution failed with exit code $?" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"