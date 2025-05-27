# Demucs 音频分离系统 + 标准MCP服务器

这是一个基于 [Demucs](https://github.com/facebookresearch/demucs) 的音频分离Web应用，现在完全支持标准 **MCP (Model Context Protocol)** 协议。该应用提供了简单易用的Web界面和符合JSON-RPC 2.0规范的MCP服务器，可与Claude Desktop、Cursor等MCP客户端无缝集成。

![Demucs Audio Separator](docs/screenshot.png)

## ✨ 主要特性

### 🎵 音频分离功能
- 💻 简洁现代的Web界面
- 🎵 支持多种音频格式 (MP3, WAV, FLAC, OGG, M4A)
- 🔊 支持多种分离模型 (htdemucs, htdemucs_ft, htdemucs_6s, mdx, mdx_q)
- 📊 实时处理进度显示
- 📱 响应式设计，适配移动设备
- 🌐 支持任意大小的音频文件
- 📂 输出为单独的音轨文件
- 🔄 支持拖放上传

### 🔗 标准MCP协议支持
- ✅ **JSON-RPC 2.0** - 完全符合MCP官方协议规范
- ✅ **单一端点通信** - 标准`/mcp`端点，便于客户端集成
- ✅ **工具调用系统** - 支持音频分离、模型查询、状态查询等工具
- ✅ **资源管理** - 提供API文档和模型信息资源
- ✅ **SSE流式输出** - 实时进度更新（MCP协议扩展）
- ✅ **多客户端兼容** - 可与Claude Desktop、Cursor等MCP工具连接
- 🧪 **内置测试界面** - 完整的MCP功能测试工具

## 🚀 快速开始

### 前提条件

- Python 3.8+
- FFmpeg 6.0+
- Torch

### 安装步骤

1. **克隆仓库并安装依赖:**

```bash
git clone https://github.com/yourusername/demucs-webapp.git
cd demucs-webapp
pip install -r requirements.txt
```

2. **设置环境变量:**

```bash
# 选择适合的配置模板
cp config/.env.production .env    # 生产环境
# 或
cp config/.env.development .env   # 开发环境

# 根据需要编辑.env文件
```

3. **运行应用:**

```bash
python run.py
```

应用将在 http://localhost:8080 上运行。

### Docker安装 (推荐)

```bash
# 使用docker-compose（推荐，自动挂载目录）
docker-compose up -d

# 或使用快捷构建脚本
./build.sh docker

# 或使用部署脚本
./build.sh deploy
```

#### 目录挂载说明

系统使用 `/demucs` 作为容器内的工作目录，并支持以下目录的外部挂载：

- **上传目录**: `/demucs/uploads` - 存放待处理的音频文件
- **输出目录**: `/demucs/outputs` - 存放分离后的音频文件  
- **模型目录**: `/demucs/models` - 存放Demucs模型缓存

使用docker-compose时，这些目录会自动挂载到本地的 `./data/` 目录下：

```bash
mkdir -p data/{uploads,outputs,models}
docker-compose up -d
```

手动运行Docker容器时，建议挂载这些目录：

```bash
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/data/uploads:/demucs/uploads \
  -v $(pwd)/data/outputs:/demucs/outputs \
  -v $(pwd)/data/models:/demucs/models \
  demucs-webapp
```

## 🎯 使用方法

### 🌐 Web界面使用

1. **音频分离**：访问 **http://localhost:8080**
   - 上传音频文件（支持拖放）
   - 选择分离模型和需要提取的音轨
   - 点击"开始分离"按钮
   - 实时查看处理进度
   - 下载分离后的音轨

2. **管理面板**：访问 **http://localhost:8080/admin**
   - 用户名：`admin`，密码：`admin123`
   - 查看所有任务和文件统计
   - 点击"📋 详情"查看任务完整信息
   - 管理文件和清理过期数据

### 🔌 MCP客户端集成

在任何支持MCP的客户端中配置：

```
MCP服务器端点: http://localhost:8080/mcp
协议: JSON-RPC 2.0 over HTTP
方法: POST
Content-Type: application/json
```

### 🧪 MCP测试界面

访问 **http://localhost:8080/test/mcp** 进行MCP功能测试：

- 🔍 查看服务器能力和可用工具
- 🎵 测试音频分离工具调用
- 📊 监听SSE流式进度更新
- 📚 获取模型信息和资源

## 📋 MCP协议使用示例

### 初始化连接
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "1.0",
    "capabilities": {},
    "clientInfo": {
      "name": "your-client-name",
      "version": "1.0.0"
    }
  }
}
```

### 调用音频分离工具
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "separate_audio",
    "arguments": {
      "file_path": "/path/to/audio.mp3",
      "model": "htdemucs",
      "stems": ["vocals", "drums"],
      "stream_progress": true
    }
  }
}
```

