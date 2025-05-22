FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    xz-utils \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装FFmpeg 6.1.1版本（确保与torchaudio兼容）
# 使用共享库而非静态库
RUN wget -q https://github.com/GyanD/codexffmpeg/releases/download/6.1.1/ffmpeg-6.1.1-full_build-shared.tar.xz && \
    mkdir -p ffmpeg-shared && \
    tar -xf ffmpeg-6.1.1-full_build-shared.tar.xz -C ffmpeg-shared --strip-components 1 && \
    cp -r ffmpeg-shared/bin/* /usr/local/bin/ && \
    cp -r ffmpeg-shared/lib/* /usr/local/lib/ && \
    ldconfig && \
    rm -rf ffmpeg-shared ffmpeg-6.1.1-full_build-shared.tar.xz

# 升级pip并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建工作目录
RUN mkdir -p uploads outputs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV FLASK_ENV=production

# 验证FFmpeg版本和torchaudio后端
RUN ffmpeg -version | grep "ffmpeg version 6" && \
    python -c "import torchaudio; print(f'Available backends: {torchaudio.list_audio_backends()}')" || echo "FFmpeg backend not detected in torchaudio, audio processing may be affected"

# 暴露端口
EXPOSE 8080

# 使用gunicorn运行应用
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "run:app" 