# YeePay AI图像生成服务

一个基于ComfyUI的AI图像生成服务，提供Web界面和RESTful API，支持Flux和Qwen模型。

## 🚀 快速部署

### 前置要求

1. **Docker & Docker Compose**
   ```bash
   # 安装Docker Desktop (Windows/Mac)
   # 或安装Docker Engine (Linux)
   ```

2. **ComfyUI服务**
   - 确保ComfyUI在 `http://localhost:8188` 运行
   - 或者修改环境变量中的 `COMFYUI_URL` 配置

3. **Ollama服务** (可选，用于翻译功能)
   - 确保Ollama在 `http://localhost:11434` 运行
   - 安装qwen2.5模型：`ollama pull qwen2.5:3b-instruct`

### 一键部署

```bash
# 克隆项目
git clone <your-repo-url>
cd YeePay

# 一键部署生产环境
./deploy.bat
```

### 手动部署

```bash
# 1. 构建和启动生产服务
docker compose -f docker-compose.prod.yml up -d --build

# 2. 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 3. 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

## 📁 项目结构

```
YeePay/
├── back/                    # 后端API服务 (FastAPI)
│   ├── main.py             # 主程序入口
│   ├── config/             # 配置管理
│   │   └── settings.py     # 统一配置管理
│   ├── core/               # 核心模块
│   │   ├── model_manager.py    # 模型管理
│   │   ├── upscale_manager.py  # 图像放大
│   │   └── workflow_template.py # 工作流模板
│   ├── api/                # API路由
│   │   └── upscale_routes.py   # 放大API
│   ├── models/             # 数据模型
│   ├── workflows/          # 工作流模板
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端Vue应用
│   ├── src/               # 源代码
│   ├── package.json       # Node.js依赖
│   └── vite.config.js     # Vite配置
├── nginx/                 # Nginx配置
│   └── default.conf       # 反向代理配置
├── docker-compose.prod.yml # 生产环境Docker编排
├── Dockerfile.nginx       # Nginx Dockerfile (包含前端)
├── deploy.bat            # Windows部署脚本
└── docs/                 # 文档目录
```

## 🌐 服务访问

部署完成后，可以通过以下地址访问：

- **前端界面**: http://localhost (通过Nginx)
- **后端API**: http://localhost:9000 (直接访问)
- **API文档**: http://localhost:9000/docs
- **健康检查**: http://localhost/api/health

## 🏗️ 架构说明

当前采用简化架构：
- **后端服务**: FastAPI (端口9000)
- **前端服务**: Vue3 + Vite (打包为静态文件)
- **反向代理**: Nginx (端口80，包含前端静态文件)
- **数据存储**: SQLite + 文件系统

## 🔧 配置说明

### 环境变量

在 `back/env.example` 中查看完整配置示例：

```env
# 环境配置
ENVIRONMENT=production  # local 或 production

# ComfyUI配置
COMFYUI_URL=http://127.0.0.1:8188

# 本地开发环境路径
COMFYUI_OUTPUT_DIR=E:/AI-Image/ComfyUI-aki-v1.4/output/yeepay
COMFYUI_MAIN_OUTPUT_DIR=E:/AI-Image/ComfyUI-aki-v1.4/output
COMFYUI_INPUT_DIR=E:/AI-Image/ComfyUI-aki-v1.4/input
COMFYUI_MODELS_DIR=E:/AI-Image/ComfyUI-aki-v1.4/models
COMFYUI_LORAS_DIR=E:/AI-Image/ComfyUI-aki-v1.4/models/loras

# Docker环境路径（自动配置）
# COMFYUI_OUTPUT_DIR=/app/comfyui/output/yeepay
# COMFYUI_MAIN_OUTPUT_DIR=/app/comfyui/output
# COMFYUI_INPUT_DIR=/app/comfyui/input
# COMFYUI_MODELS_DIR=/app/comfyui/models
# COMFYUI_LORAS_DIR=/app/comfyui/models/loras
```

### 端口配置

- **80**: Nginx反向代理 (包含前端静态文件)
- **9000**: 后端API服务 (FastAPI)
- **443**: HTTPS (生产环境，可选)

## 📊 监控和管理

### 查看服务状态

```bash
# 查看所有容器状态
docker compose -f docker-compose.prod.yml ps

# 查看服务日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx
```

### 服务管理

```bash
# 重启服务
docker compose -f docker-compose.prod.yml restart

# 停止服务
docker compose -f docker-compose.prod.yml down

