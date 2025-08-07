#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版本的main.py，包含正确的错误处理
"""

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
import os
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")

# 支持Docker和本地环境的路径配置
# 本地开发环境
if os.getenv("ENVIRONMENT", "local") == "local":
    COMFYUI_OUTPUT_DIR = Path(os.getenv("COMFYUI_OUTPUT_DIR", "D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output/yeepay"))
    COMFYUI_MAIN_OUTPUT_DIR = Path(os.getenv("COMFYUI_MAIN_OUTPUT_DIR", "D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output"))
else:
    # Docker环境
    COMFYUI_OUTPUT_DIR = Path(os.getenv("COMFYUI_OUTPUT_DIR", "/app/comfyui/output/yeepay"))
    COMFYUI_MAIN_OUTPUT_DIR = Path(os.getenv("COMFYUI_MAIN_OUTPUT_DIR", "/app/comfyui/output"))

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
        # 创建一个简化的Flux Kontext工作流，避免原始模板的复杂节点连接问题
        import random
        
        workflow = {
            "6": {
                "inputs": {
                    "text": description,
                    "clip": ["38", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP文本编码器"}
            },
            "8": {
                "inputs": {
                    "samples": ["31", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE解码"}
            },
            "31": {
                "inputs": {
                    "seed": parameters.get("seed", random.randint(1, 2**32 - 1)),
                    "steps": parameters.get("steps", 20),
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "batch_size": parameters.get("count", 1),
                    "model": ["37", 0],
                    "positive": ["35", 0],
                    "negative": ["135", 0],
                    "latent_image": ["124", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "K采样器"}
            },
            "35": {
                "inputs": {
                    "guidance": 2.5,
                    "conditioning": ["177", 0]
                },
                "class_type": "FluxGuidance",
                "_meta": {"title": "Flux引导"}
            },
            "37": {
                "inputs": {
                    "unet_name": "flux1-dev-kontext_fp8_scaled.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "UNET加载器"}
            },
            "38": {
                "inputs": {
                    "clip_name1": "clip_l.safetensors",
                    "clip_name2": "t5xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "flux",
                    "device": "default"
                },
                "class_type": "DualCLIPLoader",
                "_meta": {"title": "双CLIP加载器"}
            },
            "39": {
                "inputs": {
                    "vae_name": "ae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "VAE加载器"}
            },
            "42": {
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1,
                    "color": 0
                },
                "class_type": "EmptyImage",
                "_meta": {"title": "空图像"}
            },
            "124": {
                "inputs": {
                    "pixels": ["42", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEEncode",
                "_meta": {"title": "VAE编码"}
            },
            "135": {
                "inputs": {
                    "conditioning": ["6", 0]
                },
                "class_type": "ConditioningZeroOut",
                "_meta": {"title": "条件零化"}
            },
            "136": {
                "inputs": {
                    "filename_prefix": "yeepay/yeepay",
                    "images": ["8", 0],
                    "save_all": True
                },
                "class_type": "SaveImage",
                "_meta": {"title": "保存图像"}
            },
            "177": {
                "inputs": {
                    "conditioning": ["6", 0],
                    "latent": ["124", 0]
                },
                "class_type": "ReferenceLatent",
                "_meta": {"title": "ReferenceLatent"}
            }
        }
        
        print(f"✅ 创建简化工作流，包含 {len(workflow)} 个节点")
        
        # 检查是否有参考图
        has_reference_image = reference_image_path and reference_image_path.strip() and not reference_image_path.endswith('blank.png')
        
        if has_reference_image:
            print("检测到参考图，使用参考图模式")
            # 更新参考图像路径 - 将上传的图像复制到ComfyUI输出目录并使用[output]后缀
            container_path = Path(reference_image_path)
            # 统一路径分隔符，确保能正确匹配
            normalized_path = str(container_path).replace('\\', '/')
            if normalized_path.startswith('uploads/'):
                # 将上传的图像复制到ComfyUI输出目录
                import shutil
                source_file = Path(reference_image_path)
                dest_file = COMFYUI_MAIN_OUTPUT_DIR / source_file.name
                
                try:
                    shutil.copy2(source_file, dest_file)
                    print(f"✅ 文件复制成功: {source_file} -> {dest_file}")
                except Exception as e:
                    print(f"❌ 文件复制失败: {e}")
                    raise Exception(f"无法复制参考图像到ComfyUI输出目录: {e}")
                
                # 使用文件名加上[output]后缀
                image_filename = f"{source_file.name} [output]"
                print(f"设置LoadImageOutput图像路径: {image_filename}")
                
                # 添加LoadImageOutput节点
                workflow["142"] = {
                    "inputs": {
                        "image": image_filename,
                        "refresh": "refresh"
                    },
                    "class_type": "LoadImageOutput",
                    "_meta": {"title": "加载图像（来自输出）"}
                }
                
                # 添加FluxKontextImageScale节点
                workflow["42"] = {
                    "inputs": {
                        "width": 512,
                        "height": 512,
                        "image": ["142", 0]
                    },
                    "class_type": "FluxKontextImageScale",
                    "_meta": {"title": "FluxKontextImageScale"}
                }
                
                # 更新VAEEncode节点使用FluxKontextImageScale的输出
                workflow["124"]["inputs"]["pixels"] = ["42", 0]
                
                print(f"✅ 配置参考图模式工作流")
            else:
                print(f"使用原始路径: {reference_image_path}")
        else:
            print("未检测到参考图，使用无参考图模式")
            print(f"✅ 配置无参考图模式工作流")
        
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
                
                if has_reference_image:
                    # 有参考图模式：设置FluxKontextImageScale节点的尺寸参数
                    if "42" in workflow and "inputs" in workflow["42"]:
                        workflow["42"]["inputs"]["width"] = width
                        workflow["42"]["inputs"]["height"] = height
                        print(f"设置FluxKontextImageScale尺寸为: {width}x{height}")
                else:
                    # 无参考图模式：更新EmptyImage节点的尺寸
                    if "42" in workflow and "inputs" in workflow["42"]:
                        workflow["42"]["inputs"]["width"] = width
                        workflow["42"]["inputs"]["height"] = height
                        print(f"更新EmptyImage节点尺寸为: {width}x{height}")
                
            except ValueError:
                print(f"无法解析图像尺寸: {parameters['size']}，使用默认尺寸")
                # 使用默认尺寸
                if has_reference_image and "42" in workflow and "inputs" in workflow["42"]:
                    workflow["42"]["inputs"]["width"] = 512
                    workflow["42"]["inputs"]["height"] = 512
                elif not has_reference_image and "42" in workflow and "inputs" in workflow["42"]:
                    workflow["42"]["inputs"]["width"] = 512
                    workflow["42"]["inputs"]["height"] = 512
        else:
            # 使用默认尺寸
            if has_reference_image and "42" in workflow and "inputs" in workflow["42"]:
                workflow["42"]["inputs"]["width"] = 512
                workflow["42"]["inputs"]["height"] = 512
            elif not has_reference_image and "42" in workflow and "inputs" in workflow["42"]:
                workflow["42"]["inputs"]["width"] = 512
                workflow["42"]["inputs"]["height"] = 512
        
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
        
        # 设置SaveImage节点的文件名前缀为yeepay，用于区分项目
        if "136" in workflow and "inputs" in workflow["136"]:
            workflow["136"]["inputs"]["filename_prefix"] = "yeepay/yeepay"
            print(f"设置SaveImage文件名前缀为: yeepay/yeepay")
        
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
                updated_at TIMESTAMP,
                is_favorited INTEGER DEFAULT 0
            )
        """)
        
        # 检查是否需要添加字段（兼容旧数据库）
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'progress' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0")
        if 'is_favorited' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN is_favorited INTEGER DEFAULT 0")
        
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
            print(f"🚀 开始执行任务: {task_id}")
            print(f"   描述: {description}")
            print(f"   参数: {parameters}")
            print(f"   参考图像: {reference_image_path}")
            
            # 更新状态为处理中
            self.db.update_task_status(task_id, "processing")
            
            # 获取生成数量
            count = int(parameters.get("count", 1))
            result_paths = []
            
            print(f"🎯 开始生成 {count} 张图片...")
            
            # 循环生成每张图片
            for i in range(count):
                print(f"📸 正在生成第 {i+1}/{count} 张图片...")
                
                try:
                    # 为每次生成创建独立的参数副本
                    current_params = parameters.copy()
                    current_params["count"] = 1  # 每次只生成一张
                    
                    # 如果没有指定种子，为每张图片生成不同的随机种子
                    if not parameters.get("seed"):
                        import random
                        current_params["seed"] = random.randint(1, 2**32 - 1)
                        print(f"🎲 使用随机种子: {current_params['seed']}")
                    
                    # 准备工作流
                    print(f"🔧 准备工作流...")
                    workflow = self.workflow_template.customize_workflow(
                        reference_image_path, description, current_params
                    )
                    print(f"✅ 工作流准备完成")
                    
                    # 提交到ComfyUI
                    print(f"📤 提交工作流到ComfyUI...")
                    prompt_id = await self.comfyui.submit_workflow(workflow)
                    print(f"✅ 已提交工作流，prompt_id: {prompt_id}")
                    
                    # 等待完成
                    print(f"⏳ 等待任务完成...")
                    batch_result = await self.wait_for_completion(task_id, prompt_id)
                    
                    if batch_result:
                        result_paths.extend(batch_result)
                        print(f"✅ 第 {i+1} 张图片生成完成: {batch_result}")
                    else:
                        print(f"❌ 第 {i+1} 张图片生成失败")
                        raise Exception(f"第 {i+1} 张图片生成失败，没有返回结果")
                        
                except Exception as e:
                    print(f"❌ 生成第 {i+1} 张图片时出错: {str(e)}")
                    raise Exception(f"生成第 {i+1} 张图片失败: {str(e)}")
                
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
                error_msg = "No output generated"
                print(f"❌ {error_msg}")
                self.db.update_task_status(task_id, "failed", error=error_msg)
                
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print(f"详细错误信息:")
            print(traceback.format_exc())
            self.db.update_task_status(task_id, "failed", error=error_msg)
    
    async def wait_for_completion(self, task_id: str, prompt_id: str, max_wait_time: int = 300) -> Optional[list]:
        """等待任务完成"""
        start_time = datetime.now()
        print(f"⏰ 开始等待任务完成，最大等待时间: {max_wait_time}秒")
        
        while (datetime.now() - start_time).seconds < max_wait_time:
            try:
                print(f"🔍 检查任务状态: {prompt_id}")
                history = await self.comfyui.get_task_status(prompt_id)
                
                if prompt_id in history:
                    task_info = history[prompt_id]
                    print(f"✅ 找到任务信息")
                    
                    if "outputs" in task_info:
                        print(f"🎉 任务完成，开始处理输出")
                        # 任务完成，查找输出图像
                        outputs = task_info["outputs"]
                        result_paths = []
                        import shutil
                        comfyui_output_dir = COMFYUI_MAIN_OUTPUT_DIR
                        
                        print(f"📁 ComfyUI输出目录: {comfyui_output_dir}")
                        print(f"📁 本地输出目录: {OUTPUT_DIR}")
                        
                        # 首先尝试从节点输出获取图片
                        for node_id, output in outputs.items():
                            if "images" in output:
                                print(f"🖼️ 找到图像输出节点 {node_id}，包含 {len(output['images'])} 张图片")
                                for image_info in output["images"]:
                                    filename = image_info['filename']
                                    # 检查图片是否在yeepay子目录中
                                    source_path = comfyui_output_dir / "yeepay" / filename
                                    if not source_path.exists():
                                        # 如果不在yeepay子目录，尝试直接在输出目录中查找
                                        source_path = comfyui_output_dir / filename
                                    
                                    dest_path = OUTPUT_DIR / filename
                                    
                                    print(f"📄 处理图片: {filename}")
                                    print(f"   源路径: {source_path}")
                                    print(f"   目标路径: {dest_path}")
                                    
                                    if source_path.exists():
                                        shutil.copy2(source_path, dest_path)
                                        result_paths.append(f"outputs/{filename}")
                                        print(f"✅ 复制图片成功: {filename}")
                                    else:
                                        print(f"❌ 源文件不存在: {source_path}")
                        
                        print(f"📊 总共处理了 {len(result_paths)} 张图片: {result_paths}")
                        if result_paths:
                            return result_paths
                        else:
                            print(f"❌ 没有找到任何输出图片")
                            return None
                    else:
                        print(f"⏳ 任务还在处理中，等待...")
                
                # 检查是否还在队列中
                queue_status = await self.comfyui.get_queue_status()
                queue_running = queue_status.get("queue_running", [])
                queue_pending = queue_status.get("queue_pending", [])
                
                # 检查任务是否还在队列中
                in_queue = any(item[1] == prompt_id for item in queue_running + queue_pending)
                if not in_queue and prompt_id not in history:
                    # 任务不在队列中也不在历史中，可能失败了
                    print(f"❌ 任务不在队列中也不在历史中，可能失败了")
                    break
                
                await asyncio.sleep(2)  # 等待2秒后再检查
                
            except Exception as e:
                print(f"❌ 检查任务状态时出错: {e}")
                await asyncio.sleep(5)
        
        print(f"⏰ 等待超时，任务可能失败")
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

