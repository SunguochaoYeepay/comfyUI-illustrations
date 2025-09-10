# 使用 Alpine Linux 作为基础镜像（更轻量）
FROM python:3.10-alpine AS builder

# 设置工作目录
WORKDIR /app

# 设置 pip 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装构建依赖（Alpine 版本更轻量）
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    libjpeg-turbo-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev

# 复制 requirements.txt
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 生产环境镜像
FROM python:3.10-alpine

# 设置时区为北京时间
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata

# 设置工作目录
WORKDIR /app

# 设置 pip 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装运行时依赖（Alpine 版本）
RUN apk add --no-cache \
    curl \
    libjpeg-turbo \
    zlib \
    freetype \
    lcms2 \
    openjpeg \
    tiff \
    && rm -rf /var/cache/apk/*

# 从构建阶段复制 Python 包
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/uploads /app/outputs /app/data /app/logs

# 设置权限
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 9000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/api/health || exit 1

# 启动命令
CMD ["python", "main.py"]
