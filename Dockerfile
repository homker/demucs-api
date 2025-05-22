FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（FFmpeg用于音频处理）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

# 暴露端口
EXPOSE 8080

# 使用gunicorn运行应用
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "run:app" 