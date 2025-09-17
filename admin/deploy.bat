@echo off
chcp 65001 >nul

echo 🚀 开始部署YeePay Admin...

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未运行，请先启动Docker
    pause
    exit /b 1
)

REM 停止现有容器
echo 🛑 停止现有容器...
docker-compose down

REM 构建镜像
echo 🔨 构建Docker镜像...
docker-compose build --no-cache

REM 启动服务
echo 🌐 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 📊 检查服务状态...
docker-compose ps

REM 检查健康状态
echo 🏥 检查健康状态...
docker-compose logs admin-backend | findstr /C:"INFO" | findstr /C:"ERROR" | findstr /C:"WARNING"

echo ✅ Admin部署完成！
echo 🌐 Admin Backend: http://localhost:8888
echo 🌐 Admin Frontend: http://localhost:8889
echo.
echo 📋 查看日志: docker-compose logs -f
echo 🛑 停止服务: docker-compose down

pause
