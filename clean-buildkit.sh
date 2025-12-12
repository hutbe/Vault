#!/bin/bash
# 清理 BuildKit 相关资源

echo "Cleaning BuildKit resources..."

# 停止所有 buildx 构建器容器
docker ps -a | grep buildkit | awk '{print $1}' | xargs docker stop 2>/dev/null || true

# 删除所有 buildx 构建器容器
docker ps -a | grep buildkit | awk '{print $1}' | xargs docker rm 2>/dev/null || true

# 删除 buildkit 镜像
docker images | grep buildkit | awk '{print $3}' | xargs docker rmi 2>/dev/null || true

# 清理构建缓存
docker builder prune -f

# 清理未使用的镜像
docker image prune -af

echo "Cleanup completed!"