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
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "progress": 100,
                "result": {
                    "image_urls": ["/api/image/123e4567-e89b-12d3-a456-426614174000?index=0"],
                    "count": 1,
                    "filenames": ["ComfyUI_00001_.png"],
                    "direct_urls": ["/api/image/123e4567-e89b-12d3-a456-426614174000?filename=ComfyUI_00001_.png"]
                },
                "error": None
            }
        }

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
            # 确保SaveImage节点的save_all参数为true
            if "136" in workflow and "inputs" in workflow["136"]:
                workflow["136"]["inputs"]["save_all"] = True
                print(f"设置SaveImage节点的save_all参数为true，确保保存所有批次图片")
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
                progress INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # 检查是否需要添加progress字段（兼容旧数据库）
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'progress' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0")
        
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
    
    def update_task_progress(self, task_id: str, progress: int) -> None:
        """更新任务进度"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET progress = ?, updated_at = ?
            WHERE id = ?
        """, (progress, datetime.now(), task_id))
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
    
    def get_all_tasks(self, limit: int = 50, offset: int = 0, order: str = "desc") -> dict:
        """获取所有任务（支持分页和排序）
        
        Args:
            limit: 每页数量
            offset: 偏移量
            order: 排序方式，'desc'为倒序（最新在前），'asc'为正序（最旧在前）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取总数
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]
        
        # 根据order参数确定排序方式
        order_clause = "DESC" if order.lower() == "desc" else "ASC"
        
        # 获取分页数据
        cursor.execute(f"""
            SELECT * FROM tasks 
            ORDER BY created_at {order_clause} 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        tasks = [dict(zip(columns, row)) for row in rows]
        
        return {
            "tasks": tasks,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
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
            
            print(f"🎯 开始生成 {count} 张图片...")
            
            # 循环生成每张图片
            for i in range(count):
                print(f"📸 正在生成第 {i+1}/{count} 张图片...")
                
                # 为每次生成创建独立的参数副本
                current_params = parameters.copy()
                current_params["count"] = 1  # 每次只生成一张
                
                # 如果没有指定种子，为每张图片生成不同的随机种子
                if not parameters.get("seed"):
                    import random
                    current_params["seed"] = random.randint(1, 2**32 - 1)
                    print(f"🎲 使用随机种子: {current_params['seed']}")
                
                # 准备工作流
                workflow = self.workflow_template.customize_workflow(
                    reference_image_path, description, current_params
                )
                
                # 提交到ComfyUI
                prompt_id = await self.comfyui.submit_workflow(workflow)
                print(f"📤 已提交工作流，prompt_id: {prompt_id}")
                
                # 等待完成
                batch_result = await self.wait_for_completion(task_id, prompt_id)
                
                if batch_result:
                    result_paths.extend(batch_result)
                    print(f"✅ 第 {i+1} 张图片生成完成: {batch_result}")
                else:
                    print(f"❌ 第 {i+1} 张图片生成失败")
                
                # 更新进度
                progress = int((i + 1) / count * 100)
                self.db.update_task_progress(task_id, progress)
                
                # 如果不是最后一张，稍微等待一下避免过快请求
                if i < count - 1:
                    await asyncio.sleep(1)
            
            # 处理结果
            if result_paths:
                print(f"🔍 最终结果: count={count}, result_paths数量={len(result_paths)}, paths={result_paths}")
                
                if len(result_paths) == 1:
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
            print(f"❌ 任务执行失败: {str(e)}")
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
                        # 从任务信息中获取期望的图片数量
                        expected_count = 1  # 默认为1
                        try:
                            # 尝试从工作流中获取batch_size参数
                            if "31" in task_info.get("prompt", {}) and "inputs" in task_info["prompt"]["31"]:
                                expected_count = task_info["prompt"]["31"]["inputs"].get("batch_size", 1)
                                print(f"🔢 从工作流中获取期望图片数量: {expected_count}")
                        except Exception as e:
                            print(f"⚠️ 获取期望图片数量失败: {e}")
                            # 保持默认值
                        if len(result_paths) < expected_count:
                            print(f"⚠️ 节点输出图片数量不足({len(result_paths)}/{expected_count})，尝试查找最新文件")
                            try:
                                # 从SaveImage节点的输出中获取文件名模式
                                # ComfyUI的批量生成通常会使用相同的前缀，但添加不同的索引
                                # 例如：ComfyUI_00001_.png, ComfyUI_00002_.png 等
                                
                                # 首先检查是否有已知的文件名作为基础
                                base_filename = None
                                if result_paths and len(result_paths) > 0:
                                    # 从已有的结果中提取基本文件名模式
                                    first_file = Path(result_paths[0].replace("outputs/", ""))
                                    # 提取数字部分前的前缀和后缀
                                    import re
                                    # 尝试多种可能的文件名模式
                                    # 1. ComfyUI_00001_.png 格式
                                    match = re.search(r'(.+?)_(\d+)_(.+)', first_file.name)
                                    # 2. ComfyUI_00001.png 格式
                                    if not match:
                                        match = re.search(r'(.+?)_(\d+)(\.\w+)', first_file.name)
                                    if match:
                                        prefix = match.group(1)  # 例如 "ComfyUI"
                                        # 数字部分
                                        index = int(match.group(2))
                                        suffix = match.group(3)  # 例如 ".png"
                                        print(f"📋 提取的文件名模式: 前缀={prefix}, 索引={index}, 后缀={suffix}")
                                        
                                        # 查找具有相同前缀和后缀但索引不同的文件
                                        potential_files = []
                                        # 确定文件名格式
                                        has_underscore_suffix = '_' in suffix if suffix else False
                                        
                                        for i in range(index, index + expected_count * 2):  # 搜索范围扩大一些
                                            # 构建可能的文件名，保持相同的数字格式（例如 00001）
                                            formatted_index = str(i).zfill(len(str(index)))
                                            
                                            # 尝试多种可能的文件名格式
                                            potential_filenames = []
                                            if has_underscore_suffix:
                                                # ComfyUI_00001_.png 格式
                                                potential_filenames.append(f"{prefix}_{formatted_index}_{suffix}")
                                            else:
                                                # ComfyUI_00001.png 格式
                                                potential_filenames.append(f"{prefix}_{formatted_index}{suffix}")
                                            
                                            # 检查所有可能的文件名
                                            for potential_filename in potential_filenames:
                                                potential_path = comfyui_output_dir / potential_filename
                                                if potential_path.exists():
                                                    potential_files.append(potential_path)
                                                    print(f"🔍 找到潜在的批量文件: {potential_filename}")
                                                    break  # 找到一个就跳出内层循环
                                        
                                        if len(potential_files) >= expected_count:
                                            print(f"✅ 找到足够的批量文件: {len(potential_files)} 张")
                                            matching_files = potential_files[:expected_count]
                                        else:
                                            print(f"⚠️ 未找到足够的批量文件，回退到通配符搜索")
                                            pattern = "ComfyUI*.png"
                                            matching_files = list(comfyui_output_dir.glob(pattern))
                                    else:
                                        print(f"⚠️ 无法从现有文件提取模式: {first_file.name}，回退到通配符搜索")
                                        pattern = "ComfyUI*.png"
                                        matching_files = list(comfyui_output_dir.glob(pattern))
                                else:
                                    print(f"⚠️ 没有现有文件作为参考，回退到通配符搜索")
                                    pattern = "ComfyUI*.png"
                                    matching_files = list(comfyui_output_dir.glob(pattern))
                                
                                if matching_files:
                                    # 按修改时间排序，获取最新的文件
                                    matching_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                                    
                                    # 尝试查找具有相似时间戳的文件组（批量生成的图片通常时间戳接近）
                                    if expected_count > 1 and len(matching_files) >= expected_count:
                                        print(f"🔍 尝试查找批量生成的图片组...")
                                        # 获取最新文件的时间戳
                                        latest_time = matching_files[0].stat().st_mtime
                                        # 查找时间戳接近的文件（5秒内）
                                        batch_files = [f for f in matching_files if abs(f.stat().st_mtime - latest_time) < 5]
                                        
                                        if len(batch_files) >= expected_count:
                                            print(f"✅ 找到可能的批量生成图片组: {len(batch_files)} 张")
                                            files_to_copy = batch_files[:expected_count]
                                        else:
                                            print(f"⚠️ 未找到足够的批量图片，使用最新的 {expected_count} 张")
                                            files_to_copy = matching_files[:expected_count]
                                    else:
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
                # 提取文件名，以便前端可以直接请求特定文件
                filenames = [Path(path).name for path in result_paths]
                result = {
                    "image_urls": [f"/api/image/{task_id}?index={i}" for i in range(len(result_paths))],
                    "count": len(result_paths),
                    "filenames": filenames,  # 添加文件名列表
                    "direct_urls": [f"/api/image/{task_id}?filename={filename}" for filename in filenames]  # 直接访问URL
                }
            else:
                # 单个图像（向后兼容）
                filename = Path(result_paths).name
                result = {
                    "image_urls": [f"/api/image/{task_id}"],
                    "count": 1,
                    "filenames": [filename],
                    "direct_urls": [f"/api/image/{task_id}?filename={filename}"]
                }
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON格式，按单个图像处理（向后兼容）
            try:
                filename = Path(task["result_path"]).name
                result = {
                    "image_urls": [f"/api/image/{task_id}"],
                    "count": 1,
                    "filenames": [filename],
                    "direct_urls": [f"/api/image/{task_id}?filename={filename}"]
                }
            except:
                result = {
                    "image_urls": [f"/api/image/{task_id}"],
                    "count": 1,
                    "filenames": ["unknown.png"],
                    "direct_urls": [f"/api/image/{task_id}"]
                }
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=progress,
        result=result,
        error=task.get("error")
    )

