# Demucs API 服务

基于 Demucs 的音频源分离 API 服务，可将混合音频分离为人声、鼓点、贝斯和其他乐器等不同音轨。

## 项目结构

重构后的项目采用模块化设计，结构如下：

```
demucs-api/
├── app/                         # 应用目录
│   ├── __init__.py              # 应用工厂函数
│   ├── config.py                # 配置管理
│   ├── routes/                  # 路由模块
│   │   ├── __init__.py          # 路由注册
│   │   ├── main.py              # 主路由（首页、健康检查）
│   │   └── api.py               # API路由（分离音频、清理文件）
│   ├── services/                # 服务模块
│   │   ├── __init__.py          # 服务初始化
│   │   ├── audio_separator.py   # 音频分离服务
│   │   └── file_manager.py      # 文件管理服务
│   ├── utils/                   # 工具模块
│   │   ├── __init__.py          # 工具初始化
│   │   └── helpers.py           # 辅助函数
│   └── templates/               # 模板目录（未使用）
├── uploads/                     # 上传文件目录
├── outputs/                     # 输出文件目录
├── separated/                   # 分离音频目录
├── .gitignore                   # Git忽略文件
├── .dockerignore                # Docker忽略文件
├── Dockerfile                   # Docker构建文件
├── README.md                    # 项目说明
├── requirements.txt             # 依赖列表
└── run.py                       # 应用入口
```

## 设计模式

此重构采用了以下设计模式和最佳实践：

1. **工厂模式**：使用应用工厂创建Flask应用，便于测试和配置管理
2. **依赖注入**：通过初始化服务并注入到应用中
3. **单一职责原则**：每个模块专注于特定功能
4. **蓝图**：使用Flask蓝图分离不同的API路由
5. **面向对象设计**：使用类封装相关功能和状态
6. **配置模式**：使用类层次结构管理不同环境的配置

## 安装与运行

### 本地运行

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 运行应用：

```bash
python run.py
```

应用将在 http://localhost:5000 上运行。

### Docker部署

1. 构建Docker镜像：

```bash
docker build -t demucs-api .
```

2. 运行容器：

```bash
docker run -p 8080:8080 demucs-api
```

应用将在 http://localhost:8080 上运行。

## API接口

### 1. 音频分离API

```
POST /api/separate
Content-Type: multipart/form-data
```

**请求参数**：

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| file | 文件 | 是 | 要上传的音频文件 (支持 mp3, wav, flac 等格式) |
| model | 字符串 | 否 | 使用的模型名称 (默认: htdemucs) |
| two_stems | 字符串 | 否 | 仅分离为两个音轨 (vocals, drums, bass, other) |
| segment | 整数 | 否 | 分段长度 (htdemucs模型默认7秒，其他模型默认10秒) |
| mp3 | 布尔值 | 否 | 是否输出MP3格式 (默认: false，输出WAV格式) |
| mp3_bitrate | 整数 | 否 | MP3比特率 (默认: 320) |

**响应**：
成功时返回ZIP文件，包含分离后的各个音轨。响应头中包含 `X-Cleanup-ID` 字段，可用于后续调用清理API。

### 2. 健康检查API

```
GET /api/health
```

**响应**：
```json
{
  "status": "success",
  "message": "服务正常运行"
}
```

### 3. 文件清理API

```
DELETE /api/cleanup/{cleanup_id}
```

**请求参数**：

| 参数名 | 类型 | 位置 | 说明 |
|--------|------|------|------|
| cleanup_id | 字符串 | URL路径 | 要清理的任务ID |

**响应**：
```json
{
  "status": "success",
  "message": "文件清理成功"
}
```

## 配置说明

可通过环境变量配置应用：

- `FLASK_ENV`: 运行环境 (development, testing, production)
- `PORT`: 服务端口
- `UPLOAD_FOLDER`: 上传文件目录
- `OUTPUT_FOLDER`: 输出文件目录
- `FILE_RETENTION_MINUTES`: 临时文件保留时间（分钟）

## 支持的模型

- `htdemucs`: Hybrid Transformer Demucs，最新的混合架构模型（默认）
- `htdemucs_ft`: htdemucs的微调版本，更准确但处理速度更慢
- `htdemucs_6s`: 6音轨版本，增加了钢琴和吉他音轨
- `mdx`: 仅在MusDB HQ上训练的模型，性能适中
- `mdx_q`: mdx的量化版本，处理速度更快 