### 监听实时进度
```
GET http://localhost:8080/mcp/stream/{job_id}
Content-Type: text/event-stream
```

## 🛠️ 可用的MCP工具

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `separate_audio` | 音频分离 | `file_path`, `model`, `stems`, `stream_progress` |
| `get_models` | 获取可用模型 | 无 |
| `get_job_status` | 查询任务状态 | `job_id` |

## 📚 可用的MCP资源

| 资源URI | 名称 | 描述 |
|---------|------|------|
| `demucs://docs/api` | API文档 | 完整的API使用文档 |
| `demucs://models/info` | 模型信息 | 详细的模型参数和特性 |

## ⚙️ 构建和部署

### 快捷构建脚本

```bash
# 查看可用选项
./build.sh help

# 构建Docker镜像
./build.sh docker

# 运行部署
./build.sh deploy

# 清理临时文件
./build.sh cleanup

# 健康检查
./build.sh health
```

### 配置管理

```bash
# 开发环境
cp config/.env.development .env

# 生产环境
cp config/.env.production .env

# 自定义配置
cp config/.env.example .env
```

## 📁 项目结构

```
demucs/
├── README.md                    # 项目说明
├── build.sh                     # 构建快捷脚本
├── .env                         # 配置文件（不提交）
├── requirements.txt             # Python依赖
├── run.py                       # 应用启动入口
│
├── app/                         # 应用主代码
│   ├── routes/                 # 路由模块
│   ├── services/               # 业务逻辑
│   ├── templates/              # HTML模板
│   └── static/                 # 静态资源
│
├── build/                       # 构建和部署
│   ├── docker-build.sh        # Docker构建
│   ├── Dockerfile              # Docker镜像
│   ├── deploy                  # 部署脚本
│   └── ...                     # 其他构建工具
│
├── config/                      # 配置模板
│   ├── .env.example           # 配置模板
│   ├── .env.development       # 开发环境
│   └── .env.production        # 生产环境
│
├── docs/                        # 项目文档
│   ├── deployment.md          # 部署指南
│   ├── env_configuration_guide.md # 配置指南
│   └── ...                     # 其他文档
│
├── uploads/                     # 上传文件
├── outputs/                     # 输出文件
└── logs/                       # 日志文件
```

详细的项目结构说明请参考：[docs/project_structure.md](docs/project_structure.md)

## 📖 文档

- 📘 [项目结构说明](docs/project_structure.md)
- 🚀 [部署指南](docs/deployment.md)  
- 🔧 [环境配置指南](docs/env_configuration_guide.md)
- 🐳 [Docker故障排除](docs/docker_troubleshooting.md)
- 🌐 [子路径部署](docs/subpath_deployment.md)
- 🔄 [部署更新指南](docs/deployment_update_guide.md)

## 配置参数

可以通过环境变量或`.env`文件配置以下参数：

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `HOST` | 0.0.0.0 | 服务器绑定地址 |
| `PORT` | 8080 | 服务器端口 |
| `DEBUG` | False | 调试模式 |
| `BASE_URL` | '' | API基础路径（子路径部署时使用） |
| `APPLICATION_ROOT` | '' | Flask应用根路径 |
| `MAX_CONTENT_LENGTH` | 500MB | 最大上传文件大小 |
| `UPLOAD_FOLDER` | uploads | 上传文件目录 |
| `OUTPUT_FOLDER` | outputs | 输出文件目录 |
| `ADMIN_TOKEN` | random | 管理员令牌 |

详细配置说明请参考：[docs/env_configuration_guide.md](docs/env_configuration_guide.md) 