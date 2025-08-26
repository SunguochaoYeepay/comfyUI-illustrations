@echo off
chcp 65001 >nul
echo ========================================
echo YeePay 生产环境部署脚本
echo ========================================

echo.
echo [1/6] 检查 Docker 环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未安装或未启动
    pause
    exit /b 1
)
echo ✅ Docker 环境正常

echo.
echo [2/6] 清理 Docker 缓存...
docker system prune -f
docker builder prune -f
echo ✅ 缓存清理完成

echo.
echo [3/6] 检查必要目录...
if not exist "nginx\ssl" (
    echo 📁 创建 SSL 目录...
    mkdir "nginx\ssl"
)

echo.
echo [4/6] 停止现有容器...
docker-compose -f docker-compose.prod.yml down
if errorlevel 1 (
    echo ⚠️ 停止容器时出现警告（可能是首次运行）
)

echo.
echo [5/6] 构建并启动生产环境...
echo 📦 开始构建镜像，请耐心等待...
docker-compose -f docker-compose.prod.yml up -d --build

if errorlevel 1 (
    echo ❌ 构建失败，请检查错误信息
    echo.
    echo 🔍 查看详细日志:
    echo docker-compose -f docker-compose.prod.yml logs
    pause
    exit /b 1
)

echo.
echo [6/6] 等待服务启动...
echo ⏳ 等待服务启动，请稍候...
timeout /t 20 /nobreak >nul

echo.
echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 🌐 服务地址:
echo   统一入口: http://localhost:80
echo   HTTPS: https://localhost:443 (需要SSL证书)
echo   健康检查: http://localhost/health
echo.
echo 📊 容器状态:
docker-compose -f docker-compose.prod.yml ps

echo.
echo 🔍 查看日志:
echo   docker-compose -f docker-compose.prod.yml logs -f
echo.
echo 🛑 停止服务:
echo   docker-compose -f docker-compose.prod.yml down
echo.
pause 