#!/bin/bash

# Mosquitto 用户管理脚本

PASSWD_FILE="./config/passwd"
DOCKER_CONTAINER="mosquitto"

function create_user() {
    local username=$1
    local password=$2
    
    if [ -z "$username" ] || [ -z "$password" ]; then
        echo "用法: $0 create <username> <password>"
        return 1
    fi
    
    # 创建密码文件目录
    mkdir -p ./config
    
    # 添加用户 (如果文件不存在会自动创建)
    docker exec -it $DOCKER_CONTAINER mosquitto_passwd -b /mosquitto/config/passwd "$username" "$password"
    
    echo "用户 '$username' 创建成功!"
}

function delete_user() {
    local username=$1
    
    if [ -z "$username" ]; then
        echo "用法: $0 delete <username>"
        return 1
    fi
    
    docker exec -it $DOCKER_CONTAINER mosquitto_passwd -D /mosquitto/config/passwd "$username"
    
    echo "用户 '$username' 删除成功!"
}

function list_users() {
    if [ -f "$PASSWD_FILE" ]; then
        echo "当前用户列表:"
        cat "$PASSWD_FILE" | cut -d: -f1
    else
        echo "密码文件不存在"
    fi
}

function reload_config() {
    docker exec -it $DOCKER_CONTAINER mosquitto -c /mosquitto/config/mosquitto.conf
    echo "配置已重新加载!"
}

# 主菜单
case "$1" in
    create)
        create_user "$2" "$3"
        ;;
    delete)
        delete_user "$2"
        ;;
    list)
        list_users
        ;;
    reload)
        reload_config
        ;;
    *)
        echo "Mosquitto 用户管理工具"
        echo ""
        echo "用法:"
        echo "  $0 create <username> <password>  - 创建新用户"
        echo "  $0 delete <username>              - 删除用户"
        echo "  $0 list                           - 列出所有用户"
        echo "  $0 reload                         - 重新加载配置"
        echo ""
        echo "示例:"
        echo "  $0 create admin mypassword123"
        echo "  $0 delete testuser"
        ;;
esac