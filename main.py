from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import aiohttp
import json
import uuid
import os
import base64
from datetime import datetime
import sqlite3
from contextlib import asynccontextmanager
import aiofiles
from pathlib import Path

# 数据模型
class GenerateImageRequest(BaseModel):
    description: str
    parameters: Optional[Dict[str, Any]] = {
        "count": 1,
        "size": "512x512",
        "steps": 20,
        "seed": None
    }

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    result: Optional[Dict[str, str]] = None
    error: Optional[str] = None

# 全局变量
COMFYUI_URL = "http://127.0.0.1:8188"
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
DB_PATH = "tasks.db"

# 确保目录存在
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

class WorkflowTemplate:
    def __init__(self, template_path: str):
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = json.load(f)
    
    def customize_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]):
        """自定义工作流参数"""
        workflow = json.loads(json.dumps(self.template))  # 深拷贝
        
        # 更新文本描述
        workflow["6"]["inputs"]["text"] = description
        
        # 更新参考图像路径 - LoadImageOutput需要相对于ComfyUI输出目录的文件名
        # 我们需要将图像复制到ComfyUI的输出目录
        import shutil
        from pathlib import Path
        
        # 获取文件名
        image_filename = Path(reference_image_path).name
        
        # ComfyUI输出目录路径（假设ComfyUI在同级目录）
        comfyui_output_dir = Path("../ComfyUI/output")
        if not comfyui_output_dir.exists():
            # 尝试其他可能的路径
            comfyui_output_dir = Path("D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output")
        
        if comfyui_output_dir.exists():
            # 复制图像到ComfyUI输出目录
            dest_path = comfyui_output_dir / image_filename
            shutil.copy2(reference_image_path, dest_path)
            workflow["142"]["inputs"]["image"] = f"{image_filename} [output]"
        else:
            # 如果找不到ComfyUI输出目录，使用绝对路径（可能不工作）
            workflow["142"]["inputs"]["image"] = reference_image_path
        
        # 更新生成参数
        if parameters.get("steps"):
            workflow["31"]["inputs"]["steps"] = parameters["steps"]
        
        # 处理图像尺寸
        if parameters.get("size"):
            # 解析尺寸字符串 (例如: "512x512")
            try:
                width, height = map(int, parameters["size"].split('x'))
                # 注意：当前工作流模板可能需要根据具体的ComfyUI节点来调整尺寸设置
                # 这里先记录参数，实际的尺寸调整可能需要修改工作流模板
            except ValueError:
                pass  # 如果解析失败，使用默认尺寸
        
        # 处理生成数量
        count = parameters.get("count", 1)
        # 注意：批量生成可能需要修改工作流模板的相关节点
        
        if parameters.get("seed"):
            workflow["31"]["inputs"]["seed"] = parameters["seed"]
        else:
            # 生成随机种子
            import random
            workflow["31"]["inputs"]["seed"] = random.randint(1, 2**32 - 1)
        
        return workflow

class ComfyUIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def submit_workflow(self, workflow: Dict[str, Any]) -> str:
        """提交工作流到ComfyUI"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow}
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Failed to submit workflow to ComfyUI")
                result = await response.json()
                return result["prompt_id"]
    
    async def get_task_status(self, prompt_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/history/{prompt_id}"
            ) as response:
                if response.status != 200:
                    return {"status": "unknown"}
                return await response.json()
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/queue"
            ) as response:
                if response.status != 200:
                    return {"queue_running": [], "queue_pending": []}
                return await response.json()

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                description TEXT,
                reference_image_path TEXT,
                parameters TEXT,
                prompt_id TEXT,
                result_path TEXT,
                error TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def create_task(self, task_id: str, description: str, reference_image_path: str, parameters: Dict[str, Any]) -> None:
        """创建任务记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, status, description, reference_image_path, parameters, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, "pending", description, reference_image_path, 
            json.dumps(parameters), datetime.now(), datetime.now()
        ))
        conn.commit()
        conn.close()
    
    def update_task_status(self, task_id: str, status: str, prompt_id: str = None, result_path: str = None, error: str = None) -> None:
        """更新任务状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ["status = ?", "updated_at = ?"]
        values = [status, datetime.now()]
        
        if prompt_id:
            update_fields.append("prompt_id = ?")
            values.append(prompt_id)
        if result_path:
            update_fields.append("result_path = ?")
            values.append(result_path)
        if error:
            update_fields.append("error = ?")
            values.append(error)
        
        values.append(task_id)
        
        cursor.execute(f"""
            UPDATE tasks SET {', '.join(update_fields)}
            WHERE id = ?
        """, values)
        conn.commit()
        conn.close()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_all_tasks(self, limit: int = 50) -> list:
        """获取所有任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]

