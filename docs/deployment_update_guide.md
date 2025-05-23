# 部署更新指南 - 修复静态文件路径问题

## 问题描述

根据[whisper.ai.levelinfinite.com/demucs](https://whisper.ai.levelinfinite.com/demucs/#mcp-info)的检查结果，发现以下问题：

1. `<script src="/static/js/mcp_sse_client.js"></script>` 路径错误
2. 在子路径部署(`/demucs`)时，静态文件路径缺少基础路径前缀
3. `.env`配置文件存在多个问题

## 已修复的问题

我们已经在本地代码中修复了以下问题：

### ✅ 1. 修复MCP测试页面的API_BASE配置

**文件**: `app/templates/mcp_test.html`

**修复前**:
```javascript
const API_BASE = '{{ base_url }}' || window.location.origin;
```

**修复后**:
```javascript
const API_BASE = "{{ base_url }}" || window.location.origin;
```

### ✅ 2. 已确认静态文件引用正确

**文件**: `app/templates/index.html`

**正确使用**:
```html
<script src="{{ url_for('static', filename='js/mcp_sse_client.js') }}"></script>
```

### ✅ 3. 修复.env配置文件问题

#### 问题分析：

1. **`.env.production` 配置错误**：
   - `DEBUG=true` 应该为 `DEBUG=false`
   - `FLASK_ENV=development` 应该为 `FLASK_ENV=production`
   - 使用开发密钥而非生产密钥

2. **`.env.example` 缺失关键配置**：
   - 缺少 `BASE_URL` 和 `APPLICATION_ROOT` 配置项
   - 缺少 `FLASK_ENV` 设置

3. **`.env.development` 配置不完整**：
   - 缺少 `APPLICATION_ROOT` 配置

#### 修复后的配置：

**正确的生产环境配置 (`.env`)**:
```ini
# Flask环境设置
DEBUG=false
LOG_LEVEL=INFO
FLASK_ENV=production

# 服务器设置
HOST=0.0.0.0
PORT=8080

# API基础路径设置（子路径部署）
BASE_URL=/demucs
APPLICATION_ROOT=/demucs

# 默认模型
DEFAULT_MODEL=htdemucs

# 基本设置
SECRET_KEY=your-secret-key-change-this

# 安全设置
ADMIN_TOKEN=your-admin-token-change-this

# 文件存储设置
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
MAX_CONTENT_LENGTH=524288000  # 500MB

# 文件管理设置
FILE_RETENTION_MINUTES=60

# 音频处理设置
SAMPLE_RATE=44100
CHANNELS=2
```

### ✅ 4. Docker构建问题修复

**文件**: `requirements.txt`

**修复**: 
- 更新 `werkzeug>=2.3.7` 解决版本冲突
- 更新 `torch>=2.2.0` 和 `torchaudio>=2.2.0` 使用最新版本

## 部署更新步骤

### 方法1: 重新构建和部署（推荐）

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 构建新的Docker镜像
./docker-build.sh v1.1.0

# 3. 停止当前容器
docker stop demucs-api

# 4. 移除旧容器
docker rm demucs-api

# 5. 运行新容器
docker run -d \
  --name demucs-api \
  -p 8080:8080 \
  -e BASE_URL="/demucs" \
  -e APPLICATION_ROOT="/demucs" \
  -e FLASK_ENV=production \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  demucs-api:v1.1.0
```

### 方法2: 热更新（如果可能）

```bash
# 1. 仅更新模板文件
docker cp app/templates/mcp_test.html demucs-api:/app/app/templates/

# 2. 重启容器使更改生效
docker restart demucs-api
```

### 方法3: Kubernetes部署更新

如果使用Kubernetes，更新deployment：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demucs-api
spec:
  template:
    spec:
      containers:
      - name: demucs-api
        image: demucs-api:v1.1.0  # 更新镜像版本
        env:
        - name: BASE_URL
          value: "/demucs"
        - name: APPLICATION_ROOT
          value: "/demucs"
```

## 验证修复结果

### 1. 检查静态文件加载

访问：`https://whisper.ai.levelinfinite.com/demucs/`

在浏览器开发者工具中检查：
- 静态文件请求是否正确：`/demucs/static/js/mcp_sse_client.js`
- 没有404错误

### 2. 测试API端点

```bash
# 检查模型API
curl https://whisper.ai.levelinfinite.com/demucs/api/models

# 检查MCP端点
curl -X POST https://whisper.ai.levelinfinite.com/demucs/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# 检查健康状态
curl https://whisper.ai.levelinfinite.com/demucs/health
```

### 3. 测试MCP测试页面

访问：`https://whisper.ai.levelinfinite.com/demucs/test/mcp`

检查：
- 页面正常加载
- JavaScript控制台无错误
- API_BASE正确设置为 `/demucs`

## 故障排除

### 问题1: 静态文件仍然404

**可能原因**: 浏览器缓存

**解决方案**:
```bash
# 强制刷新浏览器缓存
# Chrome/Firefox: Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)

# 或清理浏览器缓存
```

### 问题2: API请求失败

**可能原因**: 反向代理配置问题

**解决方案**: 检查Nginx/Apache配置
```nginx
location /demucs/ {
    proxy_pass http://localhost:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 问题3: Docker构建失败

**可能原因**: 依赖版本冲突

**解决方案**: 使用我们优化的依赖版本
```bash
# 清理Docker缓存
docker system prune -a

# 重新构建
./docker-build.sh
```

## 回滚计划

如果更新出现问题，可以快速回滚：

```bash
# 回滚到之前的版本
docker stop demucs-api
docker rm demucs-api
docker run -d \
  --name demucs-api \
  -p 8080:8080 \
  -e BASE_URL="/demucs" \
  -e APPLICATION_ROOT="/demucs" \
  demucs-api:previous-version
```

## 更新验证清单

- [ ] 静态文件路径正确 (`/demucs/static/js/mcp_sse_client.js`)
- [ ] API端点正常工作
- [ ] MCP端点响应正常
- [ ] MCP测试页面功能正常
- [ ] 健康检查通过
- [ ] 浏览器控制台无错误
- [ ] SSE连接正常工作
- [ ] 音频分离功能正常

## 监控和日志

更新后，建议监控以下指标：

```bash
# 检查容器日志
docker logs -f demucs-api

# 检查容器资源使用
docker stats demucs-api

# 检查磁盘空间
df -h
```

## 联系支持

如果在更新过程中遇到问题，可以：

1. 查看详细错误日志
2. 参考 [Docker故障排除指南](docker_troubleshooting.md)
3. 参考 [子路径部署指南](subpath_deployment.md) 