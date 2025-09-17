#!/bin/bash

# Admin Backend启动脚本

echo "🚀 启动YeePay Admin Backend..."

# 初始化数据库和配置
echo "📋 初始化数据库..."
python init_admin.py

# 启动服务
echo "🌐 启动Web服务..."
exec uvicorn main:app --host 0.0.0.0 --port 8888
