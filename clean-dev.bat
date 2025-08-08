@echo off
echo 清理开发环境数据...

REM 停止开发环境服务
echo 1. 停止开发环境服务...
docker-compose -f docker-compose.dev.yml down

REM 删除开发环境数据卷
echo 2. 删除开发环境数据卷...
docker volume rm yeepay_yeepay-dev-uploads yeepay_yeepay-dev-outputs yeepay_yeepay-dev-database 2>nul

echo 开发环境数据清理完成！
pause
