#!/bin/bash

# 初始化Demucs目录结构
echo "🔧 初始化Demucs目录结构..."

# 创建主要目录
mkdir -p /demucs/{uploads,outputs,models}

# 设置权限
chmod 755 /demucs
chmod 755 /demucs/{uploads,outputs,models}

# 创建测试目录
mkdir -p /demucs/{test_uploads,test_outputs}
chmod 755 /demucs/{test_uploads,test_outputs}

echo "✅ 目录结构初始化完成："
echo "   📁 /demucs/uploads - 上传目录"
echo "   📁 /demucs/outputs - 输出目录" 
echo "   📁 /demucs/models - 模型缓存目录"
echo "   📁 /demucs/test_uploads - 测试上传目录"
echo "   📁 /demucs/test_outputs - 测试输出目录"

# 显示目录状态
ls -la /demucs/ 