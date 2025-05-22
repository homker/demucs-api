# Demucs音频分离系统部署指南

本文档提供了Demucs音频分离系统的详细部署说明。系统支持多种部署方式，包括Docker容器、Google Cloud Run和传统服务器部署。

## 前提条件

在部署之前，请确保满足以下要求：

### 所有部署方式通用
- 已安装Git
- 已克隆项目代码库
- 确保系统安装了FFmpeg（6.0或更高版本）
- Python 3.8+

### Docker部署
- 已安装Docker（推荐20.10.0或更高版本）
- Docker服务正在运行

### Google Cloud Run部署
- 已安装Google Cloud SDK
- 已配置gcloud命令行工具
- 拥有适当的GCP项目权限

### 传统服务器部署
- Python 3.8+
- 建议安装Supervisor进程管理器
- 足够的磁盘空间（建议至少10GB）

## 快速部署指南

我们提供了一个自动化部署脚本，可以简化部署过程。

### 脚本用法

```bash
./deploy [选项]
```

选项:
- `-h, --help`: 显示帮助信息
- `-e, --env ENV`: 设置环境（development/production），默认: production
- `-p, --platform PLATFORM`: 设置部署平台（docker/gcp/server），默认: docker
- `--port PORT`: 设置应用端口，默认: 8080
- `--project-id ID`: 设置GCP项目ID，默认: your-project-id
- `--service-name NAME`: 设置服务名称，默认: demucs-api
- `--region REGION`: 设置GCP区域，默认: us-central1

### 示例命令

```bash
# 使用Docker部署（默认）
./deploy

# 使用Docker部署开发环境，端口5001
./deploy -e development -p docker --port 5001

# 部署到Google Cloud Run
./deploy -p gcp --project-id my-project --service-name demucs-api

# 部署到传统服务器，端口5000
./deploy -p server --port 5000
```

## 详细部署步骤

### 1. Docker部署（推荐）

Docker部署是最简单和推荐的部署方式，可以确保一致的运行环境。

#### 手动部署步骤：

1. 构建Docker镜像
   ```bash
   docker build -t demucs-api:latest .
   ```

2. 运行容器
   ```bash
   docker run -d \
     --name demucs-api \
     -p 8080:8080 \
     -e PORT=8080 \
     -e FLASK_ENV=production \
     --restart unless-stopped \
     demucs-api:latest
   ```

3. 查看日志
   ```bash
   docker logs -f demucs-api
   ```

#### 使用Docker Compose部署

创建`docker-compose.yml`文件：

```yaml
version: '3'
services:
  demucs-api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
      - FLASK_ENV=production
    restart: unless-stopped
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
```

启动服务：
```bash
docker-compose up -d
```

### 2. Google Cloud Run部署

Cloud Run是一个无服务器平台，可以自动扩展以处理大量请求。

#### 手动部署步骤：

1. 设置环境变量
   ```bash
   export PROJECT_ID=your-project-id
   export SERVICE_NAME=demucs-api
   export REGION=us-central1
   ```

2. 构建并提交镜像
   ```bash
   gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
   ```

3. 部署到Cloud Run
   ```bash
   gcloud run deploy $SERVICE_NAME \
     --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
     --platform managed \
     --region $REGION \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --concurrency 10 \
     --timeout 1800 \
     --set-env-vars="FLASK_ENV=production" \
     --project $PROJECT_ID
   ```

### 3. 传统服务器部署

#### 手动部署步骤：

1. 创建虚拟环境
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

2. 安装依赖
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install gunicorn
   ```

3. 设置环境变量
   ```bash
   cp .env.example .env
   # 编辑.env文件设置合适的配置
   ```

4. 使用Supervisor管理进程（推荐）
   
   创建Supervisor配置文件`/etc/supervisor/conf.d/demucs.conf`：
   ```ini
   [program:demucs]
   command=/path/to/app/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 8 --timeout 0 run:app
   directory=/path/to/app
   user=yourusername
   autostart=true
   autorestart=true
   stopasgroup=true
   killasgroup=true
   environment=FLASK_ENV="production"
   stderr_logfile=/var/log/demucs/error.log
   stdout_logfile=/var/log/demucs/access.log
   ```

5. 创建日志目录并设置权限
   ```bash
   sudo mkdir -p /var/log/demucs
   sudo chown yourusername /var/log/demucs
   ```

6. 重新加载Supervisor配置
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start demucs
   ```

## 配置说明

可以通过环境变量或`.env`文件配置应用程序。主要配置项如下：

| 参数 | 说明 | 默认值 |
|-----|-----|-------|
| `DEBUG` | 调试模式 | False |
| `SECRET_KEY` | Flask密钥 | dev-key-12345 |
| `LOG_LEVEL` | 日志级别 | INFO |
| `ADMIN_TOKEN` | 管理员令牌 | admin-token-12345 |
| `UPLOAD_FOLDER` | 上传文件目录 | uploads |
| `OUTPUT_FOLDER` | 输出文件目录 | outputs |
| `MAX_CONTENT_LENGTH` | 最大上传文件大小 | 500MB |
| `FILE_RETENTION_MINUTES` | 文件保留时间 | 60 |
| `DEFAULT_MODEL` | 默认模型 | htdemucs |
| `SAMPLE_RATE` | 采样率 | 44100 |
| `CHANNELS` | 声道数 | 2 |
| `HOST` | 服务器主机 | 0.0.0.0 |
| `PORT` | 服务器端口 | 5000 |

## 生产环境建议

对于生产环境部署，建议遵循以下最佳实践：

1. **安全配置**：
   - 更改默认的`SECRET_KEY`和`ADMIN_TOKEN`
   - 设置`DEBUG=False`
   - 使用HTTPS保护应用程序
   - 配置适当的访问控制

2. **性能优化**：
   - 根据服务器硬件配置适当的工作进程数和线程数
   - 考虑使用nginx作为反向代理
   - 监控内存使用情况并适当调整

3. **扩展性**：
   - 考虑将上传的文件和处理结果存储在云存储（如AWS S3或Google Cloud Storage）
   - 对于高负载应用，考虑使用消息队列处理异步任务

4. **监控**：
   - 设置应用程序日志记录
   - 监控系统资源使用情况
   - 配置错误通知

## 故障排除

### 常见问题

1. **Docker容器无法启动**
   - 检查Docker是否正在运行
   - 查看容器日志：`docker logs demucs-api`
   - 确认端口没有被其他应用占用

2. **上传大文件失败**
   - 检查`MAX_CONTENT_LENGTH`设置
   - 检查Web服务器配置（如使用nginx代理）

3. **音频处理错误**
   - 检查FFmpeg是否正确安装
   - 验证支持的音频格式
   - 检查应用程序日志

4. **内存使用过高**
   - 减少并发处理的音频数量
   - 增加服务器内存或使用更多工作线程

### 日志位置

根据部署方式，日志位置有所不同：

- **Docker部署**：`docker logs demucs-api`
- **Cloud Run**：在Google Cloud Console的Cloud Run服务页面查看日志
- **传统服务器**：
  - 应用程序日志：`/var/log/demucs/access.log`和`/var/log/demucs/error.log`
  - 系统日志：`/var/log/syslog`（可能包含Supervisor相关信息）

## 更新应用程序

### Docker部署

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker build -t demucs-api:latest .

# 停止旧容器
docker stop demucs-api
docker rm demucs-api

# 启动新容器
docker run -d --name demucs-api -p 8080:8080 -e PORT=8080 demucs-api:latest
```

### 传统服务器部署

```bash
# 拉取最新代码
git pull

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启应用
sudo supervisorctl restart demucs
``` 