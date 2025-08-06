# YeePay AI图像生成服务

一个基于ComfyUI的AI图像生成服务，提供Web界面和RESTful API。

## 🚀 快速部署

### 前置要求

1. **Docker & Docker Compose**
   ```bash
   # 安装Docker Desktop (Windows/Mac)
   # 或安装Docker Engine (Linux)
   ```

2. **ComfyUI服务**
   - 确保ComfyUI在 `http://localhost:8188` 运行
   - 或者修改 `.env` 文件中的 `COMFYUI_URL` 配置

### 一键部署

```bash
# 克隆项目
git clone <your-repo-url>
cd YeePay

# 一键部署
./deploy.sh
```

### 手动部署

```bash
# 1. 创建环境配置
cp .env.example .env
# 编辑 .env 文件，配置ComfyUI地址等

# 2. 构建和启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

## 📁 项目结构

```
YeePay/
├── back/                 # 后端API服务
│   ├── main.py          # FastAPI主程序
│   ├── config.py        # 配置文件
│   ├── requirements.txt # Python依赖
│   ├── uploads/         # 上传文件目录
│   └── outputs/         # 生成图片目录
├── frontend/            # 前端Vue应用
│   ├── src/            # 源代码
│   ├── package.json    # Node.js依赖
│   └── vite.config.js  # Vite配置
├── nginx/              # Nginx配置
├── docker-compose.yml  # Docker编排
├── Dockerfile.backend  # 后端Dockerfile
├── Dockerfile.frontend # 前端Dockerfile
└── deploy.sh          # 部署脚本
```

## 🌐 服务访问

部署完成后，可以通过以下地址访问：

- **前端界面**: http://localhost
- **后端API**: http://localhost:9000
- **API文档**: http://localhost:9000/docs

## 🔧 配置说明

### 环境变量

在 `.env` 文件中配置：

```env
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
API_KEY=your-api-key-here
```

### 端口配置

- **80**: 前端服务 (Nginx)
- **9000**: 后端API服务
- **443**: HTTPS (生产环境)

## 📊 监控和管理

### 查看服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 服务管理

```bash
# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新服务
docker-compose pull
docker-compose up -d

# 清理资源
docker-compose down --volumes --remove-orphans
```

## 🔒 安全配置

### 生产环境部署

1. **配置HTTPS**
   ```bash
   # 将SSL证书放入 nginx/ssl/ 目录
   # 修改 nginx/default.conf 启用HTTPS
   ```

2. **设置API密钥**
   ```env
   API_KEY=your-secure-api-key
   ```

3. **限制CORS**
   ```env
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **启用生产模式**
   ```bash
   # 使用生产配置启动
   docker-compose --profile production up -d
   ```

## 📈 性能优化

### 资源限制

在 `docker-compose.yml` 中配置资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
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
   
   # 修改 .env 中的 COMFYUI_URL
   ```

2. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :80
   netstat -tulpn | grep :9000
   
   # 修改 docker-compose.yml 中的端口映射
   ```

3. **磁盘空间不足**
   ```bash
   # 清理Docker资源
   docker system prune -a
   
   # 清理生成的文件
   rm -rf back/outputs/*
   ```

### 日志分析

```bash
# 查看错误日志
docker-compose logs --tail=100 | grep ERROR

# 查看访问日志
docker-compose logs nginx | grep "GET /api"
```

## 📝 API文档

详细的API文档请访问：http://localhost:9000/docs

主要端点：
- `POST /api/generate-image` - 生成图像
- `GET /api/task/{task_id}` - 查询任务状态
- `GET /api/history` - 获取历史记录
- `GET /api/image/{task_id}` - 获取生成的图像

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

---

**YeePay AI图像生成服务** - 让AI创作更简单 🎨 