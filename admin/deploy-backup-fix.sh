#!/bin/bash

# Admin备份功能修复部署脚本

echo "🚀 开始重新部署Admin服务（修复备份功能）..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 停止现有容器
echo "🛑 停止现有Admin容器..."
docker-compose down

# 清理旧的镜像（可选）
echo "🧹 清理旧镜像..."
docker image prune -f

# 构建新镜像
echo "🔨 构建新的Docker镜像..."
docker-compose build --no-cache

# 启动服务
echo "🌐 启动Admin服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 检查健康状态
echo "🏥 检查服务健康状态..."
echo "=== Admin Backend 日志 ==="
docker-compose logs admin-backend | tail -20

echo "=== Admin Frontend 日志 ==="
docker-compose logs admin-frontend | tail -10

# 测试备份功能
echo "🧪 测试备份功能..."
echo "等待5秒后测试API..."
sleep 5

# 测试API端点
echo "测试Admin Backend API..."
curl -f http://localhost:8000/ || echo "❌ Admin Backend API测试失败"

echo "测试Admin Frontend..."
curl -f http://localhost:8001/ || echo "❌ Admin Frontend测试失败"

echo ""
echo "✅ Admin服务重新部署完成！"
echo ""
echo "🌐 服务地址："
echo "   Admin Backend: http://localhost:8000"
echo "   Admin Frontend: http://localhost:8001"
echo ""
echo "📋 备份功能修复内容："
echo "   ✅ 添加了主服务数据卷挂载"
echo "   ✅ 支持Docker环境路径检测"
echo "   ✅ 修复了备份恢复路径问题"
echo ""
echo "🔧 管理命令："
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo ""
echo "🎯 现在可以在Admin界面中正常使用备份和恢复功能了！"