class TaskManager:
    def __init__(self, db_manager: DatabaseManager, comfyui_client: ComfyUIClient, workflow_template: WorkflowTemplate):
        self.db = db_manager
        self.comfyui = comfyui_client
        self.workflow_template = workflow_template
    
    async def create_task(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        
        # 保存任务到数据库
        self.db.create_task(task_id, description, reference_image_path, parameters)
        
        # 异步执行任务
        asyncio.create_task(self.execute_task(task_id, reference_image_path, description, parameters))
        
        return task_id
    
    async def execute_task(self, task_id: str, reference_image_path: str, description: str, parameters: Dict[str, Any]):
        """执行任务"""
        try:
            # 更新状态为处理中
            self.db.update_task_status(task_id, "processing")
            
            # 准备工作流
            workflow = self.workflow_template.customize_workflow(
                reference_image_path, description, parameters
            )
            
            # 提交到ComfyUI
            prompt_id = await self.comfyui.submit_workflow(workflow)
            self.db.update_task_status(task_id, "processing", prompt_id=prompt_id)
            
            # 等待完成
            result_path = await self.wait_for_completion(task_id, prompt_id)
            
            if result_path:
                self.db.update_task_status(task_id, "completed", result_path=result_path)
            else:
                self.db.update_task_status(task_id, "failed", error="No output generated")
                
        except Exception as e:
            self.db.update_task_status(task_id, "failed", error=str(e))
    
    async def wait_for_completion(self, task_id: str, prompt_id: str, max_wait_time: int = 300) -> Optional[str]:
        """等待任务完成"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < max_wait_time:
            try:
                history = await self.comfyui.get_task_status(prompt_id)
                
                if prompt_id in history:
                    task_info = history[prompt_id]
                    if "outputs" in task_info:
                        # 任务完成，查找输出图像
                        outputs = task_info["outputs"]
                        for node_id, output in outputs.items():
                            if "images" in output:
                                # 找到图像输出
                                image_info = output["images"][0]
                                filename = image_info['filename']
                                
                                # 从ComfyUI输出目录复制文件到项目outputs目录
                                import shutil
                                comfyui_output_dir = Path("D:\\AI-Image\\ComfyUI-aki-v1.6\\ComfyUI\\output")
                                source_path = comfyui_output_dir / filename
                                dest_path = OUTPUT_DIR / filename
                                
                                if source_path.exists():
                                    shutil.copy2(source_path, dest_path)
                                    return f"outputs/{filename}"
                                else:
                                    # 尝试查找类似的文件名
                                    try:
                                        # 查找所有ComfyUI开头的png文件
                                        pattern = "ComfyUI*.png"
                                        matching_files = list(comfyui_output_dir.glob(pattern))
                                        
                                        if matching_files:
                                            # 使用最新的文件
                                            latest_file = max(matching_files, key=lambda f: f.stat().st_mtime)
                                            
                                            # 复制最新文件
                                            dest_path = OUTPUT_DIR / latest_file.name
                                            shutil.copy2(latest_file, dest_path)
                                            return f"outputs/{latest_file.name}"
                                        else:
                                            return None
                                    except Exception:
                                        return None
                        return None
                
                # 检查是否还在队列中
                queue_status = await self.comfyui.get_queue_status()
                queue_running = queue_status.get("queue_running", [])
                queue_pending = queue_status.get("queue_pending", [])
                
                # 检查任务是否还在队列中
                in_queue = any(item[1] == prompt_id for item in queue_running + queue_pending)
                if not in_queue and prompt_id not in history:
                    # 任务不在队列中也不在历史中，可能失败了
                    break
                
                await asyncio.sleep(2)  # 等待2秒后再检查
                
            except Exception:
                await asyncio.sleep(5)
        
        return None
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self.db.get_task(task_id)

# 初始化组件
db_manager = DatabaseManager(DB_PATH)
comfyui_client = ComfyUIClient(COMFYUI_URL)
workflow_template = WorkflowTemplate("flux_kontext_dev_basic.json")
task_manager = TaskManager(db_manager, comfyui_client, workflow_template)

# 创建FastAPI应用
app = FastAPI(title="Flux Kontext Image Generation API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="."), name="static")

# 添加前端页面路由
@app.get("/frontend.html")
async def get_frontend():
    """返回前端页面"""
    return FileResponse("frontend.html")

@app.get("/")
async def root():
    """根路径重定向到前端页面"""
    return FileResponse("frontend.html")

@app.post("/api/generate-image", response_model=TaskResponse)
async def generate_image(
    description: str = Form(...),
    reference_image: UploadFile = File(...),
    count: int = Form(1),
    size: str = Form("512x512"),
    steps: int = Form(20),
    seed: Optional[int] = Form(None)
):
    """生成图像API"""
    try:
        # 保存上传的参考图像
        image_filename = f"{uuid.uuid4()}_{reference_image.filename}"
        image_path = UPLOAD_DIR / image_filename
        
        async with aiofiles.open(image_path, 'wb') as f:
            content = await reference_image.read()
            await f.write(content)
        
        # 准备参数
        parameters = {
            "count": count,
            "size": size,
            "steps": steps,
            "seed": seed
        }
        
        # 创建任务
        task_id = await task_manager.create_task(
            str(image_path), description, parameters
        )
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="任务已提交，正在处理中"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task_status(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 计算进度
    progress = 0
    if task["status"] == "pending":
        progress = 0
    elif task["status"] == "processing":
        progress = 50
    elif task["status"] == "completed":
        progress = 100
    elif task["status"] == "failed":
        progress = 0
    
    # 准备结果
    result = None
    if task["status"] == "completed" and task["result_path"]:
        result = {
            "image_url": f"/api/image/{task_id}",
            "preview_url": f"/api/image/{task_id}"
        }
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=progress,
        result=result,
        error=task.get("error")
    )

@app.get("/api/image/{task_id}")
async def get_generated_image(task_id: str):
    """获取生成的图像"""
    task = task_manager.get_task_status(task_id)
    
    if not task or task["status"] != "completed" or not task["result_path"]:
        raise HTTPException(status_code=404, detail="图像不存在")
    
    image_path = Path(task["result_path"])
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图像文件不存在")
    
    return FileResponse(image_path)

@app.get("/api/history")
async def get_history(limit: int = 50):
    """获取历史记录"""
    tasks = db_manager.get_all_tasks(limit)
    
    history = []
    for task in tasks:
        history.append({
            "task_id": task["id"],
            "created_at": task["created_at"],
            "description": task["description"],
            "status": task["status"],
            "result_url": f"/api/image/{task['id']}" if task["status"] == "completed" else None
        })
    
    return {"tasks": history}

@app.get("/api/health")
async def health_check():
    """健康检查"""
    try:
        # 检查ComfyUI连接
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{COMFYUI_URL}/system_stats") as response:
                comfyui_status = response.status == 200
    except:
        comfyui_status = False
    
    return {
        "status": "healthy" if comfyui_status else "unhealthy",
        "comfyui_connected": comfyui_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)