# 添加uploads路由
@app.get("/api/uploads/{file_path:path}")
async def get_upload_file(file_path: str):
    """获取上传的文件"""
    try:
        file_path_obj = Path(file_path)
        # 确保路径在uploads目录内，防止路径遍历攻击
        if ".." in str(file_path_obj) or file_path_obj.is_absolute():
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        full_path = UPLOAD_DIR / file_path_obj
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(str(full_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

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
    """获取生成的图像"""
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

@app.get("/api/history")
async def get_history(limit: int = 20, offset: int = 0, order: str = "desc", favorite_filter: str = None, time_filter: str = None):
    """获取历史记录"""
    try:
        # 构建查询条件
        query_conditions = []
        query_params = []
        
        # 处理收藏筛选
        if favorite_filter and favorite_filter != "all":
            if favorite_filter == "favorite":
                query_conditions.append("is_favorited = ?")
                query_params.append(1)
            elif favorite_filter == "not_favorite":
                query_conditions.append("is_favorited = ?")
                query_params.append(0)
        
        # 处理时间筛选
        if time_filter and time_filter != "all":
            from datetime import timedelta
            now = datetime.now()
            if time_filter == "today":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_filter == "week":
                start_time = now - timedelta(days=7)
            elif time_filter == "month":
                start_time = now - timedelta(days=30)
            else:
                start_time = None
            
            if start_time:
                query_conditions.append("created_at >= ?")
                query_params.append(start_time.isoformat())
        
        # 构建WHERE子句
        where_clause = ""
        if query_conditions:
            where_clause = "WHERE " + " AND ".join(query_conditions)
        
        # 获取总数
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        count_query = f"SELECT COUNT(*) FROM tasks {where_clause}"
        cursor.execute(count_query, query_params)
        total_count = cursor.fetchone()[0]
        
        # 获取分页数据
        order_clause = "ORDER BY created_at DESC" if order == "desc" else "ORDER BY created_at ASC"
        limit_clause = f"LIMIT {limit} OFFSET {offset}"
        
        query = f"""
            SELECT id, status, description, reference_image_path, parameters, 
                   prompt_id, result_path, error, progress, created_at, updated_at, is_favorited
            FROM tasks 
            {where_clause}
            {order_clause}
            {limit_clause}
        """
        
        cursor.execute(query, query_params)
        rows = cursor.fetchall()
        conn.close()
        
        # 处理结果
        tasks = []
        for row in rows:
            columns = ['id', 'status', 'description', 'reference_image_path', 'parameters', 
                      'prompt_id', 'result_path', 'error', 'progress', 'created_at', 'updated_at', 'is_favorited']
            task = dict(zip(columns, row))
            
            # 解析参数
            try:
                task['parameters'] = json.loads(task['parameters']) if task['parameters'] else {}
            except:
                task['parameters'] = {}
            
            # 处理结果路径
            if task['result_path']:
                try:
                    result_paths = json.loads(task['result_path'])
                    if isinstance(result_paths, list):
                        task['image_count'] = len(result_paths)
                        task['image_urls'] = [f"/api/image/{task['id']}?index={i}" for i in range(len(result_paths))]
                    else:
                        task['image_count'] = 1
                        task['image_urls'] = [f"/api/image/{task['id']}"]
                except:
                    task['image_count'] = 1
                    task['image_urls'] = [f"/api/image/{task['id']}"]
            else:
                task['image_count'] = 0
                task['image_urls'] = []
            
            # 添加task_id字段以兼容前端
            task['task_id'] = task['id']
            
            tasks.append(task)
        
        # 计算是否有更多数据
        has_more = (offset + limit) < total_count
        
        return {
            "tasks": tasks,
            "total": total_count,
            "has_more": has_more,
            "limit": limit,
            "offset": offset,
            "order": order
        }
        
    except Exception as e:
        print(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")

@app.post("/api/task/{task_id}/favorite")
async def toggle_favorite(task_id: str):
    """切换任务收藏状态"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取当前收藏状态
        cursor.execute("SELECT is_favorited FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        current_favorite = result[0]
        new_favorite = 0 if current_favorite else 1
        
        # 更新收藏状态
        cursor.execute("UPDATE tasks SET is_favorited = ?, updated_at = ? WHERE id = ?", 
                      (new_favorite, datetime.now(), task_id))
        conn.commit()
        conn.close()
        
        return {
            "task_id": task_id,
            "is_favorited": bool(new_favorite),
            "message": "收藏状态已更新"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"切换收藏状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换收藏状态失败: {str(e)}")

@app.delete("/api/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查任务是否存在
        cursor.execute("SELECT result_path FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        result_path = result[0]
        
        # 删除相关的图像文件
        if result_path:
            try:
                result_paths = json.loads(result_path)
                if isinstance(result_paths, list):
                    for path in result_paths:
                        file_path = Path(path)
                        if file_path.exists():
                            file_path.unlink()
                            print(f"删除文件: {file_path}")
                else:
                    file_path = Path(result_path)
                    if file_path.exists():
                        file_path.unlink()
                        print(f"删除文件: {file_path}")
            except Exception as file_error:
                print(f"删除文件失败: {file_error}")
        
        # 删除数据库记录
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        
        return {
            "task_id": task_id,
            "message": "任务已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

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