# 更新服务
docker compose -f docker-compose.prod.yml up -d --build

# 清理资源
docker compose -f docker-compose.prod.yml down --volumes --remove-orphans
```

## 🔒 安全配置

### 生产环境部署

1. **配置HTTPS**
   ```bash
   # 将SSL证书放入 nginx/ssl/ 目录
   # 修改 nginx/default.conf 启用HTTPS
   ```

2. **环境变量配置**
   ```env
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   ```

3. **限制CORS**
   ```env
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **启用生产模式**
   ```bash
   # 使用生产配置启动
   docker compose -f docker-compose.prod.yml up -d
   ```

## 📈 性能优化

### 资源限制

在 `docker-compose.prod.yml` 中配置资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### 缓存配置

- 静态资源缓存：1年
- 图片文件缓存：1天
- API响应缓存：1小时

## 🐛 故障排除

### 常见问题

1. **ComfyUI连接失败**
   ```bash
   # 检查ComfyUI是否运行
   curl http://localhost:8188
   
   # 修改环境变量中的 COMFYUI_URL
   ```

2. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :80
   netstat -tulpn | grep :9000
   
   # 修改 docker-compose.prod.yml 中的端口映射
   ```

3. **磁盘空间不足**
   ```bash
   # 清理Docker资源
   docker system prune -a
   
   # 清理生成的文件
   rm -rf back/outputs/*
   ```

4. **放大功能异常**
   ```bash
   # 检查放大工作流文件
   ls -la back/flux_upscale_workflow.json
   
   # 检查模型文件
   ls -la E:/AI-Image/ComfyUI-aki-v1.4/models/
   ```

### 日志分析

```bash
# 查看错误日志
docker compose -f docker-compose.prod.yml logs --tail=100 | grep ERROR

# 查看访问日志
docker compose -f docker-compose.prod.yml logs nginx | grep "GET /api"
```

## 📝 API文档

详细的API文档请访问：http://localhost:9000/docs

### 主要端点

**图像生成**
- `POST /api/generate-image` - 生成图像
- `GET /api/task/{task_id}` - 查询任务状态
- `GET /api/history` - 获取历史记录
- `GET /api/image/{task_id}` - 获取生成的图像

**图像放大**
- `POST /api/upscale/` - 上传图像进行放大
- `POST /api/upscale/by-path` - 通过路径放大图像
- `GET /api/upscale/{task_id}` - 查询放大任务状态
- `GET /api/upscale/image/{task_id}/{filename}` - 获取放大后的图像

**模型管理**
- `GET /api/models` - 获取可用模型列表
- `GET /api/loras` - 获取可用LoRA列表
- `POST /api/loras/upload` - 上传LoRA文件

**翻译服务**
- `POST /api/translate` - 中英文翻译
- `GET /api/translate/health` - 翻译服务健康检查

## 🧹 已清理的无用脚本

为了简化项目结构，以下脚本已被清理：

### 删除的脚本
- `deploy.sh` - 已替换为 `deploy.bat` (Windows环境)
- `dev-local.bat` - 本地开发脚本
- `dev-frontend.bat` - 前端开发脚本
- `deploy-prod.bat` - 生产部署脚本
- `deploy-simple.bat` - 简化部署脚本
- `docker-compose.dev.yml` - 开发环境配置
- `docker-compose.frontend-only.yml` - 前端专用配置
- `docker-compose.prod-simple.yml` - 简化生产配置

### 保留的脚本
- `deploy.bat` - 主要部署脚本 (Windows)
- `docker-compose.prod.yml` - 生产环境配置
- `Dockerfile.nginx` - Nginx Dockerfile (包含前端)

### 架构优化
- 删除了独立的前端服务容器
- 前端静态文件直接打包到 Nginx 镜像中
- 简化了 Docker 网络配置
- 统一了路径配置管理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题，请：
1. 查看 [Issues](../../issues)
2. 提交新的 Issue
3. 联系维护团队

## 🎯 功能特性

- **多模型支持**: Flux Kontext、Qwen 图像模型
- **图像放大**: 基于 UltimateSDUpscale 的高质量放大
- **LoRA 管理**: 动态加载和管理 LoRA 文件
- **翻译服务**: 中英文互译 (基于 Ollama)
- **历史管理**: 任务历史记录和收藏功能
- **统一配置**: 环境自适应的路径配置管理

---

**YeePay AI图像生成服务** - 让AI创作更简单 🎨 