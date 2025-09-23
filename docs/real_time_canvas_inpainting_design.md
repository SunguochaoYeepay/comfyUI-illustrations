# 实时画布局部重绘系统设计文档

## 项目概述

基于ComfyUI Qwen-Edit工作流实现的专业图像编辑系统，提供类似专业图像编辑软件的实时画布界面，支持用户直接在图像上进行框选操作，实现局部重绘、图像编辑等AI功能。使用千问图像编辑模型，支持高质量的图像局部修改。

## 系统架构

```
前端画布界面 → 遮罩生成 → ComfyUI API → 结果返回 → 实时更新画布
```

### 核心组件

1. **实时画布系统** - 用户交互界面
2. **遮罩处理引擎** - 框选区域转遮罩
3. **ComfyUI集成层** - 工作流调用
4. **结果处理系统** - 图像更新和预览

## 技术栈

### 前端技术
- **Vue 3** - 主框架
- **Fabric.js** - 专业画布操作库
- **Canvas API** - 底层图像处理
- **WebGL** - 高性能渲染
- **TypeScript** - 类型安全

### 后端技术
- **FastAPI** - API服务
- **ComfyUI** - AI工作流引擎
- **OpenCV** - 图像处理
- **PIL/Pillow** - 图像格式转换

## 功能模块设计

### 1. 实时画布系统

#### 1.1 画布组件 (CanvasComponent.vue)
```vue
<template>
  <div class="canvas-container">
    <div class="toolbar">
      <button @click="selectTool('select')">选择</button>
      <button @click="selectTool('brush')">画笔</button>
      <button @click="selectTool('rectangle')">矩形框选</button>
      <button @click="selectTool('polygon')">多边形</button>
      <button @click="executeInpainting">局部重绘</button>
      <button @click="executeOutpainting">扩图</button>
    </div>
    <canvas ref="canvas" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp"></canvas>
  </div>
</template>
```

#### 1.2 核心功能
- **图像加载和显示**
- **多种选择工具** (矩形、多边形、画笔)
- **实时预览** (框选区域高亮)
- **撤销/重做** 功能
- **缩放和平移**

### 2. 遮罩处理引擎

#### 2.1 遮罩生成算法
```javascript
class MaskGenerator {
  // 矩形框选转遮罩
  generateRectMask(rect, imageSize) {
    const mask = new ImageData(imageSize.width, imageSize.height);
    const { x, y, width, height } = rect;
    
    for (let i = y; i < y + height; i++) {
      for (let j = x; j < x + width; j++) {
        const index = (i * imageSize.width + j) * 4;
        mask.data[index] = 255;     // R
        mask.data[index + 1] = 255; // G
        mask.data[index + 2] = 255; // B
        mask.data[index + 3] = 255; // A
      }
    }
    return mask;
  }
  
  // 多边形转遮罩
  generatePolygonMask(points, imageSize) {
    // 使用射线法判断点是否在多边形内
    // 实现多边形填充算法
  }
  
  // 画笔路径转遮罩
  generateBrushMask(strokes, imageSize) {
    // 将画笔轨迹转换为遮罩
  }
}
```

#### 2.2 遮罩优化
- **羽化边缘** - 平滑遮罩边界
- **反选功能** - 反转选择区域
- **遮罩编辑** - 添加/删除区域
- **预览模式** - 实时显示遮罩效果

### 3. ComfyUI集成层

