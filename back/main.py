#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YeePay AI图像生成服务 - 后端主程序
支持Flux Kontext模型，提供图像生成、历史管理、收藏等功能
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Query
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

# 导入统一服务管理器
from core.service_manager import (
    get_db_manager, get_task_manager, get_comfyui_client
)

# 导入放大服务
from api.upscale_routes import router as upscale_router

# 导入翻译服务
from core.translation_client import get_translation_client

# =============================================================================
# 初始化组件
# =============================================================================

# 使用服务管理器获取实例（延迟初始化）
db_manager = get_db_manager()
task_manager = get_task_manager()



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

# 添加uploads路由（必须在upscale路由之前注册）
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

# 添加image/upload路由（兼容前端请求）
@app.get("/api/image/upload/{file_path:path}")
async def get_upload_image(file_path: str):
    """获取上传的图片文件（兼容前端请求）"""
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

# 添加LoRA管理API
@app.get("/api/models")
async def get_available_models():
    """获取可用的基础模型列表"""
    try:
        from core.model_manager import get_available_models
        
        models = get_available_models()
        return {"models": models}
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return {"models": []}


@app.get("/api/loras")
async def get_available_loras(model: str = Query("flux1-dev", description="基础模型名称")):
    """获取可用的LoRA列表（根据模型过滤）"""
    try:
        from pathlib import Path
        from config.settings import COMFYUI_MAIN_OUTPUT_DIR
        from core.model_manager import get_model_config, ModelType

        # 获取模型配置
        model_config = get_model_config(model)
        if not model_config:
            print(f"⚠️ 模型 {model} 不存在，使用默认Flux模型")
            model_config = get_model_config("flux1-dev")

        # LoRA文件通常存放在ComfyUI的models/loras目录
        lora_dir = Path("D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/models/loras")
        
        if not lora_dir.exists():
            print(f"📁 LoRA目录不存在: {lora_dir}")
            return {"loras": [], "message": "LoRA目录不存在"}
        
        # 查找所有.safetensors文件
        lora_files = []
        for file_path in lora_dir.glob("*.safetensors"):
            lora_name = file_path.name
            
            # 根据模型类型过滤LoRA
            is_compatible = True
            if model_config.model_type == ModelType.FLUX:
                # Flux模型：排除Qwen相关的LoRA
                if any(keyword in lora_name.lower() for keyword in ['qwen', '千问', 'qwen2']):
                    is_compatible = False
            elif model_config.model_type == ModelType.QWEN:
                # Qwen模型：优先选择Qwen相关的LoRA，但也兼容通用LoRA
                # 这里可以根据需要调整过滤逻辑
                pass
            
            if is_compatible:
                lora_files.append({
                    "name": lora_name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                    "compatible": True
                })
        
        # 按修改时间排序，最新的在前
        lora_files.sort(key=lambda x: x["modified"], reverse=True)
        
        print(f"🎨 找到 {len(lora_files)} 个兼容的LoRA文件 (模型: {model_config.display_name})")
        return {
            "loras": lora_files,
            "total": len(lora_files),
            "directory": str(lora_dir),
            "model": model,
            "model_type": model_config.model_type.value
        }
        
    except Exception as e:
        print(f"❌ 获取LoRA列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取LoRA列表失败: {str(e)}")


@app.post("/api/loras/upload")
async def upload_lora(file: UploadFile = File(...)):
    """上传LoRA文件"""
    try:
        from pathlib import Path
        from config.settings import COMFYUI_MAIN_OUTPUT_DIR
        
        # 验证文件类型
        if not file.filename.endswith('.safetensors'):
            raise HTTPException(status_code=400, detail="只支持.safetensors格式的LoRA文件")
        
        # 验证文件大小（最大100MB）
        content = await file.read()
        if len(content) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="LoRA文件大小不能超过100MB")
        
        # 保存到LoRA目录
        lora_dir = Path("D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/models/loras")
        lora_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = lora_dir / file.filename
        
        # 检查文件是否已存在
        if file_path.exists():
            raise HTTPException(status_code=400, detail="LoRA文件已存在")
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        print(f"✅ LoRA文件上传成功: {file_path}")
        
        return {
            "message": "LoRA文件上传成功",
            "filename": file.filename,
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ LoRA文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"LoRA文件上传失败: {str(e)}")


@app.delete("/api/loras/{filename}")
async def delete_lora(filename: str):
    """删除LoRA文件"""
    try:
        from pathlib import Path
        from config.settings import COMFYUI_MAIN_OUTPUT_DIR
        
        # 安全检查：确保文件名不包含路径遍历
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="无效的文件名")
        
        lora_dir = Path("D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/models/loras")
        file_path = lora_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="LoRA文件不存在")
        
        # 删除文件
        file_path.unlink()
        
        print(f"✅ LoRA文件删除成功: {file_path}")
        
        return {
            "message": "LoRA文件删除成功",
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ LoRA文件删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"LoRA文件删除失败: {str(e)}")


# 注册放大服务路由
app.include_router(upscale_router)

# 添加放大图片下载路由（临时解决方案）
@app.get("/api/upscale/image/{task_id}/{filename}")
async def get_upscale_image_file(task_id: str, filename: str):
    """获取放大后的图片文件"""
    try:
        from pathlib import Path
        from fastapi.responses import FileResponse
        from config.settings import OUTPUT_DIR
        
        # 构建图片文件路径
        image_path = Path(OUTPUT_DIR) / task_id / filename
        
        print(f"🔍 查找放大图片: {image_path}")
        print(f"📁 文件是否存在: {image_path.exists()}")
        
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        return FileResponse(str(image_path))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")