@app.get("/api/image/{task_id}")
async def get_generated_image(task_id: str, index: int = 0, filename: str = None):
    """获取生成的图像
    
    参数:
        task_id: 任务ID
        index: 图像索引（批量生成时使用）
        filename: 可选，指定要获取的文件名
    """
    task = task_manager.get_task_status(task_id)
    
    if not task or task["status"] != "completed" or not task["result_path"]:
        raise HTTPException(status_code=404, detail="图像不存在")
    
    try:
        # 尝试解析JSON格式的多个结果路径
        import json
        result_paths = json.loads(task["result_path"])
        
        # 如果指定了文件名，尝试查找匹配的文件
        if filename:
            if isinstance(result_paths, list):
                # 在结果列表中查找匹配的文件名
                found = False
                for path in result_paths:
                    if Path(path).name == filename or Path(path).name.endswith(f"/{filename}"):
                        image_path = Path(path)
                        found = True
                        break
                if not found:
                    raise HTTPException(status_code=404, detail=f"指定的文件名 {filename} 不存在")
            else:
                # 单个结果，检查是否匹配
                if Path(result_paths).name != filename and not Path(result_paths).name.endswith(f"/{filename}"):
                    raise HTTPException(status_code=404, detail=f"指定的文件名 {filename} 不存在")
                image_path = Path(result_paths)
        else:
            # 使用索引获取图像
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

