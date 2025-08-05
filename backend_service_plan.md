# 基于Flux Kontext的图像生成后端服务架构规划

## 1. 工作流分析

### 当前JSON工作流功能：
- **模型加载**：使用Flux1-dev-kontext模型进行图像生成
- **参考图像处理**：通过LoadImageOutput和ImageStitch处理参考图像
- **文本编码**：使用CLIP对文本描述进行编码
- **图像生成**：结合参考图像和文本描述生成新图像
- **输出保存**：生成的图像保存为文件

### 关键节点分析：
- **节点6**：文本编码器，处理用户输入的描述
- **节点142**：加载参考图像
- **节点177**：ReferenceLatent，结合参考图像和文本
- **节点31**：K采样器，核心生成节点
- **节点136**：保存生成的图像

## 2. 后端服务架构设计

### 2.1 技术栈选择
```
后端框架：FastAPI (Python)
ComfyUI集成：ComfyUI API
文件存储：本地存储 + 可选云存储
数据库：SQLite/PostgreSQL (任务记录)
消息队列：Redis (可选，用于异步处理)
```

### 2.2 服务架构图
```
前端页面
    ↓
API Gateway (FastAPI)
    ↓
任务管理器
    ↓
ComfyUI工作流执行器
    ↓
文件存储系统
```

## 3. API接口设计

### 3.1 图像生成接口
```python
POST /api/generate-image

请求参数：
{
    "reference_image": "base64编码的图像或图像URL",
    "description": "文本描述",
    "parameters": {
        "steps": 20,
        "cfg": 1,
        "guidance": 2.5,
        "seed": null  // null表示随机
    }
}

响应：
{
    "task_id": "uuid",
    "status": "pending",
    "message": "任务已提交"
}
```

### 3.2 任务状态查询接口
```python
GET /api/task/{task_id}

响应：
{
    "task_id": "uuid",
    "status": "completed|pending|failed",
    "progress": 100,
    "result": {
        "image_url": "生成图像的URL",
        "preview_url": "预览图像的URL"
    },
    "error": null
}
```

### 3.3 历史记录接口
```python
GET /api/history

响应：
{
    "tasks": [
        {
            "task_id": "uuid",
            "created_at": "2024-01-01T00:00:00Z",
            "description": "文本描述",
            "status": "completed",
            "result_url": "图像URL"
        }
    ]
}
```

## 4. 核心组件实现

### 4.1 工作流模板管理器
```python
class WorkflowTemplate:
    def __init__(self, template_path):
        self.template = self.load_template(template_path)
    
    def customize_workflow(self, reference_image, description, parameters):
        # 动态修改工作流参数
        workflow = self.template.copy()
        
        # 更新文本描述
        workflow["6"]["inputs"]["text"] = description
        
        # 更新参考图像
        workflow["142"]["inputs"]["image"] = reference_image
        
        # 更新生成参数
        if parameters.get("steps"):
            workflow["31"]["inputs"]["steps"] = parameters["steps"]
        if parameters.get("cfg"):
            workflow["31"]["inputs"]["cfg"] = parameters["cfg"]
        if parameters.get("guidance"):
            workflow["35"]["inputs"]["guidance"] = parameters["guidance"]
        if parameters.get("seed"):
            workflow["31"]["inputs"]["seed"] = parameters["seed"]
        
        return workflow
```

### 4.2 ComfyUI集成器
```python
class ComfyUIClient:
    def __init__(self, comfyui_url):
        self.base_url = comfyui_url
        self.session = requests.Session()
    
    async def submit_workflow(self, workflow):
        # 提交工作流到ComfyUI
        response = await self.session.post(
            f"{self.base_url}/prompt",
            json={"prompt": workflow}
        )
        return response.json()["prompt_id"]
    
    async def get_task_status(self, prompt_id):
        # 查询任务状态
        response = await self.session.get(
            f"{self.base_url}/history/{prompt_id}"
        )
        return response.json()
    
    async def get_generated_image(self, prompt_id):
        # 获取生成的图像
        history = await self.get_task_status(prompt_id)
        if prompt_id in history:
            outputs = history[prompt_id]["outputs"]
            # 从outputs中提取图像信息
            return outputs
        return None
```

### 4.3 任务管理器
```python
class TaskManager:
    def __init__(self, db_connection, comfyui_client):
        self.db = db_connection
        self.comfyui = comfyui_client
    
    async def create_task(self, reference_image, description, parameters):
        task_id = str(uuid.uuid4())
        
        # 保存任务到数据库
        await self.db.execute(
            "INSERT INTO tasks (id, status, description, created_at) VALUES (?, ?, ?, ?)",
            (task_id, "pending", description, datetime.now())
        )
        
        # 异步执行任务
        asyncio.create_task(self.execute_task(task_id, reference_image, description, parameters))
        
        return task_id
    
    async def execute_task(self, task_id, reference_image, description, parameters):
        try:
            # 更新状态为处理中
            await self.update_task_status(task_id, "processing")
            
            # 准备工作流
            workflow_template = WorkflowTemplate("flux_kontext_dev_basic.json")
            workflow = workflow_template.customize_workflow(
                reference_image, description, parameters
            )
            
            # 提交到ComfyUI
            prompt_id = await self.comfyui.submit_workflow(workflow)
            
            # 等待完成并获取结果
            result = await self.wait_for_completion(prompt_id)
            
            # 更新任务状态
            await self.update_task_status(task_id, "completed", result)
            
        except Exception as e:
            await self.update_task_status(task_id, "failed", error=str(e))
```

## 5. 前端集成建议

### 5.1 页面功能
- 参考图像上传区域
- 文本描述输入框
- 高级参数设置（可折叠）
- 生成按钮
- 结果展示区域
- 历史记录列表

### 5.2 用户体验优化
- 实时进度显示
- 预览图像展示
- 参数预设模板
- 批量生成功能
- 结果对比功能

## 6. 部署建议

### 6.1 开发环境
```bash
# 安装依赖
pip install fastapi uvicorn sqlalchemy aiofiles pillow

# 启动ComfyUI
cd ComfyUI
python main.py --api-only

# 启动后端服务
uvicorn main:app --reload --port 8000
```

### 6.2 生产环境
- 使用Docker容器化部署
- 配置负载均衡
- 设置文件存储CDN
- 监控和日志系统

## 7. 扩展功能

### 7.1 短期扩展
- 多种模型支持
- 批量处理
- 用户管理系统
- API限流

### 7.2 长期扩展
- 模型微调功能
- 风格迁移
- 视频生成
- 社区分享功能

这个架构设计充分利用了现有的ComfyUI工作流，提供了灵活的API接口，支持前端的各种需求。