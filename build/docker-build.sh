#!/bin/bash

# Docker构建脚本
set -e

echo "🐳 开始构建Demucs音频分离Docker镜像..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon未运行，请先启动Docker Desktop"
    exit 1
fi

# 设置项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "📁 项目根目录: $PROJECT_ROOT"

# 设置镜像名称和标签
IMAGE_NAME="demucs-api"
TAG=${1:-latest}
FULL_NAME="$IMAGE_NAME:$TAG"

echo "📦 镜像名称: $FULL_NAME"

# 构建镜像（从项目根目录构建，使用build目录下的Dockerfile）
echo "🔨 开始构建..."
cd "$PROJECT_ROOT"
docker build --no-cache -f build/Dockerfile -t "$FULL_NAME" .

if [ $? -eq 0 ]; then
    echo "✅ 构建成功！"
    echo ""
    echo "🚀 运行容器命令："
    echo "  docker run -d --name demucs-api -p 8080:8080 $FULL_NAME"
    echo ""
    echo "🌐 访问地址："
    echo "  http://localhost:8080"
    echo ""
    echo "🔍 其他常用命令："
    echo "  查看镜像大小: docker images $FULL_NAME"
    echo "  查看容器日志: docker logs demucs-api"
    echo "  停止容器: docker stop demucs-api"
    echo "  删除容器: docker rm demucs-api"
else
    echo "❌ 构建失败！"
    exit 1
fi 