@app.get("/api/reference-image/{task_id}")
async def get_reference_image(task_id: str):
    """获取任务的参考图像"""
    task = task_manager.get_task_status(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if not task.get("reference_image_path"):
        raise HTTPException(status_code=404, detail="该任务没有参考图像")
    
    reference_path = Path(task["reference_image_path"])
    if not reference_path.exists():
        raise HTTPException(status_code=404, detail="参考图像文件不存在")
    
    return FileResponse(reference_path)

@app.get("/api/history")
async def get_history(limit: int = 20, offset: int = 0, order: str = "desc"):
    """获取历史记录（支持分页和排序）"""
    result = db_manager.get_all_tasks(limit, offset, order)
    tasks = result["tasks"]
    
    history = []
    for task in tasks:
        task_data = {
            "task_id": task["id"],
            "created_at": task["created_at"],
            "description": task["description"],
            "status": task["status"],
            "result_url": None,
            "filenames": None,
            "direct_urls": None,
            "reference_image_url": None
        }
        
        # 添加参考图URL
        if task.get("reference_image_path"):
            reference_path = Path(task["reference_image_path"])
            if reference_path.exists():
                # 构建参考图的访问URL
                task_data["reference_image_url"] = f"/api/reference-image/{task['id']}"
        
        # 如果任务已完成，添加图片信息
        if task["status"] == "completed" and task.get("result_path"):
            try:
                # 尝试解析JSON格式的多个结果路径
                import json
                result_paths = json.loads(task["result_path"])
                
                if isinstance(result_paths, list):
                    # 多个图像
                    filenames = [Path(path).name for path in result_paths]
                    task_data.update({
                        "result_url": f"/api/image/{task['id']}",
                        "filenames": json.dumps(filenames),
                        "direct_urls": json.dumps([f"/api/image/{task['id']}?filename={filename}" for filename in filenames])
                    })
                else:
                    # 单个图像
                    filename = Path(result_paths).name
                    task_data.update({
                        "result_url": f"/api/image/{task['id']}",
                        "filenames": json.dumps([filename]),
                        "direct_urls": json.dumps([f"/api/image/{task['id']}?filename={filename}"])
                    })
            except (json.JSONDecodeError, TypeError):
                # 如果不是JSON格式，按单个图像处理
                try:
                    filename = Path(task["result_path"]).name
                    task_data.update({
                        "result_url": f"/api/image/{task['id']}",
                        "filenames": json.dumps([filename]),
                        "direct_urls": json.dumps([f"/api/image/{task['id']}?filename={filename}"])
                    })
                except:
                    task_data["result_url"] = f"/api/image/{task['id']}"
        
        history.append(task_data)
    
    return {
        "tasks": history,
        "total": result["total"],
        "limit": result["limit"],
        "offset": result["offset"],
        "has_more": result["has_more"]
    }

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
    from config import config
    uvicorn.run(app, host=config.HOST, port=config.PORT)