#### 3.1 API接口设计
```python
# backend/api/qwen_edit_routes.py
from fastapi import APIRouter, UploadFile, File, Form
from core.comfyui_client import ComfyUIClient

router = APIRouter()

@router.post("/qwen-edit")
async def execute_qwen_edit(
    image: UploadFile = File(...),
    mask: UploadFile = File(...),
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    steps: int = Form(8),
    cfg: float = Form(2.5),
    denoise: float = Form(1.0),
    target_size: int = Form(1024),
    lora_strength: float = Form(1.0),
    seed: int = Form(-1)
):
    """执行千问图像编辑"""
    client = ComfyUIClient()
    
    # 上传图像和遮罩
    image_path = await upload_file(image)
    mask_path = await upload_file(mask)
    
    # 调用Qwen-Edit工作流
    result = await client.execute_qwen_edit_workflow(
        image_path=image_path,
        mask_path=mask_path,
        prompt=prompt,
        negative_prompt=negative_prompt,
        steps=steps,
        cfg=cfg,
        denoise=denoise,
        target_size=target_size,
        lora_strength=lora_strength,
        seed=seed
    )
    
    return {"result_image": result}

@router.post("/qwen-edit-batch")
async def execute_qwen_edit_batch(
    images: List[UploadFile] = File(...),
    masks: List[UploadFile] = File(...),
    prompt: str = Form(...),
    **kwargs
):
    """批量执行千问图像编辑"""
    # 实现批量处理逻辑
    pass
```

#### 3.2 ComfyUI客户端
```python
# backend/core/comfyui_client.py
import requests
import json
from typing import Dict, Any

class ComfyUIClient:
    def __init__(self, base_url: str = "http://localhost:8188"):
        self.base_url = base_url
        
    async def execute_qwen_edit_workflow(self, **kwargs) -> str:
        """执行千问图像编辑工作流"""
        # 加载工作流模板
        workflow = self.load_workflow_template("qwen_edit")
        
        # 设置参数
        workflow = self.adapt_qwen_edit_workflow(workflow, kwargs)
        
        # 提交任务
        task_id = await self.submit_workflow(workflow)
        
        # 等待完成并获取结果
        result = await self.wait_for_completion(task_id)
        
        return result["output_image"]
    
    def load_workflow_template(self, workflow_type: str) -> Dict[str, Any]:
        """加载工作流模板"""
        with open(f"workflows/{workflow_type}.json", "r") as f:
            return json.load(f)
    
    def adapt_qwen_edit_workflow(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """适配千问编辑工作流参数"""
        # 设置图像路径 (节点117)
        workflow["117"]["inputs"]["image"] = params["image_path"]
        
        # 设置提示词 (节点106)
        workflow["106"]["inputs"]["text"] = params["prompt"]
        
        # 设置负面提示词 (节点77)
        workflow["77"]["inputs"]["prompt"] = params.get("negative_prompt", "")
        
        # 设置采样参数 (节点3)
        workflow["3"]["inputs"]["steps"] = params.get("steps", 8)
        workflow["3"]["inputs"]["cfg"] = params.get("cfg", 2.5)
        workflow["3"]["inputs"]["denoise"] = params.get("denoise", 1.0)
        workflow["3"]["inputs"]["seed"] = params.get("seed", -1)
        
        # 设置图像尺寸 (节点109, 126)
        target_size = params.get("target_size", 1024)
        workflow["109"]["inputs"]["size"] = target_size
        workflow["126"]["inputs"]["width"] = target_size
        workflow["126"]["inputs"]["height"] = target_size
        
        # 设置LoRA强度 (节点129)
        if params.get("lora_strength"):
            workflow["129"]["inputs"]["strength_01"] = params["lora_strength"]
        
        return workflow
```

### 4. 用户界面设计

#### 4.1 界面布局
```
┌─────────────────────────────────────────────────────────┐
│ 工具栏: [选择] [画笔] [矩形] [多边形] [千问编辑] [预览]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │           画布区域 (图像显示)                    │   │
│  │                                                 │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ 参数面板: [提示词] [负面提示词] [步数] [CFG] [去噪] [尺寸] │
└─────────────────────────────────────────────────────────┘
```

#### 4.2 千问编辑特有参数
- **采样步数** (Steps): 默认8步，范围1-50
- **CFG Scale**: 默认2.5，范围1.0-20.0
- **去噪强度** (Denoise): 默认1.0，范围0.1-1.0
- **目标尺寸** (Target Size): 默认1024，支持512/768/1024/1536
- **LoRA强度**: 默认1.0，范围0.1-2.0
- **随机种子**: 支持固定种子或随机生成

