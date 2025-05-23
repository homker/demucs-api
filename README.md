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
cp .env.example .env
# 根据需要编辑.env文件
```

3. **运行应用:**

```bash
python run.py
```

应用将在 http://localhost:8080 上运行。

### Docker安装 (推荐)

```bash
# 使用docker-compose
docker-compose up -d

# 或使用部署脚本
./deploy
```

## 🎯 使用方法

### 🌐 Web界面使用

1. 访问 **http://localhost:8080**
2. 上传音频文件（支持拖放）
3. 选择分离模型和需要提取的音轨
4. 点击"开始分离"按钮
5. 实时查看处理进度
6. 下载分离后的音轨

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

## 配置参数

可以通过环境变量或`.env`文件配置以下参数：

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `HOST` | 0.0.0.0 | 服务器绑定地址 |
| `PORT` | 8080 | 服务器端口 |
| `DEBUG` | False | 调试模式 |
| `MAX_CONTENT_LENGTH` | 100MB | 最大上传文件大小 |
| `UPLOAD_FOLDER` | uploads | 上传文件目录 |
| `OUTPUT_FOLDER` | outputs | 输出文件目录 |
| `ADMIN_TOKEN` | random | 管理员令牌 |
| `BASE_URL` | http://localhost:8080 | 基础URL |

## 目录结构

```
demucs/
├── app/                    # 主应用目录
│   ├── routes/            # 路由模块
│   │   ├── api.py         # REST API路由
│   │   ├── mcp.py         # MCP协议路由
│   │   └── main.py        # 主页路由
│   ├── services/          # 服务模块
│   │   ├── audio_separator.py  # 音频分离服务
│   │   ├── file_manager.py     # 文件管理服务
│   │   └── mcp_server.py       # MCP服务实现
│   ├── templates/         # HTML模板
│   │   ├── index.html     # 主页
│   │   └── mcp_test.html  # MCP测试页面
│   ├── static/            # 静态文件
│   ├── utils/             # 工具函数
│   ├── config.py          # 配置管理
│   └── factory.py         # 应用工厂
├── test/                   # 测试工具
│   └── mcp/               # MCP测试工具
│       ├── client.py      # 客户端测试工具
│       └── README.md      # 测试文档
├── docs/                   # 文档
├── uploads/               # 上传文件目录
├── outputs/               # 输出文件目录
├── requirements.txt       # Python依赖
├── Dockerfile            # Docker配置
├── docker-compose.yml    # Docker Compose配置
└── run.py                # 启动脚本
```

## 开发说明

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export FLASK_ENV=development
export DEBUG=True

# 启动应用
python run.py
```

### Docker开发

```bash
# 构建镜像
docker build -t demucs-webapp .

# 运行容器
docker run -p 8080:8080 demucs-webapp
```

## 故障排除

### FFmpeg问题

如果遇到FFmpeg相关错误，请确保安装了正确版本的FFmpeg：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# 检查版本
ffmpeg -version
```

### 内存不足

处理大文件时可能需要更多内存。可以通过以下方式优化：

1. 增加Docker容器内存限制
2. 使用分块处理
3. 选择较小的模型

### 权限问题

确保应用有读写上传和输出目录的权限：

```bash
chmod 755 uploads outputs
```

## 许可证

MIT License

## 贡献

欢迎提交Issues和Pull Requests！ 