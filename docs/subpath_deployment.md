# 子路径部署配置指南

## 概述

本文档介绍如何将Demucs音频分离应用部署在子路径下，例如 `https://yourdomain.com/demucs/`。

## 配置说明

### 环境变量配置

要将应用部署在子路径下，需要设置以下环境变量：

```bash
# 基础URL路径（前端JavaScript使用）
BASE_URL=/demucs

# Flask应用根路径（Flask内部路由使用）
APPLICATION_ROOT=/demucs
```

### 配置文件示例

**方法1: 环境变量**
```bash
export BASE_URL="/demucs"
export APPLICATION_ROOT="/demucs"
python run.py
```

**方法2: .env文件**
```ini
# .env
BASE_URL=/demucs
APPLICATION_ROOT=/demucs
PORT=8080
FLASK_ENV=production
DEBUG=False
```

**方法3: Docker环境变量**
```bash
docker run -d \
  --name demucs-api \
  -p 8080:8080 \
  -e BASE_URL="/demucs" \
  -e APPLICATION_ROOT="/demucs" \
  -e PORT=8080 \
  demucs-api:latest
```

## URL映射

配置 `BASE_URL=/demucs` 后，应用的URL映射如下：

| 功能 | 相对路径 | 完整URL示例 |
|------|----------|-------------|
| 主页 | `/demucs/` | `https://yourdomain.com/demucs/` |
| API端点 | `/demucs/api/*` | `https://yourdomain.com/demucs/api/models` |
| MCP端点 | `/demucs/mcp` | `https://yourdomain.com/demucs/mcp` |
| MCP流 | `/demucs/mcp/stream/{job_id}` | `https://yourdomain.com/demucs/mcp/stream/123` |
| 静态文件 | `/demucs/static/*` | `https://yourdomain.com/demucs/static/js/mcp_sse_client.js` |
| 健康检查 | `/demucs/health` | `https://yourdomain.com/demucs/health` |
| MCP测试 | `/demucs/test/mcp` | `https://yourdomain.com/demucs/test/mcp` |

## 反向代理配置

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 子路径代理
    location /demucs/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 支持SSE连接
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

### Apache配置示例

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    
    # 子路径代理
    ProxyPreserveHost On
    ProxyPass /demucs/ http://localhost:8080/
    ProxyPassReverse /demucs/ http://localhost:8080/
    
    # 支持SSE连接
    ProxyPassMatch ^/demucs/(.*)$ http://localhost:8080/$1
</VirtualHost>
```

## 验证部署

运行以下命令验证子路径部署是否正确配置：

```bash
# 运行验证测试
python test_subpath_deployment.py
```

或手动检查关键端点：

```bash
# 检查主页
curl https://yourdomain.com/demucs/

# 检查API
curl https://yourdomain.com/demucs/api/models

# 检查MCP端点
curl -X POST https://yourdomain.com/demucs/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# 检查健康状态
curl https://yourdomain.com/demucs/health
```

## 常见问题

### 1. 静态文件404错误

**问题**: 静态文件无法加载，出现404错误

**解决方案**: 
- 确保设置了 `APPLICATION_ROOT` 环境变量
- 检查反向代理配置是否正确转发静态文件请求

### 2. API请求路径错误

**问题**: 前端API请求路径不正确

**解决方案**:
- 确保设置了 `BASE_URL` 环境变量
- 检查JavaScript中 `BASE_URL` 是否正确设置

### 3. SSE连接失败

**问题**: 实时进度更新不工作

**解决方案**:
- 检查反向代理是否支持SSE连接
- 确保禁用了代理缓存和缓冲

### 4. MCP客户端连接失败

**问题**: MCP客户端无法连接到服务器

**解决方案**:
- 使用完整的MCP端点URL: `https://yourdomain.com/demucs/mcp`
- 确保网络防火墙允许相关端口

## 最佳实践

1. **环境变量管理**: 使用 `.env` 文件管理配置，避免硬编码
2. **HTTPS配置**: 生产环境建议使用HTTPS
3. **监控日志**: 定期检查应用和代理服务器日志
4. **性能优化**: 配置适当的缓存策略（静态文件）
5. **安全配置**: 设置适当的安全头和访问控制

## 部署检查清单

- [ ] 设置 `BASE_URL` 环境变量
- [ ] 设置 `APPLICATION_ROOT` 环境变量  
- [ ] 配置反向代理规则
- [ ] 测试主页访问
- [ ] 测试API端点
- [ ] 测试MCP功能
- [ ] 测试静态文件加载
- [ ] 测试SSE连接
- [ ] 运行自动化测试
- [ ] 检查日志输出 