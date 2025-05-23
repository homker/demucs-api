# .env配置文件指南

## 概述

项目使用`.env`文件来管理环境变量配置。不同的部署环境应该使用相应的配置文件。

## 文件结构

```
.env                  # 主配置文件（不提交到git）
.env.example         # 示例配置文件（模板）
.env.development     # 开发环境配置
.env.production      # 生产环境配置
```

## 配置文件说明

### 🔧 基础配置

#### Flask环境设置
```ini
DEBUG=false                # 是否启用调试模式（生产环境必须为false）
LOG_LEVEL=INFO            # 日志级别：DEBUG, INFO, WARNING, ERROR
FLASK_ENV=production      # Flask环境：development, production, testing
```

#### 服务器设置
```ini
HOST=0.0.0.0             # 服务器绑定地址
PORT=8080                # 服务器端口号
```

#### API基础路径设置
```ini
BASE_URL=/demucs         # API基础路径（子路径部署时使用）
APPLICATION_ROOT=/demucs # Flask应用根路径
```

⚠️ **重要说明**：
- 对于根路径部署，`BASE_URL`和`APPLICATION_ROOT`应该为空字符串或不设置
- 对于子路径部署（如 `/demucs`），两个值应该相同

### 🔐 安全配置

```ini
SECRET_KEY=your-secret-key-change-this      # Flask会话密钥（生产环境必须更改）
ADMIN_TOKEN=your-admin-token-change-this    # 管理员API令牌
```

⚠️ **安全提醒**：
- 生产环境中必须使用强密码
- 不要在代码中暴露真实的密钥
- 定期更换密钥

### 📁 文件存储设置

```ini
UPLOAD_FOLDER=uploads                # 上传文件存储目录
OUTPUT_FOLDER=outputs               # 输出文件存储目录
MAX_CONTENT_LENGTH=524288000        # 最大上传文件大小（字节）
FILE_RETENTION_MINUTES=60           # 文件保留时间（分钟）
```

### 🎵 音频处理设置

```ini
DEFAULT_MODEL=htdemucs              # 默认音频分离模型
SAMPLE_RATE=44100                   # 音频采样率
CHANNELS=2                          # 音频声道数
```

## 环境配置示例

### 开发环境（.env.development）

```ini
# Flask环境设置
DEBUG=true
LOG_LEVEL=DEBUG
FLASK_ENV=development

# 服务器设置
HOST=0.0.0.0
PORT=5000

# API基础路径（开发环境通常为根路径）
BASE_URL=
APPLICATION_ROOT=

# 默认模型
DEFAULT_MODEL=htdemucs

# 基本设置
SECRET_KEY=dev-key-12345

# 安全设置
ADMIN_TOKEN=admin-token-12345

# 文件存储设置
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
MAX_CONTENT_LENGTH=524288000

# 文件管理设置
FILE_RETENTION_MINUTES=60

# 音频处理设置
SAMPLE_RATE=44100
CHANNELS=2
```

### 生产环境（.env.production）

```ini
# Flask环境设置
DEBUG=false
LOG_LEVEL=INFO
FLASK_ENV=production

# 服务器设置
HOST=0.0.0.0
PORT=8080

# API基础路径
BASE_URL=/demucs
APPLICATION_ROOT=/demucs

# 默认模型
DEFAULT_MODEL=htdemucs

# 基本设置
SECRET_KEY=production-secret-key-change-this

# 安全设置
ADMIN_TOKEN=production-admin-token-change-this

# 文件存储设置
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
MAX_CONTENT_LENGTH=524288000

# 文件管理设置
FILE_RETENTION_MINUTES=60

# 音频处理设置
SAMPLE_RATE=44100
CHANNELS=2
```

## 使用方法

### 方法1: 复制示例文件

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
nano .env
```

### 方法2: 选择环境配置

```bash
# 使用开发环境配置
cp .env.development .env

# 使用生产环境配置
cp .env.production .env
```

### 方法3: Docker环境变量

```bash
# 通过Docker环境变量覆盖
docker run -d \
  --name demucs-api \
  -p 8080:8080 \
  -e DEBUG=false \
  -e BASE_URL="/demucs" \
  -e APPLICATION_ROOT="/demucs" \
  -e SECRET_KEY="your-strong-secret-key" \
  demucs-api:latest
```

## 常见问题

### ❌ 问题1: 静态文件404错误

**原因**: `BASE_URL`和`APPLICATION_ROOT`配置不一致

**解决方案**:
```ini
# 确保两者相同
BASE_URL=/demucs
APPLICATION_ROOT=/demucs
```

### ❌ 问题2: API请求路径错误

**原因**: 前端JavaScript的BASE_URL与后端配置不匹配

**解决方案**: 检查模板中的BASE_URL传递是否正确

### ❌ 问题3: 生产环境仍显示调试信息

**原因**: 生产环境配置错误

**解决方案**:
```ini
# 生产环境必须设置
DEBUG=false
FLASK_ENV=production
LOG_LEVEL=INFO
```

## 安全最佳实践

### 1. 密钥管理

```bash
# 生成强密钥
python -c "import secrets; print(secrets.token_hex(32))"

# 使用环境变量而不是硬编码
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

### 2. 文件权限

```bash
# 设置正确的文件权限
chmod 600 .env
```

### 3. Git配置

```bash
# 确保.env文件不被提交
echo ".env" >> .gitignore
```

## 验证配置

### 运行配置测试

```bash
# 测试配置加载
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('BASE_URL:', repr(os.getenv('BASE_URL')))
print('APPLICATION_ROOT:', repr(os.getenv('APPLICATION_ROOT')))
print('DEBUG:', os.getenv('DEBUG'))
print('FLASK_ENV:', os.getenv('FLASK_ENV'))
"
```

### 检查配置一致性

```bash
# 运行子路径部署测试
python test_subpath_deployment.py
```

## 故障排除

如果遇到配置问题：

1. **检查文件存在**: 确保`.env`文件存在且可读
2. **检查语法**: 确保没有多余的空格或引号
3. **检查加载顺序**: 环境变量会覆盖.env文件中的值
4. **检查权限**: 确保应用有读取.env文件的权限

## 参考资源

- [python-dotenv文档](https://python-dotenv.readthedocs.io/)
- [Flask配置文档](https://flask.palletsprojects.com/en/2.3.x/config/)
- [Docker环境变量指南](https://docs.docker.com/compose/environment-variables/) 