#!/bin/bash

# 项目构建快捷脚本
# 这个脚本作为build目录下构建脚本的快捷入口

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"

echo "🚀 Demucs音频分离项目构建脚本"
echo "构建目录: $BUILD_DIR"
echo ""

# 显示可用选项
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "可用选项:"
    echo "  docker          构建Docker镜像"
    echo "  deploy          运行部署脚本"
    echo "  cleanup         清理临时文件"
    echo "  health          运行健康检查"
    echo "  help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 docker       # 构建Docker镜像"
    echo "  $0 deploy       # 部署应用"
    echo ""
}

# 执行对应的构建脚本
case "${1:-help}" in
    docker)
        echo "📦 构建Docker镜像..."
        cd "$BUILD_DIR"
        ./docker-build.sh "${@:2}"
        ;;
    deploy)
        echo "🚀 运行部署脚本..."
        cd "$BUILD_DIR"
        ./deploy "${@:2}"
        ;;
    cleanup)
        echo "🧹 清理临时文件..."
        cd "$BUILD_DIR"
        python3 cleanup_files.py "${@:2}"
        ;;
    health)
        echo "💊 运行健康检查..."
        cd "$BUILD_DIR"
        python3 healthcheck.py "${@:2}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ 未知选项: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 