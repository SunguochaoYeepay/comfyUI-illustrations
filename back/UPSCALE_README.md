# 🖼️ 图像高清放大服务

基于 ComfyUI 工作流的图像高清放大服务，支持多种高质量放大算法。

## ✨ 功能特性

- 🎯 **单图放大**: 支持单张图像的高清放大
- 🔧 **多种算法**: RealESRGAN、SwinIR、Lanczos 插值
- 📏 **灵活倍数**: 支持 2x、3x、4x 放大倍数
- 🚀 **异步处理**: 基于任务队列的异步处理
- 📊 **状态跟踪**: 实时任务状态查询
- 🧹 **自动清理**: 支持任务文件自动清理

## 🏗️ 架构设计

```
用户请求 → FastAPI → UpscaleManager → ComfyUI → 放大结果
    ↓           ↓           ↓           ↓         ↓
  上传图像    API路由    工作流管理    RealESRGAN  高清图像
```

### 核心组件

- **UpscaleManager**: 放大任务管理器
- **ComfyUI Client**: ComfyUI API 客户端
- **Workflow Template**: 放大工作流模板
- **API Routes**: RESTful API 接口

## 📋 API 接口

### 1. 图像放大

```http
POST /api/upscale/
Content-Type: multipart/form-data

image: [图像文件]
scale_factor: 2
algorithm: realesrgan
```

**响应:**
```json
{
    "task_id": "uuid",
    "status": "processing",
    "message": "放大任务已提交，正在处理中",
    "scale_factor": 2,
    "algorithm": "realesrgan"
}
```

### 2. 查询任务状态

```http
GET /api/upscale/{task_id}
```

**响应:**
```json
{
    "task_id": "uuid",
    "status": "completed",
    "progress": 100,
    "result": {
        "original_image": "path/to/original.png",
        "upscaled_images": ["path/to/upscaled.png"],
        "output_dir": "path/to/output"
    }
}
```

### 3. 获取可用算法

```http
GET /api/upscale/algorithms/list
```

**响应:**
```json
{
    "algorithms": [
        {
            "name": "realesrgan",
            "display_name": "RealESRGAN",
            "description": "基于ESRGAN的高质量图像超分辨率算法",
            "supported_scales": [2, 3, 4],
            "quality": "high",
            "speed": "medium"
        }
    ],
    "total": 3
}
```

### 4. 批量放大

```http
POST /api/upscale/batch
Content-Type: multipart/form-data

images: [图像文件1, 图像文件2, ...]
scale_factor: 2
algorithm: realesrgan
```

### 5. 清理任务

```http
DELETE /api/upscale/{task_id}
```

## 🔧 支持的算法

### Lanczos 插值
- **质量**: 高
- **速度**: 快
- **适用场景**: 照片和图像的高质量放大
- **支持倍数**: 2x, 3x, 4x

### 双三次插值 (Bicubic)
- **质量**: 中等
- **速度**: 快
- **适用场景**: 平衡质量和速度的通用放大
- **支持倍数**: 2x, 3x, 4x

### 双线性插值 (Bilinear)
- **质量**: 中等
- **速度**: 很快
- **适用场景**: 快速放大，适合实时处理
- **支持倍数**: 2x, 3x, 4x

### 最近邻插值 (Nearest)
- **质量**: 低
- **速度**: 最快
- **适用场景**: 保持像素边界的快速放大
- **支持倍数**: 2x, 3x, 4x

## 🚀 使用示例

### Python 客户端示例

```python
import aiohttp
import asyncio

async def upscale_image():
    url = "http://localhost:9000/api/upscale/"
    
    # 准备文件数据
    data = aiohttp.FormData()
    data.add_field('image', 
                   open('input.png', 'rb'),
                   filename='input.png',
                   content_type='image/png')
    data.add_field('scale_factor', '2')
    data.add_field('algorithm', 'lanczos')
    
    async with aiohttp.ClientSession() as session:
        # 提交放大任务
        async with session.post(url, data=data) as response:
            result = await response.json()
            task_id = result['task_id']
            print(f"任务ID: {task_id}")
        
        # 轮询任务状态
        while True:
            async with session.get(f"{url}{task_id}") as response:
                status = await response.json()
                if status['status'] == 'completed':
                    print(f"放大完成: {status['result']}")
                    break
                await asyncio.sleep(2)

# 运行示例
asyncio.run(upscale_image())
```

### cURL 示例

```bash
# 提交放大任务
curl -X POST "http://localhost:9000/api/upscale/" \
  -F "image=@input.png" \
  -F "scale_factor=2" \
  -F "algorithm=lanczos"

# 查询任务状态
curl "http://localhost:9000/api/upscale/{task_id}"

# 获取可用算法
curl "http://localhost:9000/api/upscale/algorithms/list"
```

## ⚙️ 配置说明

### 环境变量

```bash
# ComfyUI 服务地址
COMFYUI_URL=http://127.0.0.1:8188

# 输出目录
OUTPUT_DIR=./outputs

# 上传目录
UPLOAD_DIR=./uploads

# 最大文件大小 (字节)
MAX_FILE_SIZE=10485760
```

### 工作流配置

放大工作流模板位于 `upscale_workflow_simple.json`，包含以下节点：

1. **LoadImage**: 加载输入图像
2. **ImageScale**: 执行放大（使用内置插值算法）
3. **SaveImage**: 保存放大结果
4. **PreviewImage**: 预览放大结果

## 🔍 故障排除

### 常见问题

**1. ComfyUI 连接失败**
```bash
# 检查 ComfyUI 是否运行
curl http://localhost:8188/system_stats

# 检查防火墙设置
# 确保 8188 端口开放
```

**2. 放大模型未找到**
```bash
# 检查模型文件路径
# 确保模型文件完整下载
# 检查文件权限
```

**3. 内存不足**
```bash
# 减少并发任务数
# 使用较小的放大倍数
# 选择更快的算法
```

**4. 放大速度慢**
- 检查 GPU 使用率
- 使用更快的算法 (Nearest > Bilinear > Bicubic > Lanczos)
- 减少放大倍数

### 日志查看

```bash
# 查看应用日志
tail -f app.log

# 查看 ComfyUI 日志
# 在 ComfyUI 终端查看输出
```

## 🧪 测试

运行测试脚本验证服务功能：

```bash
cd back
python test_upscale.py
```

测试内容包括：
- API 接口可用性
- 工作流文件完整性
- 放大管理器功能
- 服务健康状态

## 📝 注意事项

1. **文件格式**: 支持 PNG、JPG、JPEG、WEBP 格式
2. **文件大小**: 默认最大 10MB
3. **放大倍数**: 建议不超过 4x，避免内存不足
4. **并发限制**: 根据硬件配置调整并发任务数
5. **存储空间**: 确保有足够的磁盘空间存储放大结果

## 🔄 更新日志

### v1.0.0
- 初始版本发布
- 支持 Lanczos、Bicubic、Bilinear、Nearest 内置算法
- 提供完整的 RESTful API
- 支持单图和批量放大
- 异步任务处理
