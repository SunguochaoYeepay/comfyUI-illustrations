@echo off
chcp 65001 >nul
echo ========================================
echo YeePay Production Deployment Script
echo ========================================

echo.
echo [1/7] Checking Docker environment...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not installed or not running
    pause
    exit /b 1
)
echo OK: Docker environment is ready

echo.
echo [2/7] Cleaning Docker cache...
docker system prune -f
docker builder prune -f
echo OK: Cache cleanup completed

echo.
echo [3/7] Checking required directories...
if not exist "nginx\ssl" (
    echo Creating SSL directory...
    mkdir "nginx\ssl"
)

echo.
echo [4/7] Stopping existing containers...
docker-compose -f docker-compose.prod.yml down 2>nul
if errorlevel 1 (
    echo WARNING: Error stopping containers (may be first run)
)

echo.
echo [5/7] Checking frontend build...
if not exist "frontend\dist\index.html" (
    echo Building frontend...
    cd frontend
    call npm run build
    if errorlevel 1 (
        echo ERROR: Frontend build failed
        pause
        exit /b 1
    )
    cd ..
    echo OK: Frontend build completed
) else (
    echo OK: Frontend already built
)

echo.
echo [6/7] Building and starting production environment...
echo Building images, please wait...
docker-compose -f docker-compose.prod.yml up -d --build

if errorlevel 1 (
    echo ERROR: Build failed, please check error messages
    echo.
    echo View detailed logs:
    docker-compose -f docker-compose.prod.yml logs
    pause
    exit /b 1
)

echo.
echo [7/7] Waiting for services to start...
echo Please wait for services to start...
timeout /t 20 /nobreak >nul

echo.
echo ========================================
echo Deployment completed!
echo ========================================
echo.
echo Service URLs:
echo   Main entry: http://localhost:80
echo   HTTPS: https://localhost:443 (requires SSL certificate)
echo   Health check: http://localhost/health
echo.
echo Container status:
docker-compose -f docker-compose.prod.yml ps

echo.
echo View logs:
echo   docker-compose -f docker-compose.prod.yml logs -f
echo.
echo Stop services:
echo   docker-compose -f docker-compose.prod.yml down
echo.
pause