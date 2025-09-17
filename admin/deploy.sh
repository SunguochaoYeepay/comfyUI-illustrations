#!/bin/bash

# Admin Docker部署脚本

echo "🚀 开始部署YeePay Admin..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose build --no-cache

# 启动服务
echo "🌐 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 检查健康状态
echo "🏥 检查健康状态..."
docker-compose logs admin-backend | tail -20

echo "✅ Admin部署完成！"
echo "🌐 Admin Backend: http://localhost:8888"
echo "🌐 Admin Frontend: http://localhost:8889"
echo ""
echo "📋 查看日志: docker-compose logs -f"
echo "🛑 停止服务: docker-compose down"
