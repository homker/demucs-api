FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    build-essential \
    software-properties-common \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 添加FFmpeg官方仓库并安装最新版本
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 如果默认ffmpeg版本不满足需求，使用静态构建版本
RUN if ! ffmpeg -version | grep -q "version [6-9]"; then \
    mkdir -p /tmp/ffmpeg && \
    cd /tmp/ffmpeg && \
    wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xf ffmpeg-release-amd64-static.tar.xz --strip-components=1 && \
    cp ffmpeg ffprobe /usr/local/bin/ && \
    cd / && \
    rm -rf /tmp/ffmpeg; \
fi

# 升级pip并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建工作目录
RUN mkdir -p uploads outputs test/mcp

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV FLASK_ENV=production
ENV HOST=0.0.0.0
ENV TORCH_HOME=/app/models
ENV OMP_NUM_THREADS=1

# 验证安装
RUN ffmpeg -version && \
    python -c "import torchaudio; print(f'Available backends: {torchaudio.list_audio_backends()}')" && \
    python -c "import flask_cors; import sseclient; print('MCP dependencies installed successfully')" && \
    python -c "import demucs; print('Demucs installed successfully')"

VOLUME /app/uploads
VOLUME /app/outputs
VOLUME /app/models

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 使用gunicorn运行应用
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "run:application" 