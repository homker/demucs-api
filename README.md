# Demucs API 服务

基于 [Demucs](https://github.com/adefossez/demucs) 的音频源分离 RESTful API 服务。该服务可以将混合音频分离为各个音轨（鼓、贝斯、人声和其他）。

## 功能特点

- 支持多种音频格式（wav、mp3、flac等）
- 提供多种预训练模型选择
- 可选择输出为MP3或WAV格式
- 支持Docker部署
- RESTful API接口

## API接口

### 音频分离

```
POST /separate
Content-Type: multipart/form-data

参数:- file: 要上传的音频文件 (必需)- model: 使用的模型 (可选，默认: htdemucs)- two_stems: 是否只分离为两个音轨 (可选，如 vocals 表示分离人声和伴奏)- segment: 分段长度，必须为整数 (可选，htdemucs模型默认7秒，其他模型默认10秒)- mp3: 是否输出MP3格式 (可选，默认: false)- mp3_bitrate: MP3比特率 (可选，默认: 320)
```

### 健康检查

```
GET /health
```

## 本地运行

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 运行服务：

```bash
python app.py
```

服务将在 http://localhost:5000 上运行。

## Docker部署

### 构建Docker镜像

```bash
docker build -t demucs-api .
```

### 运行Docker容器

```bash
docker run -p 8080:8080 demucs-api
```

服务将在 http://localhost:8080 上运行。

## GCP部署

### 使用Cloud Run部署

1. 构建并推送镜像到Google Container Registry：

```bash
# 设置项目ID
PROJECT_ID=your-project-id

# 构建镜像
docker build -t gcr.io/$PROJECT_ID/demucs-api .

# 推送镜像
docker push gcr.io/$PROJECT_ID/demucs-api
```

2. 部署到Cloud Run：

```bash
gcloud run deploy demucs-api \
  --image gcr.io/$PROJECT_ID/demucs-api \
  --platform managed \
  --region asia-east1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --allow-unauthenticated
```

## 可用模型

- `htdemucs`: Hybrid Transformer Demucs (默认)
- `htdemucs_ft`: 微调版本的htdemucs，更准确但更慢
- `htdemucs_6s`: 6音轨版本，增加了钢琴和吉他音轨
- `mdx`: 仅在MusDB HQ上训练的模型
- `mdx_q`: mdx的量化版本，更小但质量可能略差

## 使用示例

使用curl发送请求：

```bash
curl -X POST -F "file=@song.mp3" -F "model=htdemucs" -F "mp3=true" http://localhost:8080/separate -o separated.zip
```

响应将是一个ZIP文件，包含分离后的各个音轨文件。 