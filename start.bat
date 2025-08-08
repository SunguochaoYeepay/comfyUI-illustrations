@echo off
echo 启动YeePay服务...

REM 构建前端
echo 1. 构建前端...
call build-frontend.bat

REM 启动Docker服务
echo 2. 启动Docker服务...
docker-compose up -d

echo 服务启动完成！
echo 访问地址: http://localhost:3000
pause
