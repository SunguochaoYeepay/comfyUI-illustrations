#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YeePay AI图像生成服务 - 后端主程序
支持Flux Kontext模型，提供图像生成、历史管理、收藏等功能
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 导入配置和模型
from config.settings import (
    COMFYUI_URL, UPLOAD_DIR, OUTPUT_DIR, DB_PATH, 
    DEFAULT_COUNT, DEFAULT_IMAGE_SIZE, DEFAULT_STEPS, MIN_FILE_SIZE
)
from models.schemas import (
    TaskResponse, TaskStatusResponse, HistoryResponse, 
    FavoriteResponse, DeleteResponse, HealthResponse
)

# 导入核心业务逻辑
from core.database_manager import DatabaseManager
from core.comfyui_client import ComfyUIClient
from core.workflow_template import WorkflowTemplate
from core.task_manager import TaskManager

# =============================================================================
# 初始化组件
# =============================================================================

# 初始化各个管理器
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
    reference_image: Optional[UploadFile] = File(None),
    count: int = Form(DEFAULT_COUNT),
    size: str = Form(DEFAULT_IMAGE_SIZE),
    steps: int = Form(DEFAULT_STEPS),
    seed: Optional[int] = Form(None)
):
    """生成图像API"""
    try:
        # 处理参考图像
        image_path = None
        if reference_image:
            try:
                # 保存上传的参考图像
                image_filename = f"{uuid.uuid4()}_{reference_image.filename}"
                image_path = UPLOAD_DIR / image_filename
                
                # 读取文件内容
                content = await reference_image.read()
                
                # 验证文件内容
                if len(content) == 0:
                    print("❌ 参考图像文件为空")
                    raise HTTPException(status_code=400, detail="参考图像文件为空")
                
                if len(content) < MIN_FILE_SIZE:  # 图片文件通常至少100字节
                    print(f"❌ 参考图像文件过小: {len(content)} 字节")
                    raise HTTPException(status_code=400, detail="参考图像文件过小或损坏")
                
                # 保存文件
                async with aiofiles.open(image_path, 'wb') as f:
                    await f.write(content)
                
                # 验证保存的文件
                if not image_path.exists() or image_path.stat().st_size == 0:
                    print("❌ 参考图像保存失败")
                    raise HTTPException(status_code=500, detail="参考图像保存失败")
                
                print(f"✅ 保存参考图像成功: {image_path} ({image_path.stat().st_size} 字节)")
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"❌ 保存参考图像时出错: {e}")
                # 如果保存失败，清理可能创建的文件
                if image_path and image_path.exists():
                    try:
                        image_path.unlink()
                    except:
                        pass
                raise HTTPException(status_code=500, detail=f"保存参考图像失败: {str(e)}")
        else:
            print("📸 无参考图像，使用无参考图模式")
        
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
            str(image_path) if image_path else "", description, parameters
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
async def get_history(limit: int = 20, offset: int = 0, order: str = "asc", favorite_filter: str = None, time_filter: str = None):
    """获取历史记录"""
    try:
        result = db_manager.get_tasks_with_filters(
            limit=limit, 
            offset=offset, 
            order=order, 
            favorite_filter=favorite_filter, 
            time_filter=time_filter
        )
        return result
    except Exception as e:
        print(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")

@app.post("/api/task/{task_id}/favorite")
async def toggle_favorite(task_id: str):
    """切换任务收藏状态（向后兼容）"""
    try:
        new_favorite = db_manager.toggle_favorite(task_id)
        if new_favorite is False and not db_manager.get_task(task_id):
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "task_id": task_id,
            "is_favorited": new_favorite,
            "message": "收藏状态已更新"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"切换收藏状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换收藏状态失败: {str(e)}")

@app.post("/api/image/{task_id}/{image_index}/favorite")
async def toggle_image_favorite(task_id: str, image_index: int, filename: str = None):
    """切换单张图片收藏状态"""
    try:
        # 验证任务是否存在
        task = db_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        new_favorite = db_manager.toggle_image_favorite(task_id, image_index, filename)
        
        return {
            "task_id": task_id,
            "image_index": image_index,
            "is_favorited": new_favorite,
            "message": "图片收藏状态已更新"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"切换图片收藏状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换图片收藏状态失败: {str(e)}")



@app.delete("/api/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    try:
        result_path = db_manager.delete_task(task_id)
        if result_path is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        
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
        comfyui_status = await comfyui_client.check_health()
    except:
        comfyui_status = False
    
    from datetime import datetime
    return {
        "status": "healthy" if comfyui_status else "unhealthy",
        "comfyui_connected": comfyui_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
