@echo off
echo 启动开发环境...

REM 启动后端服务（使用开发环境配置）
echo 1. 启动后端服务...
docker-compose -f docker-compose.dev.yml up -d backend

REM 启动前端开发服务器
echo 2. 启动前端开发服务器...
cd frontend
npm run dev

echo 开发环境启动完成！
echo 前端地址: http://localhost:5173
echo 后端API: http://localhost:9000
pause
