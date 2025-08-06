@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM YeePay AI图像生成服务部署脚本 (Windows版本)
REM 作者: AI Assistant
REM 版本: 1.0.0

echo ==========================================
echo     YeePay AI图像生成服务部署脚本
echo ==========================================
echo.

REM 检查Docker是否安装
echo [INFO] 检查Docker环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

echo [SUCCESS] Docker环境检查通过
echo.

REM 创建必要的目录
echo [INFO] 创建必要的目录...
if not exist "back\uploads" mkdir "back\uploads"
if not exist "back\outputs" mkdir "back\outputs"
if not exist "nginx\ssl" mkdir "nginx\ssl"
if not exist "logs" mkdir "logs"
echo [SUCCESS] 目录创建完成
echo.

REM 设置环境变量
echo [INFO] 设置环境变量...
if not exist ".env" (
    (
        echo # YeePay AI图像生成服务环境配置
        echo ENVIRONMENT=production
        echo.
        echo # ComfyUI配置
        echo COMFYUI_URL=http://host.docker.internal:8188
        echo COMFYUI_TIMEOUT=300
        echo.
        echo # 服务配置
        echo MAX_CONCURRENT_TASKS=3
        echo CORS_ORIGINS=*
        echo DEBUG=false
        echo LOG_LEVEL=INFO
        echo.
        echo # 文件上传配置
        echo MAX_FILE_SIZE=10485760
        echo.
        echo # 安全配置
        echo API_KEY=
        echo.
        echo # 数据库配置
        echo DATABASE_URL=./tasks.db
    ) > .env
    echo [SUCCESS] 环境配置文件创建完成
) else (
    echo [WARNING] 环境配置文件已存在，跳过创建
)
echo.

REM 构建和启动服务
echo [INFO] 开始构建和部署服务...

REM 停止现有服务
echo [INFO] 停止现有服务...
docker-compose down --remove-orphans

REM 清理旧镜像
echo [INFO] 清理旧镜像...
docker system prune -f

REM 构建镜像
echo [INFO] 构建Docker镜像...
docker-compose build --no-cache

REM 启动服务
echo [INFO] 启动服务...
docker-compose up -d

echo [SUCCESS] 服务部署完成
echo.

REM 检查服务状态
echo [INFO] 检查服务状态...
timeout /t 10 /nobreak >nul

REM 检查容器状态
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo [ERROR] 部分服务启动失败
    docker-compose logs
    pause
    exit /b 1
) else (
    echo [SUCCESS] 所有服务运行正常
)

REM 检查健康状态
echo [INFO] 检查服务健康状态...
curl -f http://localhost:9000/api/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] 后端API服务健康检查失败，请检查日志
) else (
    echo [SUCCESS] 后端API服务健康检查通过
)

curl -f http://localhost >nul 2>&1
if errorlevel 1 (
    echo [WARNING] 前端服务健康检查失败，请检查日志
) else (
    echo [SUCCESS] 前端服务健康检查通过
)

echo.
echo [SUCCESS] 部署完成！
echo.
echo 服务访问地址：
echo   - 前端界面: http://localhost
echo   - 后端API: http://localhost:9000
echo   - API文档: http://localhost:9000/docs
echo.
echo 常用命令：
echo   - 查看日志: docker-compose logs -f
echo   - 停止服务: docker-compose down
echo   - 重启服务: docker-compose restart
echo   - 更新服务: deploy.bat
echo.
echo 注意事项：
echo   - 确保ComfyUI服务在 http://localhost:8188 运行
echo   - 数据库文件保存在 ./back/tasks.db
echo   - 上传文件保存在 ./back/uploads
echo   - 生成图片保存在 ./back/outputs
echo.

pause 