#!/bin/bash

# YeePay Docker 部署脚本
set -e

echo "========================================"
echo "YeePay Docker 部署脚本"
echo "========================================"

# 检查 Docker 环境
echo ""
echo "[1/6] 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ Docker 环境正常"

# 清理 Docker 缓存
echo ""
echo "[2/6] 清理 Docker 缓存..."
docker system prune -f
docker builder prune -f
echo "✅ 缓存清理完成"

# 检查必要目录
echo ""
echo "[3/6] 检查必要目录..."
if [ ! -d "nginx/ssl" ]; then
    echo "📁 创建 SSL 目录..."
    mkdir -p nginx/ssl
fi

# 停止现有容器
echo ""
echo "[4/6] 停止现有容器..."
docker-compose -f docker-compose.prod.yml down || true

# 构建并启动生产环境
echo ""
echo "[5/6] 构建并启动生产环境..."
echo "📦 开始构建镜像，请耐心等待..."
docker-compose -f docker-compose.prod.yml up -d --build

if [ $? -ne 0 ]; then
    echo "❌ 构建失败，请检查错误信息"
    echo ""
    echo "🔍 查看详细日志:"
    echo "docker-compose -f docker-compose.prod.yml logs"
    exit 1
fi

# 等待服务启动
echo ""
echo "[6/6] 等待服务启动..."
echo "⏳ 等待服务启动，请稍候..."
sleep 20

echo ""
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
echo "🌐 服务地址:"
echo "   统一入口: http://localhost:80"
echo "   HTTPS: https://localhost:443 (需要SSL证书)"
echo "   健康检查: http://localhost/health"
echo ""
echo "📊 容器状态:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🔍 查看日志:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🛑 停止服务:"
echo "   docker-compose -f docker-compose.prod.yml down"
echo ""
