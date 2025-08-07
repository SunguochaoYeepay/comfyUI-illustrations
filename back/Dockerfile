FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads outputs

# 暴露端口
EXPOSE 9000

# 设置环境变量
ENV ENVIRONMENT=docker
ENV COMFYUI_URL=http://comfyui:8188
ENV COMFYUI_OUTPUT_DIR=/app/comfyui/output/yeepay
ENV COMFYUI_MAIN_OUTPUT_DIR=/app/comfyui/output

# 启动应用
CMD ["python", "main.py"]
