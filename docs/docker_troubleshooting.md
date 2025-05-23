# Docker构建故障排除指南

## 问题概述

之前遇到的Docker构建失败主要是由依赖版本冲突导致的：

```
ERROR: Cannot install -r requirements.txt (line 4) and werkzeug==2.0.3 because these package versions have conflicting dependencies.
The conflict is caused by:
    The user requested werkzeug==2.0.3
    flask 2.3.3 depends on Werkzeug>=2.3.7
```

## 解决方案

### 1. 修复依赖版本冲突

**问题**: Werkzeug版本冲突
- **原因**: Flask 2.3.3需要Werkzeug>=2.3.7，但requirements.txt指定了werkzeug==2.0.3
- **解决**: 更新requirements.txt中的版本

**问题**: PyTorch版本过时
- **原因**: torch==2.1.2不再可用
- **解决**: 升级到torch>=2.2.0

### 2. 优化的requirements.txt

```
torch>=2.2.0
torchaudio>=2.2.0
demucs>=4.0.0
flask>=2.3.0
flask-cors>=4.0.0
gunicorn>=21.0.0
python-dotenv>=1.0.0
requests>=2.31.0
sseclient-py>=1.7.0
numpy
werkzeug>=2.3.7
diffq
psutil>=5.9.0
```

### 3. Dockerfile优化

- 添加了DEBIAN_FRONTEND=noninteractive避免交互式安装
- 升级了pip、setuptools和wheel
- 添加了curl工具用于健康检查
- 改进了验证步骤

## 构建步骤

### 方法1: 使用构建脚本（推荐）

```bash
# 给脚本执行权限
chmod +x docker-build.sh

# 运行构建
./docker-build.sh
```

### 方法2: 手动构建

```bash
# 检查Docker是否运行
docker info

# 构建镜像
docker build --no-cache -t demucs-api:latest .

# 运行容器
docker run -d --name demucs-api -p 8080:8080 demucs-api:latest
```

## 常见问题和解决方案

### 1. Docker daemon未运行

**错误信息**:
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

**解决方案**:
- macOS: 启动Docker Desktop应用
- Linux: `sudo systemctl start docker`
- Windows: 启动Docker Desktop

### 2. 依赖冲突

**错误信息**:
```
ERROR: Cannot install ... because these package versions have conflicting dependencies
```

**解决方案**:
1. 检查requirements.txt中的版本约束
2. 使用>=而不是==来允许兼容版本
3. 运行`pip install --dry-run -r requirements.txt`测试

### 3. 构建上下文过大

**错误信息**:
```
Sending build context to Docker daemon  XXX MB
```

**解决方案**:
1. 检查.dockerignore文件
2. 排除不必要的文件（模型文件、上传文件等）
3. 清理临时文件

### 4. 内存不足

**错误信息**:
```
ERROR: failed to solve: process "/bin/sh -c pip install ..." did not complete successfully
```

**解决方案**:
1. 增加Docker Desktop的内存限制
2. 使用多阶段构建减少依赖安装压力
3. 分批安装依赖

### 5. FFmpeg安装失败

**错误信息**:
```
E: Unable to locate package ffmpeg
```

**解决方案**:
1. 更新包列表：`apt-get update`
2. 使用静态构建版本的FFmpeg
3. 检查网络连接

## 验证构建结果

### 1. 检查镜像

```bash
# 查看镜像列表
docker images

# 查看镜像详情
docker inspect demucs-api:latest
```

### 2. 测试运行

```bash
# 启动容器
docker run -d --name demucs-test -p 8080:8080 demucs-api:latest

# 检查容器状态
docker ps

# 查看日志
docker logs demucs-test

# 测试健康检查
curl http://localhost:8080/health

# 清理测试容器
docker stop demucs-test && docker rm demucs-test
```

### 3. 功能测试

```bash
# 测试API端点
curl http://localhost:8080/api/models

# 测试MCP端点
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## 部署建议

### 生产环境

```bash
# 使用特定标签
docker build -t demucs-api:v1.0.0 .

# 运行时设置环境变量
docker run -d \
  --name demucs-api \
  -p 8080:8080 \
  -e FLASK_ENV=production \
  -e BASE_URL="/demucs" \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  demucs-api:v1.0.0
```

### 开发环境

```bash
# 开发模式运行
docker run -d \
  --name demucs-dev \
  -p 8080:8080 \
  -e FLASK_ENV=development \
  -e DEBUG=true \
  -v $(pwd):/app \
  demucs-api:latest
```

## 性能优化

### 1. 多阶段构建

考虑使用多阶段构建减少最终镜像大小：

```dockerfile
# 构建阶段
FROM python:3.10-slim as builder
# ... 安装依赖和构建

# 运行阶段
FROM python:3.10-slim as runtime
# ... 只复制必要文件
```

### 2. 缓存优化

```bash
# 使用BuildKit提升构建速度
DOCKER_BUILDKIT=1 docker build -t demucs-api .
```

### 3. 资源限制

```bash
# 设置资源限制
docker run -d \
  --name demucs-api \
  --memory=4g \
  --cpus=2 \
  -p 8080:8080 \
  demucs-api:latest
``` 