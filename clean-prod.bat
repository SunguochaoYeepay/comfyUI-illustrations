@echo off
echo 清理生产环境数据...

REM 停止生产环境服务
echo 1. 停止生产环境服务...
docker-compose down

REM 删除生产环境数据卷
echo 2. 删除生产环境数据卷...
docker volume rm yeepay_yeepay-uploads yeepay_yeepay-outputs yeepay_yeepay-database 2>nul

echo 生产环境数据清理完成！
pause
