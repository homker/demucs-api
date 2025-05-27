# 资源限制部署配置

## 概述

为了适应资源有限的服务器环境，本配置将应用限制为：
- 只支持默认模型 (htdemucs)
- 只支持MP3输出格式
- 只支持低质量音频 (128kbps, 22kHz)

## 配置说明

### 限制内容
1. **模型限制**：只使用 `htdemucs` 默认模型
2. **格式限制**：只输出 `MP3` 格式
3. **质量限制**：只支持 `low` 质量 (128kbps, 22kHz)
4. **文件大小限制**：最大上传文件 100MB
5. **保留时间限制**：文件保留时间 30分钟

### 优势
- 显著降低内存使用
- 减少CPU处理时间
- 节省存储空间
- 提高处理速度
- 降低服务器负载

### 部署方式

#### 使用Docker Compose
```bash
docker-compose up -d
```

#### 使用环境变量部署
```bash
export DEFAULT_OUTPUT_FORMAT=mp3
export DEFAULT_AUDIO_QUALITY=low
export MAX_CONTENT_LENGTH=104857600
export FILE_RETENTION_MINUTES=30
export SAMPLE_RATE=22050

python run.py
```

## 性能预期

- 内存使用：约1-2GB
- 处理时间：比全功能版本快20-30%
- 文件大小：比WAV格式小80-90%
- 磁盘使用：显著降低 