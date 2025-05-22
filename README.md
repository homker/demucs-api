# Demucs 音频分离系统

这是一个基于 [Demucs](https://github.com/facebookresearch/demucs) 的音频分离Web应用。该应用提供了一个简单易用的界面，允许用户上传音频文件并将其分离成不同的音轨（人声、鼓、贝斯、其他乐器等）。

![Demucs Audio Separator](docs/screenshot.png)

## 特性

- 💻 简洁现代的Web界面
- 🎵 支持多种音频格式 (MP3, WAV, FLAC, OGG, M4A)
- 🔊 支持多种分离模型 (htdemucs, htdemucs_ft, htdemucs_6s, mdx, mdx_q)
- 📊 实时处理进度显示
- 📱 响应式设计，适配移动设备
- 🌐 支持任意大小的音频文件
- 📂 输出为单独的音轨文件
- 🔄 支持拖放上传

## 安装

### 前提条件

- Python 3.8+
- FFmpeg
- Torch

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/demucs-webapp.git
cd demucs-webapp
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装 Demucs

```bash
pip install demucs
```

### 5. 配置环境变量

复制`.env.example`为`.env`并根据需要修改配置：

```bash
cp .env.example .env
```

### 6. 运行应用

```bash
python run.py
```

应用将在 http://localhost:5000 上运行。

## 使用方法

1. 访问Web界面 (默认 http://localhost:5000)
2. 上传音频文件（支持拖放）
3. 选择分离模型和需要提取的音轨
4. 点击"开始分离"按钮
5. 等待处理完成（可以实时查看进度）
6. 下载分离后的音轨

## API文档

### 获取可用模型

```
GET /api/models
```

响应示例:

```json
{
  "status": "success",
  "data": {
    "models": ["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx", "mdx_q"]
  }
}
```

### 处理音频文件

```
POST /api/process
Content-Type: multipart/form-data
```

参数:
- `file`: 音频文件 (必需)
- `model`: 模型名称 (可选，默认: htdemucs)
- `stems`: 要提取的音轨，逗号分隔 (可选，默认: vocals,drums,bass,other)

响应示例:

```json
{
  "status": "success",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Audio separation started",
    "status_url": "/api/status/550e8400-e29b-41d4-a716-446655440000",
    "progress_url": "/api/progress/550e8400-e29b-41d4-a716-446655440000",
    "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 获取任务状态

```
GET /api/status/<job_id>
```

响应示例:

```json
{
  "status": "success",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "progress": 65,
    "status": "processing",
    "message": "Separated drums using htdemucs"
  }
}
```

### 获取任务进度（SSE）

```
GET /api/progress/<job_id>
```

返回Server-Sent Events流，实时更新处理进度。

### 下载处理结果

```
GET /api/download/<job_id>
```

返回分离后的音轨ZIP文件。

### 清理任务文件

```
DELETE /api/cleanup/<job_id>
```

响应示例:

```json
{
  "status": "success",
  "data": {
    "message": "任务文件清理成功"
  }
}
```

### 管理接口：清理所有文件

```
POST /api/admin/cleanup
X-Admin-Token: <管理员令牌>
```

响应示例:

```json
{
  "status": "success",
  "data": {
    "message": "所有文件清理成功",
    "tasks_cleared": 5,
    "stats": {
      "uploads_deleted": 10,
      "outputs_deleted": 15,
      "separated_deleted": 20,
      "zip_files_deleted": 8
    }
  }
}
```

## 配置参数

可以通过环境变量或`.env`文件配置以下参数：

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

## 开发

### 项目结构

```
demucs-webapp/
├── app/                    # 应用代码
│   ├── __init__.py         # 应用初始化
│   ├── factory.py          # 应用工厂
│   ├── config.py           # 配置类
│   ├── routes/             # 路由模块
│   │   ├── __init__.py
│   │   ├── api.py          # API路由
│   │   └── main.py         # 主路由
│   ├── services/           # 服务层
│   │   ├── __init__.py
│   │   ├── audio_separator.py  # 音频分离服务
│   │   └── file_manager.py     # 文件管理服务
│   ├── utils/              # 工具函数
│   │   ├── __init__.py
│   │   ├── helpers.py      # 辅助函数
│   │   └── sse.py          # SSE支持
│   └── templates/          # 模板文件
│       └── index.html      # 主页模板
├── uploads/                # 上传文件目录
├── outputs/                # 输出文件目录
├── .env                    # 环境变量配置
├── .env.example            # 环境变量示例
├── requirements.txt        # 依赖列表
├── run.py                  # 应用入口
└── README.md               # 项目说明
```

## 贡献

欢迎贡献代码、报告问题或提出建议。请随时提交Pull Request或Issue。

## 许可

本项目基于MIT许可证开源 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [Demucs](https://github.com/facebookresearch/demucs) - Facebook AI Research开发的音频源分离模型
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [PyTorch](https://pytorch.org/) - 深度学习框架 