@app.get("/api/upscale/image/{task_id}/original")
async def get_upscale_original_file(task_id: str):
    """获取原始图片文件"""
    try:
        from pathlib import Path
        from fastapi.responses import FileResponse
        from config.settings import OUTPUT_DIR
        
        # 查找原始图片文件
        task_dir = Path(OUTPUT_DIR) / task_id
        if not task_dir.exists():
            raise HTTPException(status_code=404, detail="任务目录不存在")
        
        # 查找原始图片（通常是输入图片的副本）
        original_files = list(task_dir.glob("upscale_*"))
        if not original_files:
            # 如果没有找到，尝试查找任何非task_前缀的图片
            all_images = list(task_dir.glob("*.png")) + list(task_dir.glob("*.jpg")) + list(task_dir.glob("*.jpeg"))
            original_files = [f for f in all_images if not f.name.startswith("task_")]
        
        if not original_files:
            raise HTTPException(status_code=404, detail="原始图片不存在")
        
        # 返回第一个找到的原始图片
        return FileResponse(str(original_files[0]))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取原始图片失败: {str(e)}")

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
    seed: Optional[int] = Form(None),
    model: str = Form("flux1-dev"),  # 新增模型选择参数
    loras: Optional[str] = Form(None)  # JSON字符串格式的LoRA配置
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
        
        # 处理LoRA配置
        lora_configs = []
        if loras:
            try:
                import json
                lora_data = json.loads(loras)
                if isinstance(lora_data, list):
                    # 验证LoRA配置
                    for lora in lora_data:
                        if isinstance(lora, dict) and "name" in lora:
                            lora_configs.append(lora)
                    print(f"🎨 解析到 {len(lora_configs)} 个LoRA配置")
                else:
                    print("⚠️ LoRA配置格式错误，应为数组格式")
            except json.JSONDecodeError as e:
                print(f"❌ LoRA配置JSON解析失败: {e}")
            except Exception as e:
                print(f"❌ LoRA配置处理失败: {e}")
        
        # 准备参数
        parameters = {
            "count": count,
            "size": size,
            "steps": steps,
            "seed": seed,
            "model": model,  # 添加模型参数
            "loras": lora_configs
        }
        
        print(f"🔍 接收到生成请求: description='{description[:50]}...', count={count}, size={size}, steps={steps}")
        print(f"📊 参数详情: {parameters}")
        if lora_configs:
            print(f"🎨 LoRA配置: {lora_configs}")
        
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

@app.post("/api/translate")
async def translate_text(text: str = Form(...)):
    """翻译文本API"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🌐 收到翻译API请求")
        logger.info(f"   请求文本: {text}")
        logger.info(f"   文本长度: {len(text)}字符")
        
        if not text.strip():
            logger.warning(f"⚠️ 翻译请求被拒绝: 文本为空")
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        # 获取翻译客户端
        logger.info(f"🔧 获取翻译客户端")
        translation_client = get_translation_client()
        
        # 检查Ollama服务是否可用
        logger.info(f"🏥 检查Ollama服务健康状态")
        if not await translation_client.check_ollama_health():
            logger.error(f"❌ Ollama服务不可用")
            raise HTTPException(status_code=503, detail="Ollama服务不可用")
        
        # 检查qwen2.5:7b模型是否可用
        logger.info(f"🔍 检查模型可用性")
        if not await translation_client.check_model_available():
            logger.error(f"❌ qwen2.5:7b模型不可用")
            raise HTTPException(status_code=503, detail="qwen2.5:7b模型不可用")
        
        # 执行翻译
        logger.info(f"🔄 开始执行翻译")
        translated_text = await translation_client.translate_to_english(text)
        
        if translated_text:
            logger.info(f"✅ 翻译API成功")
            logger.info(f"   原文: {text}")
            logger.info(f"   译文: {translated_text}")
            logger.info(f"   翻译比例: {len(translated_text)}/{len(text)}字符")
            
            return {
                "original": text,
                "translated": translated_text,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"❌ 翻译失败: 返回空结果")
            raise HTTPException(status_code=500, detail="翻译失败")
            
    except HTTPException:
        logger.error(f"❌ 翻译API HTTP异常")
        raise
    except Exception as e:
        logger.error(f"❌ 翻译API异常: {str(e)}")
        logger.error(f"   异常类型: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"翻译服务出错: {str(e)}")

@app.get("/api/translate/health")
async def translate_health_check():
    """翻译服务健康检查"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🏥 收到翻译服务健康检查请求")
        
        translation_client = get_translation_client()
        
        logger.info(f"🔍 检查Ollama服务状态")
        ollama_health = await translation_client.check_ollama_health()
        
        model_available = False
        if ollama_health:
            logger.info(f"🔍 检查模型可用性")
            model_available = await translation_client.check_model_available()
        
        service_ready = ollama_health and model_available
        
        logger.info(f"📊 健康检查结果:")
        logger.info(f"   Ollama服务: {'✅ 正常' if ollama_health else '❌ 异常'}")
        logger.info(f"   模型可用: {'✅ 正常' if model_available else '❌ 异常'}")
        logger.info(f"   服务就绪: {'✅ 是' if service_ready else '❌ 否'}")
        
        return {
            "ollama_available": ollama_health,
            "qwen_model_available": model_available,
            "translation_service_ready": service_ready,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ 健康检查异常: {str(e)}")
        return {
            "ollama_available": False,
            "qwen_model_available": False,
            "translation_service_ready": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        db_manager.get_task("test")  # 简单查询测试
        db_healthy = True
    except:
        db_healthy = False
    
    try:
        comfyui_client = get_comfyui_client()
        comfyui_status = await comfyui_client.check_health()
    except:
        comfyui_status = False
    
    from datetime import datetime
    overall_healthy = db_healthy and comfyui_status
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "database_connected": db_healthy,
        "comfyui_connected": comfyui_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
