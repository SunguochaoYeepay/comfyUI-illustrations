# Admin Backend Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖 - 使用重试机制
RUN apt-get update --fix-missing && \
    apt-get install -y --fix-missing curl && \
    rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/admin.db
ENV HOST=0.0.0.0
ENV PORT=8888

# 暴露端口
EXPOSE 8888

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8888/ || exit 1

# 创建启动脚本
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 启动命令
CMD ["/app/start.sh"]
