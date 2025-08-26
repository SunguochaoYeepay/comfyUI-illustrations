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
    openssl-dev

# 复制 requirements.txt
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 生产环境镜像
FROM python:3.10-alpine

# 设置工作目录
WORKDIR /app

# 设置 pip 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装运行时依赖（Alpine 版本）
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# 从构建阶段复制 Python 包
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 9000

# 启动命令
CMD ["python", "main.py"]