#### 4.3 交互设计
- **拖拽上传** - 支持拖拽图像文件
- **快捷键** - 常用操作快捷键
- **右键菜单** - 上下文相关操作
- **状态指示** - 处理进度和状态显示
- **实时预览** - 遮罩区域实时高亮显示
- **参数预设** - 快速应用常用参数组合

## 工作流集成

### 1. 工作流分析
基于Qwen-Edit工作流的关键节点：

#### 核心节点结构
- **节点117 (LoadImage)** - 加载图像和遮罩
  - 输入：图像文件路径
  - 输出：图像和遮罩数据
  
- **节点122 (ImageAndMaskPreview)** - 图像与遮罩预览
  - 输入：图像和遮罩
  - 输出：预览图像
  
- **节点109 (ImageScaleDownToSize)** - 图像尺寸调整
  - 输入：图像，目标尺寸1024
  - 输出：调整后的图像
  
- **节点126 (ImageScale)** - 最终图像缩放
  - 输入：调整后的图像
  - 输出：1024x1024的最终图像
  
- **节点106 (Text Multiline)** - 提示词输入
  - 输入：文本提示词
  - 输出：文本数据
  
- **节点76/77 (TextEncodeQwenImageEdit)** - 千问图像编辑文本编码
  - 输入：提示词、CLIP、VAE、图像
  - 输出：编码后的条件
  
- **节点3 (KSampler)** - 采样器
  - 输入：模型、条件、潜在图像
  - 输出：采样结果
  
- **节点8 (VAEDecode)** - VAE解码
  - 输入：潜在图像、VAE
  - 输出：最终图像

#### 模型配置
- **UNET**: qwen_image_edit_fp8_e4m3fn.safetensors
- **CLIP**: qwen_2.5_vl_7b_fp8_scaled.safetensors
- **VAE**: qwen_image_vae.safetensors
- **LoRA**: Qwen-Image-Lightning-8steps-V1.0.safetensors

### 2. 工作流适配
```python
def adapt_qwen_edit_workflow(workflow_template, params):
    """适配Qwen-Edit工作流参数"""
    
    # 设置图像路径 (节点117)
    workflow["117"]["inputs"]["image"] = params["image_path"]
    
    # 设置提示词 (节点106)
    workflow["106"]["inputs"]["text"] = params["prompt"]
    
    # 设置负面提示词 (节点77)
    workflow["77"]["inputs"]["prompt"] = params.get("negative_prompt", "")
    
    # 设置采样参数 (节点3)
    workflow["3"]["inputs"]["steps"] = params.get("steps", 8)
    workflow["3"]["inputs"]["cfg"] = params.get("cfg", 2.5)
    workflow["3"]["inputs"]["denoise"] = params.get("denoise", 1.0)
    workflow["3"]["inputs"]["seed"] = params.get("seed", -1)
    
    # 设置图像尺寸 (节点109, 126)
    target_size = params.get("target_size", 1024)
    workflow["109"]["inputs"]["size"] = target_size
    workflow["126"]["inputs"]["width"] = target_size
    workflow["126"]["inputs"]["height"] = target_size
    
    # 设置LoRA强度 (节点129)
    if params.get("lora_strength"):
        workflow["129"]["inputs"]["strength_01"] = params["lora_strength"]
    
    return workflow
```

## 开发计划

### 阶段1: 基础画布系统 (3-4天)
- [ ] 创建Vue画布组件
- [ ] 集成Fabric.js
- [ ] 实现基础选择工具
- [ ] 图像加载和显示

### 阶段2: 遮罩处理 (2-3天)
- [ ] 遮罩生成算法
- [ ] 遮罩预览功能
- [ ] 遮罩编辑工具
- [ ] 羽化和优化

### 阶段3: ComfyUI集成 (2-3天)
- [ ] API接口开发
- [ ] 工作流调用
- [ ] 结果处理
- [ ] 错误处理

