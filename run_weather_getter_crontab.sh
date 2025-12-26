#!/bin/bash

# 设置脚本在遇到错误时退出
set -e

# ========== 配置参数 ==========
TIMEOUT_SECONDS=180  # 超时时间：5分钟
MIN_UPTIME=180       # 最小运行时间：5分钟
# ==============================

# 获取系统开机秒数（从 /proc/uptime 读取第一个字段）
uptime_seconds=$(cat /proc/uptime | awk '{print int($1)}')

# 检查是否大于 300 秒 需要等服务运行稳定后再执行
if [ "$uptime_seconds" -gt "$MIN_UPTIME" ]; then
    # 获取脚本所在目录的绝对路径
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$SCRIPT_DIR"

    # 日志文件路径
    LOG_FILE="$PROJECT_ROOT/logs/weather_getter.log"
    mkdir -p "$PROJECT_ROOT/logs"

    # 记录开始时间
    echo "========== $(date '+%Y-%m-%d %H:%M:%S') ==========" >> "$LOG_FILE"

    # 激活虚拟环境
    source "$PROJECT_ROOT/vault/venv/bin/activate"

    # 加载 .env 文件中的环境变量
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    fi

    # 更改指向数据库连接的配置
    export DB_HOST=localhost

    # 运行 Python 脚本（带超时控制）
    cd "$PROJECT_ROOT"
    
    # 方案1: 使用 timeout 命令（推荐）
    if command -v timeout &> /dev/null; then
        echo "Starting script with ${TIMEOUT_SECONDS}s timeout..." >> "$LOG_FILE"
        
        # timeout 会在超时时自动终止进程及其子进程
        timeout --kill-after=10s ${TIMEOUT_SECONDS}s \
            python vault/app/blueprints/smart_clock/weather_data_getter.py >> "$LOG_FILE" 2>&1
        
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 124 ]; then
            echo "ERROR: Script timed out after ${TIMEOUT_SECONDS} seconds" >> "$LOG_FILE"
            echo "Timeout occurred at $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
        elif [ $EXIT_CODE -eq 137 ]; then
            echo "ERROR: Script was killed (SIGKILL) after timeout grace period" >> "$LOG_FILE"
        elif [ $EXIT_CODE -eq 0 ]; then
            echo "Script executed successfully" >> "$LOG_FILE"
        else
            echo "Script execution failed with exit code $EXIT_CODE" >> "$LOG_FILE"
        fi
    else
        # 方案2: 如果没有 timeout 命令，使用后台进程 + kill
        echo "timeout command not found, using manual timeout..." >> "$LOG_FILE"
        
        python vault/app/blueprints/smart_clock/weather_data_getter.py >> "$LOG_FILE" 2>&1 &
        PYTHON_PID=$!
        
        # 等待进程完成或超时
        SECONDS_WAITED=0
        while kill -0 $PYTHON_PID 2>/dev/null; do
            if [ $SECONDS_WAITED -ge $TIMEOUT_SECONDS ]; then
                echo "ERROR:  Script timed out after ${TIMEOUT_SECONDS} seconds" >> "$LOG_FILE"
                echo "Killing process $PYTHON_PID and its children..." >> "$LOG_FILE"
                
                # 杀死进程组（包括子进程）
                pkill -TERM -P $PYTHON_PID 2>/dev/null || true
                sleep 2
                pkill -KILL -P $PYTHON_PID 2>/dev/null || true
                kill -KILL $PYTHON_PID 2>/dev/null || true
                
                echo "Process terminated due to timeout" >> "$LOG_FILE"
                break
            fi
            sleep 1
            SECONDS_WAITED=$((SECONDS_WAITED + 1))
        done
        
        # 检查退出状态
        if kill -0 $PYTHON_PID 2>/dev/null; then
            wait $PYTHON_PID
            EXIT_CODE=$?
            if [ $EXIT_CODE -eq 0 ]; then
                echo "Script executed successfully" >> "$LOG_FILE"
            else
                echo "Script execution failed with exit code $EXIT_CODE" >> "$LOG_FILE"
            fi
        fi
    fi

    echo "Completed at $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
else
    echo "系统运行时间不足 $MIN_UPTIME 秒（当前：$uptime_seconds 秒），跳过任务"
    exit 0
fi