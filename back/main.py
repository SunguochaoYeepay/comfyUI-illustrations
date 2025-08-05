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
    result: Optional[Dict[str, Any]] = None
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
        
        # 获取文件名并确保是支持的格式
        source_path = Path(reference_image_path)
        image_filename = source_path.name
        
        # 如果不是webp格式，转换文件扩展名为webp（ComfyUI工作流期望webp格式）
        if not image_filename.lower().endswith('.webp'):
            name_without_ext = source_path.stem
            image_filename = f"{name_without_ext}.webp"
        
        # ComfyUI输出目录路径
        comfyui_output_dir = Path("D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output")
        
        if comfyui_output_dir.exists():
            # 复制图像到ComfyUI输出目录
            dest_path = comfyui_output_dir / image_filename
            try:
                shutil.copy2(reference_image_path, dest_path)
                # 更新工作流中的图像文件名（LoadImageOutput格式）
                workflow["142"]["inputs"]["image"] = f"{image_filename} [output]"
                print(f"已复制参考图像到ComfyUI输出目录: {dest_path}")
            except Exception as e:
                print(f"复制图像文件失败: {e}")
                # 如果复制失败，尝试使用绝对路径
                workflow["142"]["inputs"]["image"] = str(reference_image_path)
        else:
            print(f"ComfyUI输出目录不存在: {comfyui_output_dir}")
            # 如果找不到ComfyUI输出目录，使用绝对路径
            workflow["142"]["inputs"]["image"] = str(reference_image_path)
        
        # 更新生成参数
        if parameters.get("steps"):
            workflow["31"]["inputs"]["steps"] = parameters["steps"]
        
        # 更新CFG参数（如果提供）
        if parameters.get("cfg"):
            workflow["31"]["inputs"]["cfg"] = parameters["cfg"]
        
        # 更新Guidance参数（如果提供）
        if parameters.get("guidance"):
            workflow["35"]["inputs"]["guidance"] = parameters["guidance"]
        
        # 处理图像尺寸
        if parameters.get("size"):
            # 解析尺寸字符串 (例如: "512x512")
            try:
                width, height = map(int, parameters["size"].split('x'))
                # 注意：当前工作流模板可能需要根据具体的ComfyUI节点来调整尺寸设置
                # 这里先记录参数，实际的尺寸调整可能需要修改工作流模板
                print(f"图像尺寸设置为: {width}x{height}")
            except ValueError:
                print(f"无法解析图像尺寸: {parameters['size']}，使用默认尺寸")
        
        # 处理生成数量
        count = parameters.get("count", 1)
        print(f"生成数量: {count}")
        # 设置KSampler的batch_size参数
        if count > 1:
            workflow["31"]["inputs"]["batch_size"] = count
            print(f"设置batch_size为: {count}")
        else:
            # 确保单张图片时batch_size为1
            workflow["31"]["inputs"]["batch_size"] = 1
        
        # 处理种子参数
        if parameters.get("seed"):
            workflow["31"]["inputs"]["seed"] = parameters["seed"]
            print(f"使用指定种子: {parameters['seed']}")
        else:
            # 生成随机种子
            import random
            seed = random.randint(1, 2**32 - 1)
            workflow["31"]["inputs"]["seed"] = seed
            print(f"使用随机种子: {seed}")
        
        print(f"工作流参数更新完成: 描述='{description[:50]}...', 步数={workflow['31']['inputs']['steps']}, CFG={workflow['31']['inputs']['cfg']}, 引导={workflow['35']['inputs']['guidance']}")
        
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
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 首先获取任务信息，以便删除相关文件
        cursor.execute("SELECT result_path FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            # 删除结果文件
            result_path = Path(row[0])
            if result_path.exists():
                try:
                    result_path.unlink()
                except Exception as e:
                    print(f"删除文件失败: {e}")
        
        # 删除数据库记录
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def clear_all_tasks(self) -> int:
        """清空所有任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有任务的结果文件路径
        cursor.execute("SELECT result_path FROM tasks WHERE result_path IS NOT NULL")
        rows = cursor.fetchall()
        
        # 删除所有结果文件
        deleted_files = 0
        for row in rows:
            if row[0]:
                result_path = Path(row[0])
                if result_path.exists():
                    try:
                        result_path.unlink()
                        deleted_files += 1
                    except Exception as e:
                        print(f"删除文件失败: {e}")
        
        # 清空数据库
        cursor.execute("DELETE FROM tasks")
        deleted_tasks = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_tasks

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
            
            # 获取生成数量
            count = int(parameters.get("count", 1))
            result_paths = []
            
            # 准备工作流（使用batch_size一次生成多张图）
            workflow = self.workflow_template.customize_workflow(
                reference_image_path, description, parameters
            )
            
            # 提交到ComfyUI
            prompt_id = await self.comfyui.submit_workflow(workflow)
            self.db.update_task_status(task_id, "processing", prompt_id=prompt_id)
            
            # 等待完成
            result_paths = await self.wait_for_completion(task_id, prompt_id)
            
            # 处理结果
            if result_paths:
                print(f"🔍 调试信息: count={count}, result_paths数量={len(result_paths)}, paths={result_paths}")
                if count == 1:
                    # 单张图片，直接存储路径
                    print(f"💾 保存单张图片: {result_paths[0]}")
                    self.db.update_task_status(task_id, "completed", result_path=result_paths[0])
                else:
                    # 多张图片，将路径合并为JSON字符串存储
                    import json
                    result_data = json.dumps(result_paths)
                    print(f"💾 保存多张图片JSON: {result_data}")
                    self.db.update_task_status(task_id, "completed", result_path=result_data)
            else:
                self.db.update_task_status(task_id, "failed", error="No output generated")
                
        except Exception as e:
            self.db.update_task_status(task_id, "failed", error=str(e))
    
    async def wait_for_completion(self, task_id: str, prompt_id: str, max_wait_time: int = 300) -> Optional[list]:
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
                        result_paths = []
                        import shutil
                        comfyui_output_dir = Path("D:\\AI-Image\\ComfyUI-aki-v1.6\\ComfyUI\\output")
                        
                        # 首先尝试从节点输出获取图片
                        for node_id, output in outputs.items():
                            if "images" in output:
                                print(f"🖼️ 找到图像输出节点 {node_id}，包含 {len(output['images'])} 张图片")
                                for image_info in output["images"]:
                                    filename = image_info['filename']
                                    source_path = comfyui_output_dir / filename
                                    dest_path = OUTPUT_DIR / filename
                                    
                                    if source_path.exists():
                                        shutil.copy2(source_path, dest_path)
                                        result_paths.append(f"outputs/{filename}")
                                        print(f"✅ 复制图片: {filename}")
                                    else:
                                        print(f"❌ 源文件不存在: {source_path}")
                        
                        # 如果从节点输出获取的图片数量不足，尝试查找最新的文件
                        expected_count = 4  # 期望的图片数量
                        if len(result_paths) < expected_count:
                            print(f"⚠️ 节点输出图片数量不足({len(result_paths)}/{expected_count})，尝试查找最新文件")
                            try:
                                # 查找所有ComfyUI开头的png文件
                                pattern = "ComfyUI*.png"
                                matching_files = list(comfyui_output_dir.glob(pattern))
                                
                                if matching_files:
                                    # 按修改时间排序，获取最新的文件
                                    matching_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                                    
                                    # 复制最新的文件，补足数量
                                    files_to_copy = matching_files[:expected_count]
                                    result_paths = []  # 重新开始，使用最新文件
                                    
                                    for latest_file in files_to_copy:
                                        dest_path = OUTPUT_DIR / latest_file.name
                                        shutil.copy2(latest_file, dest_path)
                                        result_paths.append(f"outputs/{latest_file.name}")
                                        print(f"✅ 复制最新文件: {latest_file.name}")
                            except Exception as e:
                                print(f"❌ 查找最新文件失败: {e}")
                        
                        print(f"📊 总共处理了 {len(result_paths)} 张图片: {result_paths}")
                        return result_paths if result_paths else None
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
workflow_template = WorkflowTemplate("./flux_kontext_dev_basic.json")
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
        
        print(f"🔍 接收到生成请求: description='{description[:50]}...', count={count}, size={size}, steps={steps}")
        print(f"📊 参数详情: {parameters}")
        
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
        try:
            # 尝试解析JSON格式的多个结果路径
            import json
            result_paths = json.loads(task["result_path"])
            if isinstance(result_paths, list):
                # 多个图像
                result = {
                    "image_urls": [f"/api/image/{task_id}?index={i}" for i in range(len(result_paths))],
                    "count": len(result_paths)
                }
            else:
                # 单个图像（向后兼容）
                result = {
                    "image_urls": [f"/api/image/{task_id}"],
                    "count": 1
                }
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON格式，按单个图像处理（向后兼容）
            result = {
                "image_urls": [f"/api/image/{task_id}"],
                "count": 1
            }
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=progress,
        result=result,
        error=task.get("error")
    )

@app.get("/api/image/{task_id}")
async def get_generated_image(task_id: str, index: int = 0):
    """获取生成的图像"""
    task = task_manager.get_task_status(task_id)
    
    if not task or task["status"] != "completed" or not task["result_path"]:
        raise HTTPException(status_code=404, detail="图像不存在")
    
    try:
        # 尝试解析JSON格式的多个结果路径
        import json
        result_paths = json.loads(task["result_path"])
        if isinstance(result_paths, list):
            # 多个图像
            if index >= len(result_paths) or index < 0:
                raise HTTPException(status_code=404, detail="图像索引不存在")
            image_path = Path(result_paths[index])
        else:
            # 单个图像（向后兼容）
            if index != 0:
                raise HTTPException(status_code=404, detail="图像索引不存在")
            image_path = Path(result_paths)
    except (json.JSONDecodeError, TypeError):
        # 如果不是JSON格式，按单个图像处理（向后兼容）
        if index != 0:
            raise HTTPException(status_code=404, detail="图像索引不存在")
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

@app.delete("/api/history/{task_id}")
async def delete_history_item(task_id: str):
    """删除单个历史记录"""
    try:
        deleted = db_manager.delete_task(task_id)
        if deleted:
            return {"message": "历史记录已删除", "task_id": task_id}
        else:
            raise HTTPException(status_code=404, detail="任务不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@app.delete("/api/history")
async def clear_all_history():
    """清空所有历史记录"""
    try:
        deleted_count = db_manager.clear_all_tasks()
        return {"message": f"已清空 {deleted_count} 条历史记录"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")

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