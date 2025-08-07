# YeePay 图片生成系统部署指南

## 本地开发环境

### 1. 环境要求
- Python 3.11+
- ComfyUI 服务运行在 `http://127.0.0.1:8188`

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 环境变量配置
复制 `env.example` 为 `.env` 并配置：
```bash
cp env.example .env
```

### 4. 启动服务
```bash
python main.py
```

服务将在 `http://localhost:9000` 启动。

## Docker 部署

### 1. 使用 Docker Compose（推荐）

#### 1.1 创建必要的目录
```bash
mkdir -p comfyui_output uploads outputs data models
```

#### 1.2 启动服务
```bash
docker-compose up -d
```

#### 1.3 查看日志
```bash
docker-compose logs -f yeepay-backend
```

### 2. 手动 Docker 部署

#### 2.1 构建镜像
```bash
docker build -t yeepay-backend .
```

#### 2.2 运行容器
```bash
docker run -d \
  --name yeepay-backend \
  -p 9000:9000 \
  -v $(pwd)/comfyui_output:/app/comfyui/output \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/data:/app/data \
  -e ENVIRONMENT=docker \
  -e COMFYUI_URL=http://your-comfyui-host:8188 \
  yeepay-backend
```

## 路径映射说明

### 本地开发环境
- **上传目录**: `./uploads/`
- **输出目录**: `./outputs/`
- **ComfyUI输出**: `D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output/`
- **数据库**: `./tasks.db`

### Docker环境
- **上传目录**: `/app/uploads/` (映射到 `./uploads/`)
- **输出目录**: `/app/outputs/` (映射到 `./outputs/`)
- **ComfyUI输出**: `/app/comfyui/output/` (映射到 `./comfyui_output/`)
- **数据库**: `/app/data/tasks.db` (映射到 `./data/tasks.db`)

## 环境变量配置

| 变量名 | 本地开发 | Docker | 说明 |
|--------|----------|--------|------|
| `ENVIRONMENT` | `local` | `docker` | 环境标识 |
| `COMFYUI_URL` | `http://127.0.0.1:8188` | `http://comfyui:8188` | ComfyUI服务地址 |
| `COMFYUI_OUTPUT_DIR` | `D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output/yeepay` | `/app/comfyui/output/yeepay` | 项目输出目录 |
| `COMFYUI_MAIN_OUTPUT_DIR` | `D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output` | `/app/comfyui/output` | ComfyUI主输出目录 |

## 注意事项

1. **路径映射**: Docker部署时，确保ComfyUI的输出目录与后端应用的输出目录正确映射
2. **权限问题**: 确保Docker容器有足够的权限访问映射的目录
3. **网络连接**: Docker环境中，ComfyUI服务地址需要使用容器名称或IP地址
4. **数据持久化**: 重要数据目录都已映射到宿主机，确保数据安全

## 故障排除

### 1. 文件复制失败
- 检查ComfyUI输出目录是否存在且有写权限
- 确认路径映射是否正确

### 2. ComfyUI连接失败
- 检查ComfyUI服务是否正常运行
- 确认网络连接和端口配置

### 3. 数据库错误
- 检查数据库文件权限
- 确认数据目录映射正确
