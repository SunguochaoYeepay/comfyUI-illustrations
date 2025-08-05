# Flux Kontext 后端服务

基于 FastAPI 的 AI 图像生成后端服务，支持批量生成和参考图像引导。

## 功能特性

- 🎨 基于参考图像的 AI 图像生成
- 📦 支持批量生成（1-4张图像）
- 🔄 异步任务处理
- 📊 实时进度跟踪
- 💾 SQLite 数据库存储
- 🌐 CORS 跨域支持
- 📁 文件上传和管理

## 目录结构

```
back/
├── main.py                 # 主应用文件
├── config.py              # 配置文件
├── run.py                 # 启动脚本
├── start_server.py        # 服务器启动检查
├── flux_kontext_dev_basic.json  # ComfyUI 工作流模板
├── requirements.txt       # Python 依赖
├── check_task.py         # 任务检查工具
├── fix_existing_tasks.py # 任务修复工具
├── manual_fix.py         # 手动修复工具
└── test_image_access.py  # 图像访问测试
```

## 快速开始

### 1. 安装依赖

```bash
cd back
pip install -r requirements.txt
```

### 2. 启动 ComfyUI

确保 ComfyUI 在 `http://127.0.0.1:8188` 运行

### 3. 启动后端服务

```bash
python run.py
```

或者使用原始方式：

```bash
python main.py
```

### 4. 访问服务

- API 文档: http://localhost:9000/docs
- 健康检查: http://localhost:9000/health

## API 接口

### 生成图像

```http
POST /generate-image
Content-Type: multipart/form-data

referenceImage: [文件]
description: "图像描述"
count: 2
size: "1024x1024"
steps: 20
seed: 12345
```

### 查询任务状态

```http
GET /api/task-status/{task_id}
```

### 获取生成的图像

```http
GET /api/image/{task_id}?index=0
```

## 配置说明

主要配置项在 `config.py` 中：

- `COMFYUI_URL`: ComfyUI 服务地址
- `HOST` / `PORT`: 服务监听地址和端口
- `MAX_FILE_SIZE`: 最大文件上传大小
- `MAX_CONCURRENT_TASKS`: 最大并发任务数

## 环境变量

```bash
# 服务配置
HOST=0.0.0.0
PORT=9000
DEBUG=false

# ComfyUI 配置
COMFYUI_URL=http://127.0.0.1:8188
COMFYUI_TIMEOUT=300

# 文件配置
MAX_FILE_SIZE=10485760  # 10MB

# 任务配置
MAX_CONCURRENT_TASKS=3
TASK_CLEANUP_DAYS=7
```

## 故障排除

### 常见问题

1. **ComfyUI 连接失败**
   - 检查 ComfyUI 是否正常运行
   - 确认端口 8188 未被占用

2. **工作流文件不存在**
   - 确保 `flux_kontext_dev_basic.json` 在当前目录

3. **文件上传失败**
   - 检查文件大小是否超过限制
   - 确认文件格式是否支持

### 调试工具

```bash
# 检查任务状态
python check_task.py

# 修复现有任务
python fix_existing_tasks.py

# 测试图像访问
python test_image_access.py
```

## 开发说明

### 数据库结构

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    description TEXT,
    status TEXT,
    progress INTEGER,
    result_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 任务状态

- `pending`: 等待处理
- `processing`: 正在处理
- `completed`: 处理完成
- `failed`: 处理失败

### 批量生成逻辑

后端支持根据 `count` 参数循环调用 ComfyUI 工作流，每次生成一张图像，最终将所有结果路径以 JSON 格式存储。