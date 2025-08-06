#!/bin/bash

# YeePay AI图像生成服务部署脚本
# 作者: AI Assistant
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p back/uploads
    mkdir -p back/outputs
    mkdir -p nginx/ssl
    mkdir -p logs
    
    log_success "目录创建完成"
}

# 设置环境变量
setup_environment() {
    log_info "设置环境变量..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# YeePay AI图像生成服务环境配置
ENVIRONMENT=production

# ComfyUI配置
COMFYUI_URL=http://host.docker.internal:8188
COMFYUI_TIMEOUT=300

# 服务配置
MAX_CONCURRENT_TASKS=3
CORS_ORIGINS=*
DEBUG=false
LOG_LEVEL=INFO

# 文件上传配置
MAX_FILE_SIZE=10485760

# 安全配置
API_KEY=

# 数据库配置
DATABASE_URL=./tasks.db
EOF
        log_success "环境配置文件创建完成"
    else
        log_warning "环境配置文件已存在，跳过创建"
    fi
}

# 构建和启动服务
deploy_services() {
    log_info "开始构建和部署服务..."
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose down --remove-orphans
    
    # 清理旧镜像
    log_info "清理旧镜像..."
    docker system prune -f
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker-compose up -d
    
    log_success "服务部署完成"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    sleep 10
    
    # 检查容器状态
    if docker-compose ps | grep -q "Up"; then
        log_success "所有服务运行正常"
    else
        log_error "部分服务启动失败"
        docker-compose logs
        exit 1
    fi
    
    # 检查健康状态
    log_info "检查服务健康状态..."
    if curl -f http://localhost:9000/api/health &> /dev/null; then
        log_success "后端API服务健康检查通过"
    else
        log_warning "后端API服务健康检查失败，请检查日志"
    fi
    
    if curl -f http://localhost &> /dev/null; then
        log_success "前端服务健康检查通过"
    else
        log_warning "前端服务健康检查失败，请检查日志"
    fi
}

# 显示服务信息
show_info() {
    log_success "部署完成！"
    echo
    echo "服务访问地址："
    echo "  - 前端界面: http://localhost"
    echo "  - 后端API: http://localhost:9000"
    echo "  - API文档: http://localhost:9000/docs"
    echo
    echo "常用命令："
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 停止服务: docker-compose down"
    echo "  - 重启服务: docker-compose restart"
    echo "  - 更新服务: ./deploy.sh"
    echo
    echo "注意事项："
    echo "  - 确保ComfyUI服务在 http://localhost:8188 运行"
    echo "  - 数据库文件保存在 ./back/tasks.db"
    echo "  - 上传文件保存在 ./back/uploads"
    echo "  - 生成图片保存在 ./back/outputs"
}

# 主函数
main() {
    echo "=========================================="
    echo "    YeePay AI图像生成服务部署脚本"
    echo "=========================================="
    echo
    
    check_docker
    create_directories
    setup_environment
    deploy_services
    check_services
    show_info
}

# 执行主函数
main "$@" 