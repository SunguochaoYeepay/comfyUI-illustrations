# 🎨 Flux Kontext 图像生成服务

基于ComfyUI和Flux模型的智能图像生成后端服务，支持参考图像和文本描述生成高质量图像。

## ✨ 功能特性

- 🖼️ **参考图像生成**: 基于上传的参考图像生成新图像
- 📝 **文本描述**: 结合文本描述控制生成效果
- ⚙️ **参数调节**: 支持步数、CFG、引导强度等参数调节
- 📊 **任务管理**: 异步任务处理，实时状态查询
- 📚 **历史记录**: 保存生成历史，支持查看和下载
- 🌐 **Web界面**: 提供美观的前端界面
- 🔌 **RESTful API**: 完整的API接口，支持第三方集成

## 🏗️ 架构设计

```
前端页面 (frontend.html)
    ↓
FastAPI 后端服务 (main.py)
    ↓
ComfyUI 工作流执行器
    ↓
Flux Kontext 模型
```

### 核心组件

- **WorkflowTemplate**: 工作流模板管理器
- **ComfyUIClient**: ComfyUI API客户端
- **TaskManager**: 任务管理器
- **DatabaseManager**: 数据库管理器

## 📋 系统要求

### 硬件要求
- **GPU**: NVIDIA RTX 3060 或更高 (推荐 RTX 4070+)
- **显存**: 最少 8GB (推荐 12GB+)
- **内存**: 最少 16GB (推荐 32GB+)
- **存储**: 最少 20GB 可用空间

### 软件要求
- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.8 或更高版本
- **ComfyUI**: 最新版本
- **CUDA**: 11.8 或更高版本 (NVIDIA GPU)

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆或下载项目文件
cd YeePay

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 安装ComfyUI

```bash
# 克隆ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 安装ComfyUI依赖
pip install -r requirements.txt
```

### 3. 下载模型文件

将以下模型文件放入ComfyUI对应目录：

```
ComfyUI/
├── models/
│   ├── unet/
│   │   └── flux1-dev-kontext_fp8_scaled.safetensors
│   ├── clip/
│   │   ├── clip_l.safetensors
│   │   └── t5xxl_fp8_e4m3fn_scaled.safetensors
│   └── vae/
│       └── ae.safetensors
```

### 4. 启动服务

```bash
# 1. 启动ComfyUI (新终端)
cd ComfyUI
python main.py --api-only

# 2. 启动后端服务 (新终端)
cd YeePay
python start_server.py
```

### 5. 访问服务

- **前端界面**: http://localhost:9000/frontend.html
- **API文档**: http://localhost:9000/docs
- **健康检查**: http://localhost:9000/api/health

## 📖 API 文档

### 生成图像

```http
POST /api/generate-image
Content-Type: multipart/form-data

reference_image: [文件]
description: "文本描述"
steps: 20
cfg: 1.0
guidance: 2.5
seed: [可选]
```

**响应:**
```json
{
    "task_id": "uuid",
    "status": "pending",
    "message": "任务已提交"
}
```

### 查询任务状态

```http
GET /api/task/{task_id}
```

**响应:**
```json
{
    "task_id": "uuid",
    "status": "completed",
    "progress": 100,
    "result": {
        "image_url": "/api/image/uuid",
        "preview_url": "/api/image/uuid"
    },
    "error": null
}
```

### 获取生成图像

```http
GET /api/image/{task_id}
```

返回图像文件。

### 获取历史记录

```http
GET /api/history?limit=50
```

**响应:**
```json
{
    "tasks": [
        {
            "task_id": "uuid",
            "created_at": "2024-01-01T00:00:00Z",
            "description": "文本描述",
            "status": "completed",
            "result_url": "/api/image/uuid"
        }
    ]
}
```

## ⚙️ 配置说明

### 环境变量

```bash
# 服务器配置
HOST=0.0.0.0
PORT=9000
DEBUG=false

# ComfyUI配置
COMFYUI_URL=http://127.0.0.1:8188
COMFYUI_TIMEOUT=300

# 文件配置
MAX_FILE_SIZE=10485760  # 10MB

# 任务配置
MAX_CONCURRENT_TASKS=3
TASK_CLEANUP_DAYS=7

# 安全配置
CORS_ORIGINS=*
API_KEY=your_secret_key  # 可选
```

### 参数说明

| 参数 | 说明 | 范围 | 默认值 |
|------|------|------|--------|
| steps | 生成步数 | 1-50 | 20 |
| cfg | CFG Scale | 0.1-20.0 | 1.0 |
| guidance | 引导强度 | 0.1-10.0 | 2.5 |
| seed | 随机种子 | 任意整数 | 随机 |

## 🔧 高级配置

### 自定义工作流

1. 修改 `flux_kontext_dev_basic.json` 文件
2. 更新 `WorkflowTemplate.customize_workflow()` 方法
3. 重启服务

### 数据库配置

默认使用SQLite，可配置为PostgreSQL：

```python
# config.py
DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

### 负载均衡

使用Nginx进行负载均衡：

```nginx
upstream backend {
    server 127.0.0.1:9000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

## 🐳 Docker 部署

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 9000

CMD ["python", "start_server.py"]
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "9000:9000"
    environment:
      - COMFYUI_URL=http://comfyui:8188
    depends_on:
      - comfyui
  
  comfyui:
    image: comfyui:latest
    ports:
      - "8188:8188"
    volumes:
      - ./models:/app/models
```

## 🔍 故障排除

### 常见问题

**1. ComfyUI连接失败**
```bash
# 检查ComfyUI是否运行
curl http://localhost:8188/system_stats

# 检查防火墙设置
# 确保8188端口开放
```

**2. 模型加载失败**
```bash
# 检查模型文件路径
# 确保模型文件完整下载
# 检查文件权限
```

**3. 内存不足**
```bash
# 减少并发任务数
MAX_CONCURRENT_TASKS=1

# 使用较小的模型
# 调整生成参数
```

**4. 生成速度慢**
- 检查GPU使用率
- 优化生成参数
- 使用更快的采样器

### 日志查看

```bash
# 查看应用日志
tail -f app.log

# 查看ComfyUI日志
# 在ComfyUI终端查看输出
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的图像生成工作流工具
- [Flux](https://github.com/black-forest-labs/flux) - 高质量的图像生成模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架

## 📞 支持

如有问题或建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索 [Issues](https://github.com/your-repo/issues)
3. 创建新的 [Issue](https://github.com/your-repo/issues/new)

---

**享受创作的乐趣！** 🎨✨