### 阶段4: 界面优化 (2-3天)
- [ ] 工具栏设计
- [ ] 参数面板
- [ ] 状态管理
- [ ] 用户体验优化

### 阶段5: 测试和部署 (1-2天)
- [ ] 功能测试
- [ ] 性能优化
- [ ] 部署配置
- [ ] 文档完善

## 技术难点和解决方案

### 1. 大图像处理
**问题**: 高分辨率图像可能导致性能问题
**解决方案**: 
- 使用WebGL加速渲染
- 实现图像分块加载
- 添加图像压缩选项

### 2. 实时预览
**问题**: 框选操作需要实时反馈
**解决方案**:
- 使用Canvas离屏渲染
- 实现增量更新
- 优化重绘频率

### 3. 遮罩精度
**问题**: 复杂形状的遮罩生成
**解决方案**:
- 使用多边形填充算法
- 实现画笔路径平滑
- 添加遮罩后处理

### 4. 工作流稳定性
**问题**: ComfyUI工作流可能失败
**解决方案**:
- 实现重试机制
- 添加错误恢复
- 提供降级方案

## 性能指标

### 目标性能 (基于千问编辑模型)
- **图像加载**: < 2秒 (10MB图像)
- **框选响应**: < 100ms
- **遮罩生成**: < 500ms
- **AI处理**: < 15秒 (1024x1024, 8步采样)
- **界面响应**: < 50ms
- **模型加载**: < 5秒 (首次启动)

### 千问编辑模型优势
- **快速采样**: 仅需8步即可获得高质量结果
- **低CFG值**: 默认2.5，减少计算量
- **FP8精度**: 使用FP8量化，提升推理速度
- **Lightning LoRA**: 加速采样过程

### 优化策略
- **模型预热**: 启动时预加载模型
- **图像缓存**: 缓存处理过的图像
- **遮罩缓存**: 缓存生成的遮罩
- **异步处理**: 非阻塞式UI更新
- **内存管理**: 及时释放大图像内存
- **批量处理**: 支持多图像同时处理

## 安全考虑

### 1. 文件上传安全
- 文件类型验证
- 文件大小限制
- 恶意文件检测

### 2. API安全
- 请求频率限制
- 参数验证
- 错误信息过滤

### 3. 数据隐私
- 临时文件清理
- 用户数据保护
- 日志脱敏

## 部署方案

### 开发环境
```bash
# 前端开发
cd frontend
npm run dev

# 后端开发
cd backend
python -m uvicorn main:app --reload

# ComfyUI
python main.py --listen
```

### 生产环境
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - comfyui
  
  comfyui:
    image: comfyui:latest
    ports:
      - "8188:8188"
    volumes:
      - ./models:/models
      - ./workflows:/workflows
```

## 总结

这个基于千问编辑模型的实时画布局部重绘系统将提供专业级的图像编辑体验。相比传统方案，千问编辑模型具有以下优势：

### 技术优势
- **高效采样**: 8步采样即可获得高质量结果，大幅提升处理速度
- **智能理解**: 千问模型对中文提示词理解更准确
- **FP8量化**: 使用FP8精度，在保证质量的同时提升推理速度
- **Lightning加速**: 集成Lightning LoRA，进一步优化性能

### 用户体验
- **快速响应**: 15秒内完成1024x1024图像编辑
- **直观操作**: 专业级画布界面，支持多种选择工具
- **实时预览**: 框选区域实时高亮，所见即所得
- **参数丰富**: 支持步数、CFG、去噪强度等精细调节

### 应用场景
- **内容创作**: 快速修改图像局部内容
- **设计工作**: 专业设计师的辅助工具
- **批量处理**: 支持多图像同时编辑
- **创意实验**: 快速验证设计想法

通过模块化设计和渐进式开发，可以快速实现核心功能并持续优化用户体验，为用户提供高效、专业的AI图像编辑解决方案。
