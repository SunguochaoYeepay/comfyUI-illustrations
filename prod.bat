@echo off
echo 启动生产环境...

REM 构建前端
echo 1. 构建前端...
cd frontend
npm run build
cd ..

REM 启动所有服务（使用生产环境配置）
echo 2. 启动Docker服务...
docker-compose up -d

echo 生产环境启动完成！
echo 访问地址: http://localhost:3000
pause
