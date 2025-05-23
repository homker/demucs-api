# 静态文件路径问题解决指南

## 🚨 问题描述

当访问 `http://127.0.0.1:8080/` 时，页面中的静态文件引用 `<script src="/static/js/mcp_sse_client.js"></script>` 会产生404错误。

## 🔍 原因分析

这个问题的根本原因是**Flask应用配置与访问路径不匹配**：

### 配置问题

之前的配置设置了：
```ini
BASE_URL=/demucs
APPLICATION_ROOT=/demucs
```

这意味着Flask应用期待在子路径 `/demucs` 下运行，即正确的访问地址应该是：
- ✅ **正确**: `http://127.0.0.1:8080/demucs/`
- ❌ **错误**: `http://127.0.0.1:8080/`

### 静态文件路径问题

当设置了 `APPLICATION_ROOT=/demucs` 时：
- Flask的 `url_for('static', filename='js/mcp_sse_client.js')` 会生成 `/demucs/static/js/mcp_sse_client.js`
- 但直接访问根路径时，浏览器请求的是 `/static/js/mcp_sse_client.js`，导致404错误

## ✅ 解决方案

### 方案1: 根路径访问（已修复）

**适用场景**: 本地开发、单独部署

```ini
# 根路径部署配置
BASE_URL=
APPLICATION_ROOT=
```

**访问地址**: `http://127.0.0.1:8080/`

### 方案2: 子路径访问

**适用场景**: 反向代理、多应用部署

```ini
# 子路径部署配置
BASE_URL=/demucs
APPLICATION_ROOT=/demucs
```

**访问地址**: `http://127.0.0.1:8080/demucs/`

## 🔧 配置切换

我们提供了便捷的配置切换脚本：

```bash
# 切换到本地开发模式（根路径）
./config_switch.sh local

# 切换到生产环境（子路径）
./config_switch.sh prod

# 查看所有可用配置
./config_switch.sh help
```

## 📁 配置文件说明

### config/.env.local
```ini
# 本地开发配置 - 根路径访问
BASE_URL=
APPLICATION_ROOT=
PORT=8080
DEBUG=true
```
**访问**: `http://127.0.0.1:8080/`

### config/.env.development
```ini
# 开发环境配置 - 根路径访问
BASE_URL=
APPLICATION_ROOT=
PORT=5000
DEBUG=true
```
**访问**: `http://127.0.0.1:5000/`

### config/.env.production
```ini
# 生产环境配置 - 子路径访问
BASE_URL=/demucs
APPLICATION_ROOT=/demucs
PORT=8080
DEBUG=false
```
**访问**: `http://域名:8080/demucs/`

## 🔍 验证方法

### 1. 检查当前配置
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('BASE_URL:', repr(os.getenv('BASE_URL'))); print('APPLICATION_ROOT:', repr(os.getenv('APPLICATION_ROOT')))"
```

### 2. 检查静态文件路径
在浏览器开发者工具中查看网络请求：
- **正确**: `/static/js/mcp_sse_client.js` (200)
- **子路径**: `/demucs/static/js/mcp_sse_client.js` (200)

### 3. 测试API端点
```bash
# 根路径部署
curl http://127.0.0.1:8080/api/models

# 子路径部署
curl http://127.0.0.1:8080/demucs/api/models
```

## 🌐 反向代理配置

### Nginx 根路径配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Nginx 子路径配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /demucs/ {
        proxy_pass http://127.0.0.1:8080/demucs/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 常见问题

### 问题1: 静态文件404
**症状**: 页面加载但CSS/JS文件404
**原因**: 配置路径与访问路径不匹配
**解决**: 使用正确的配置或访问正确的路径

### 问题2: API调用失败
**症状**: JavaScript中API调用失败
**原因**: API基础路径配置错误
**解决**: 检查模板中的`base_url`变量传递

### 问题3: MCP端点无法访问
**症状**: MCP客户端连接失败
**原因**: MCP端点路径错误
**解决**: 
- 根路径: `http://127.0.0.1:8080/mcp`
- 子路径: `http://127.0.0.1:8080/demucs/mcp`

## 📊 决策指南

### 选择根路径部署 (BASE_URL="")
- ✅ 简单直观
- ✅ 本地开发友好
- ✅ 单应用部署
- ❌ 不适合多应用环境

### 选择子路径部署 (BASE_URL="/demucs")
- ✅ 支持多应用
- ✅ 反向代理友好
- ✅ 企业部署标准
- ❌ 配置稍复杂

## 🔄 迁移步骤

### 从子路径切换到根路径
```bash
# 1. 切换配置
./config_switch.sh local

# 2. 重启应用
python run.py

# 3. 访问新地址
open http://127.0.0.1:8080/
```

### 从根路径切换到子路径
```bash
# 1. 切换配置
./config_switch.sh prod

# 2. 重启应用
python run.py

# 3. 访问新地址
open http://127.0.0.1:8080/demucs/
```

通过正确的配置管理，可以避免静态文件路径问题，确保应用在不同部署环境下都能正常工作。 