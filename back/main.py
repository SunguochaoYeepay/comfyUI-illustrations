#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YeePay AI图像生成服务 - 后端主程序
支持Flux Kontext模型，提供图像生成、历史管理、收藏等功能
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

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
    FavoriteResponse, DeleteResponse, HealthResponse, GenerateFusionRequest
)

# 导入统一服务管理器
from core.service_manager import (
    get_db_manager, get_task_manager, get_comfyui_client
)

# 导入缓存管理器
from core.cache_manager import get_cache_manager

# 导入缩略图管理器
from core.thumbnail_manager import get_thumbnail_manager

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
cache_manager = get_cache_manager()
thumbnail_manager = get_thumbnail_manager()



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
        from core.model_manager import get_available_models_async, get_available_models
        
        # 优先使用配置客户端获取模型
        try:
            models = await get_available_models_async()
            return {
                "models": models,
                "config_source": "backend",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as config_error:
            print(f"⚠️ 配置客户端获取模型失败，使用降级方法: {config_error}")
            # 降级到本地配置
            models = get_available_models()
            return {
                "models": models,
                "config_source": "local",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return {
            "models": [],
            "config_source": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/loras")
async def get_available_loras(model: str = Query(..., description="基础模型名称")):
    """获取可用的LoRA列表（根据模型过滤）"""
    try:
        from core.lora_manager import get_loras_from_config
        
        # 优先使用配置客户端获取LoRA
        try:
            loras = await get_loras_from_config(model)
            return {
                "loras": loras,
                "config_source": "backend",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as config_error:
            import traceback
            print(f"⚠️ 配置客户端获取LoRA失败，使用降级方法: {config_error}")
            print(f"详细错误信息: {traceback.format_exc()}")
            # 降级到空列表
            return {
                "loras": [],
                "config_source": "error",
                "error": str(config_error),
                "timestamp": datetime.now().isoformat()
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
        
        # 使用统一配置的LoRA目录
        from config.settings import COMFYUI_LORAS_DIR
        lora_dir = COMFYUI_LORAS_DIR
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
        
        lora_dir = Path("E:/AI-Image/ComfyUI-aki-v1.4/models/loras")
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

# 放大图片路由已在 upscale_routes.py 中定义，这里删除重复的路由

# 添加前端页面路由
@app.get("/frontend.html")
async def get_frontend():
    """返回前端页面"""
    return FileResponse("frontend.html")

@app.get("/")
async def root():
    """根路径重定向到前端页面"""
    return FileResponse("frontend.html")

@app.post("/api/generate-video", response_model=TaskResponse)
async def generate_video(
    description: str = Form(...),
    reference_image: UploadFile = File(...),  # 视频生成必须要有参考图
    fps: int = Form(16),
    duration: int = Form(5),  # 秒
    model: str = Form("wan2.2-video"),
    loras: Optional[str] = Form(None)  # JSON字符串格式的LoRA配置
):
    """生成视频API"""
    try:
        # 处理参考图像
        image_path = None
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
            
            if len(content) < MIN_FILE_SIZE:
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
            if image_path and image_path.exists():
                try:
                    image_path.unlink()
                except:
                    pass
            raise HTTPException(status_code=500, detail=f"保存参考图像失败: {str(e)}")
        
        # 处理LoRA配置
        lora_configs = []
        if loras:
            try:
                import json
                lora_data = json.loads(loras)
                if isinstance(lora_data, list):
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
            "fps": fps,
            "duration": duration,
            "model": model,
            "loras": lora_configs
        }
        
        print(f"🎬 接收到视频生成请求: description='{description[:50]}...', fps={fps}, duration={duration}")
        print(f"📊 参数详情: {parameters}")
        if lora_configs:
            print(f"🎨 LoRA配置: {lora_configs}")
        
        # 创建任务
        task_id = await task_manager.create_task(
            reference_image_path=str(image_path),
            description=f"视频生成: {description}",  # 添加视频生成标识
            parameters=parameters
        )
        
        print(f"✅ 视频生成任务创建成功: {task_id}")
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message="视频生成任务已创建"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建视频生成任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建视频生成任务失败: {str(e)}")


@app.post("/api/generate-image", response_model=TaskResponse)
async def generate_image(
    description: str = Form(...),
    reference_image: Optional[UploadFile] = File(None),
    reference_images: Optional[List[UploadFile]] = File(None),  # 支持多张参考图
    count: int = Form(DEFAULT_COUNT),
    size: str = Form(DEFAULT_IMAGE_SIZE),
    steps: int = Form(DEFAULT_STEPS),
    seed: Optional[int] = Form(None),
    model: str = Form(...),  # 模型选择参数（必填）
    loras: Optional[str] = Form(None),  # JSON字符串格式的LoRA配置
    duration: Optional[int] = Form(None),  # 视频时长（秒）
    fps: Optional[int] = Form(None)  # 视频帧率
):
    """生成图像API"""
    try:
        # 处理参考图像
        image_path = None
        image_paths = []
        
        # 处理多张参考图像（Flux模型2图融合）
        if reference_images and len(reference_images) > 0:
            print(f"🖼️ 处理多张参考图像: {len(reference_images)}张")
            for i, ref_img in enumerate(reference_images):
                try:
                    # 保存上传的参考图像
                    image_filename = f"{uuid.uuid4()}_{ref_img.filename}"
                    image_path = UPLOAD_DIR / image_filename
                    
                    # 读取文件内容
                    content = await ref_img.read()
                    
                    # 验证文件内容
                    if len(content) == 0:
                        print(f"❌ 参考图像{i+1}文件为空")
                        raise HTTPException(status_code=400, detail=f"参考图像{i+1}文件为空")
                    
                    if len(content) < MIN_FILE_SIZE:
                        print(f"❌ 参考图像{i+1}文件过小: {len(content)} 字节")
                        raise HTTPException(status_code=400, detail=f"参考图像{i+1}文件过小或损坏")
                    
                    # 保存文件
                    async with aiofiles.open(image_path, 'wb') as f:
                        await f.write(content)
                    
                    # 验证保存的文件
                    if not image_path.exists() or image_path.stat().st_size == 0:
                        print(f"❌ 参考图像{i+1}保存失败")
                        raise HTTPException(status_code=500, detail=f"参考图像{i+1}保存失败")
                    
                    # 复制文件到ComfyUI输入目录
                    from config.settings import COMFYUI_INPUT_DIR
                    import shutil
                    
                    comfyui_input_path = COMFYUI_INPUT_DIR / image_filename
                    shutil.copy2(image_path, comfyui_input_path)
                    print(f"✅ 复制参考图像{i+1}到ComfyUI输入目录: {comfyui_input_path}")
                    
                    image_paths.append(str(image_path))
                    print(f"✅ 保存参考图像{i+1}成功: {image_path} ({image_path.stat().st_size} 字节)")
                    
                except HTTPException:
                    raise
                except Exception as e:
                    print(f"❌ 保存参考图像{i+1}时出错: {e}")
                    # 如果保存失败，清理可能创建的文件
                    if image_path and image_path.exists():
                        try:
                            image_path.unlink()
                        except:
                            pass
                    raise HTTPException(status_code=500, detail=f"保存参考图像{i+1}失败: {str(e)}")
        
        # 处理单张参考图像（向后兼容）
        elif reference_image:
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
                
                # 复制文件到ComfyUI输入目录
                from config.settings import COMFYUI_INPUT_DIR
                import shutil
                
                comfyui_input_path = COMFYUI_INPUT_DIR / image_filename
                shutil.copy2(image_path, comfyui_input_path)
                print(f"✅ 复制参考图像到ComfyUI输入目录: {comfyui_input_path}")
                
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
        
        # 获取最优尺寸（使用配置客户端）
        try:
            from core.image_gen_config_manager import get_optimal_size
            optimal_width, optimal_height = await get_optimal_size(size, model)
            optimal_size = f"{optimal_width}x{optimal_height}"
            print(f"🎯 使用最优尺寸: {optimal_size} (原始: {size})")
        except Exception as config_error:
            print(f"⚠️ 获取最优尺寸失败，使用原始尺寸: {config_error}")
            optimal_size = size
        
        # 准备参数
        parameters = {
            "count": count,
            "size": optimal_size,  # 使用最优尺寸
            "steps": steps,
            "seed": seed,
            "model": model,  # 添加模型参数
            "loras": lora_configs
        }
        
        # 如果是视频模型，添加视频参数
        if model == "wan2.2-video" and duration is not None and fps is not None:
            parameters["duration"] = duration
            parameters["fps"] = fps
            print(f"🎬 视频生成参数: duration={duration}秒, fps={fps}")
        
        print(f"🔍 接收到生成请求: description='{description[:50]}...', count={count}, size={size}, steps={steps}")
        print(f"📊 参数详情: {parameters}")
        if lora_configs:
            print(f"🎨 LoRA配置: {lora_configs}")
        
        # 创建任务
        # 确定参考图像路径
        reference_path = ""
        if image_paths:
            # 多张参考图像
            reference_path = str(image_paths)
        elif image_path:
            # 单张参考图像
            reference_path = str(image_path)
        
        # 添加多图路径参数
        if image_paths:
            parameters["reference_image_paths"] = image_paths
        
        task_id = await task_manager.create_task(
            reference_path, description, parameters
        )
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="任务已提交，正在处理中"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@app.post("/api/generate-image-fusion", response_model=TaskResponse)
async def generate_image_fusion(
    description: str = Form(...),
    reference_images: List[UploadFile] = File(...),
    fusion_mode: str = Form("concat"),
    steps: int = Form(20),
    cfg: float = Form(2.5),
    seed: Optional[int] = Form(None),
    model: str = Form(...),
    loras: Optional[str] = Form(None),
    size: str = Form(DEFAULT_IMAGE_SIZE)  # 添加尺寸参数
):
    """多图融合生成API"""
    try:
        # 动态验证模型类型 - 从配置获取支持的融合模型
        try:
            from core.config_client import get_config_client
            config_client = get_config_client()
            models_config = await config_client.get_models_config()
            available_models = [m.get("name") for m in models_config.get("models", []) if m.get("available", True)]
            
            # 检查模型是否支持融合功能（这里可以根据实际需求调整）
            fusion_supported_models = [m for m in available_models if m in ['qwen-image', 'gemini-image']]
            
            if model not in fusion_supported_models:
                raise HTTPException(
                    status_code=400, 
                    detail=f"模型 {model} 不支持多图融合功能。支持的模型: {', '.join(fusion_supported_models)}"
                )
        except Exception as e:
            print(f"⚠️ 动态验证模型失败，使用默认验证: {e}")
            # 降级到默认验证
            if model not in ['qwen-image', 'gemini-image']:
                raise HTTPException(status_code=400, detail="多图融合只支持Qwen和Gemini模型")
        
        # 验证图像数量
        if len(reference_images) < 2:
            raise HTTPException(status_code=400, detail="多图融合至少需要2张图像")
        if len(reference_images) > 3:
            raise HTTPException(status_code=400, detail="多图融合最多支持3张图像")
        
        # 处理多张参考图像
        image_paths = []
        for i, reference_image in enumerate(reference_images):
            try:
                # 保存上传的参考图像
                image_filename = f"{uuid.uuid4()}_{reference_image.filename}"
                image_path = UPLOAD_DIR / image_filename
                
                # 读取文件内容
                content = await reference_image.read()
                
                # 验证文件内容
                if len(content) == 0:
                    print(f"❌ 参考图像{i+1}文件为空")
                    raise HTTPException(status_code=400, detail=f"参考图像{i+1}文件为空")
                
                if len(content) < MIN_FILE_SIZE:
                    print(f"❌ 参考图像{i+1}文件过小: {len(content)} 字节")
                    raise HTTPException(status_code=400, detail=f"参考图像{i+1}文件过小或损坏")
                
                # 保存文件
                async with aiofiles.open(image_path, 'wb') as f:
                    await f.write(content)
                
                # 验证保存的文件
                if not image_path.exists() or image_path.stat().st_size == 0:
                    print(f"❌ 参考图像{i+1}保存失败")
                    raise HTTPException(status_code=500, detail=f"参考图像{i+1}保存失败")
                
                # 复制文件到ComfyUI输入目录
                from config.settings import COMFYUI_INPUT_DIR
                import shutil
                
                comfyui_input_path = COMFYUI_INPUT_DIR / image_filename
                shutil.copy2(image_path, comfyui_input_path)
                print(f"✅ 复制参考图像{i+1}到ComfyUI输入目录: {comfyui_input_path}")
                
                image_paths.append(str(image_path))
                print(f"✅ 保存参考图像{i+1}成功: {image_path} ({image_path.stat().st_size} 字节)")
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"❌ 保存参考图像{i+1}时出错: {e}")
                # 清理已保存的文件
                for path in image_paths:
                    try:
                        Path(path).unlink()
                    except:
                        pass
                raise HTTPException(status_code=500, detail=f"保存参考图像{i+1}失败: {str(e)}")
        
        # 处理LoRA配置（多图融合暂不支持）
        lora_configs = []
        if loras:
            print("⚠️ 多图融合功能暂不支持LoRA配置")
        
        # 获取最优尺寸（使用配置客户端）
        try:
            from core.image_gen_config_manager import get_optimal_size
            optimal_width, optimal_height = await get_optimal_size(size, model)
            optimal_size = f"{optimal_width}x{optimal_height}"
            print(f"🎯 使用最优尺寸: {optimal_size} (原始: {size})")
        except Exception as config_error:
            print(f"⚠️ 获取最优尺寸失败，使用原始尺寸: {config_error}")
            optimal_size = size
        
        # 准备参数
        parameters = {
            "steps": steps,
            "cfg": cfg,
            "seed": seed,
            "model": model,
            "fusion_mode": fusion_mode,
            "size": optimal_size,  # 添加尺寸参数
            "loras": lora_configs
        }
        
        print(f"🔍 接收到多图融合请求: description='{description[:50]}...', 图像数量={len(image_paths)}, 融合模式={fusion_mode}, 尺寸={size}")
        print(f"📊 参数详情: {parameters}")
        
        # 创建多图融合任务
        task_id = await task_manager.create_fusion_task(
            reference_image_paths=image_paths,
            description=description,
            parameters=parameters
        )
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="多图融合任务已提交，正在处理中"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建多图融合任务失败: {str(e)}")


@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    # 尝试从缓存获取
    cached_task = cache_manager.get_task_cache(task_id)
    
    if cached_task:
        task = cached_task
    else:
        # 缓存未命中，从数据库获取
        task = task_manager.get_task_status(task_id)
        
        if task:
            # 缓存任务状态
            cache_manager.set_task_cache(task_id, task)
    
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
                    "image_urls": [f"/api/image/{task_id}/{i}" for i in range(len(result_paths))],
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

@app.get("/api/image/{task_id}/{image_index}")
async def get_generated_image_by_index(task_id: str, image_index: int):
    """根据索引获取生成的图像"""
    return await get_generated_image(task_id, index=image_index)

# 添加兼容路由，支持前端使用的 {index} 参数名
@app.get("/api/image/{task_id}/{index}")
async def get_generated_image_by_index_compat(task_id: str, index: int):
    """根据索引获取生成的图像（兼容前端请求）"""
    return await get_generated_image(task_id, index=index)

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
                        # 处理相对路径，转换为绝对路径
                        if not Path(path).is_absolute():
                            if path.startswith("outputs/"):
                                image_path = OUTPUT_DIR / path[8:]  # 去掉 "outputs/" 前缀
                            else:
                                image_path = OUTPUT_DIR / path
                        else:
                            image_path = Path(path)
                        found = True
                        break
                if not found:
                    raise HTTPException(status_code=404, detail=f"指定的文件名 {filename} 不存在")
            else:
                # 单个结果，检查是否匹配
                if Path(result_paths).name != filename and not Path(result_paths).name.endswith(f"/{filename}"):
                    raise HTTPException(status_code=404, detail=f"指定的文件名 {filename} 不存在")
                # 处理相对路径，转换为绝对路径
                if not Path(result_paths).is_absolute():
                    if result_paths.startswith("outputs/"):
                        image_path = OUTPUT_DIR / result_paths[8:]  # 去掉 "outputs/" 前缀
                    else:
                        image_path = OUTPUT_DIR / result_paths
                else:
                    image_path = Path(result_paths)
        else:
            # 使用索引获取图像
            if isinstance(result_paths, list):
                # 多个图像
                if index >= len(result_paths) or index < 0:
                    raise HTTPException(status_code=404, detail="图像索引不存在")
                # 处理相对路径，转换为绝对路径
                relative_path = result_paths[index]
                if not Path(relative_path).is_absolute():
                    # 如果是相对路径，需要根据路径前缀确定正确的目录
                    if relative_path.startswith("outputs/"):
                        image_path = OUTPUT_DIR / relative_path[8:]  # 去掉 "outputs/" 前缀
                    else:
                        image_path = OUTPUT_DIR / relative_path
                else:
                    image_path = Path(relative_path)
            else:
                # 单个图像（向后兼容）
                if index != 0:
                    raise HTTPException(status_code=404, detail="图像索引不存在")
                # 处理相对路径，转换为绝对路径
                relative_path = result_paths
                if not Path(relative_path).is_absolute():
                    # 如果是相对路径，需要根据路径前缀确定正确的目录
                    if relative_path.startswith("outputs/"):
                        image_path = OUTPUT_DIR / relative_path[8:]  # 去掉 "outputs/" 前缀
                    else:
                        image_path = OUTPUT_DIR / relative_path
                else:
                    image_path = Path(relative_path)
    except (json.JSONDecodeError, TypeError):
        # 如果不是JSON格式，按单个图像处理（向后兼容）
        if index != 0:
            raise HTTPException(status_code=404, detail="图像索引不存在")
        # 处理相对路径，转换为绝对路径
        relative_path = task["result_path"]
        if not Path(relative_path).is_absolute():
            if relative_path.startswith("outputs/"):
                image_path = OUTPUT_DIR / relative_path[8:]  # 去掉 "outputs/" 前缀
            else:
                image_path = OUTPUT_DIR / relative_path
        else:
            image_path = Path(relative_path)
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图像文件不存在")
    
    return FileResponse(image_path)

@app.get("/api/thumbnail/{thumbnail_filename}")
async def get_thumbnail(thumbnail_filename: str):
    """获取缩略图"""
    try:
        # 解析缩略图文件名格式: {task_id}_{index}_small.jpg
        if '_small.jpg' in thumbnail_filename:
            task_id = thumbnail_filename.replace('_small.jpg', '').rsplit('_', 1)[0]
            image_index = int(thumbnail_filename.replace('_small.jpg', '').rsplit('_', 1)[1])
            
            # 获取任务信息
            task = task_manager.get_task_status(task_id)
            if not task or task["status"] != "completed" or not task["result_path"]:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            # 解析结果路径
            import json
            result_path_str = task["result_path"]
            if not result_path_str or result_path_str.strip() == "":
                raise HTTPException(status_code=404, detail="任务结果路径为空")

            try:
                result_paths = json.loads(result_path_str)
                if not isinstance(result_paths, list):
                    result_paths = [result_paths]  # 如果不是数组，转为数组
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}, result_path: {result_path_str}")
                # 如果不是JSON格式，当作单个文件处理
                result_paths = [result_path_str]
            
            if isinstance(result_paths, list) and image_index < len(result_paths):
                original_path = result_paths[image_index]
                # 处理相对路径
                if not Path(original_path).is_absolute():
                    if original_path.startswith("outputs/"):
                        image_path = OUTPUT_DIR / original_path[8:]
                    else:
                        image_path = OUTPUT_DIR / original_path
                else:
                    image_path = Path(original_path)
                
                # 生成缩略图
                thumbnail_path = thumbnail_manager.generate_thumbnail(str(image_path), 'small')
                if thumbnail_path and thumbnail_path.exists():
                    return FileResponse(thumbnail_path)
                else:
                    # 如果缩略图生成失败，返回原图（作为临时方案）
                    if image_path.exists():
                        return FileResponse(image_path)
        
        # 如果无法解析或生成缩略图，返回404
        raise HTTPException(status_code=404, detail="缩略图不存在")
        
    except Exception as e:
        print(f"获取缩略图失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}")

@app.get("/api/video/{task_id}")
async def get_generated_video(task_id: str, filename: str = None):
    """获取生成的视频"""
    task = task_manager.get_task_status(task_id)
    
    if not task or task["status"] != "completed" or not task["result_path"]:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    try:
        # 尝试解析JSON格式的结果路径
        import json
        result_paths = json.loads(task["result_path"])
        
        # 如果指定了文件名，尝试查找匹配的文件
        if filename:
            if isinstance(result_paths, list):
                # 在结果列表中查找匹配的视频文件名
                found = False
                for path in result_paths:
                    if Path(path).name == filename or Path(path).name.endswith(f"/{filename}"):
                        video_path = Path(path)
                        found = True
                        break
                if not found:
                    raise HTTPException(status_code=404, detail=f"指定的文件名 {filename} 不存在")
            else:
                # 单个结果，检查是否匹配
                if Path(result_paths).name != filename and not Path(result_paths).name.endswith(f"/{filename}"):
                    raise HTTPException(status_code=404, detail=f"指定的文件名 {filename} 不存在")
                video_path = Path(result_paths)
        else:
            # 获取第一个视频文件
            if isinstance(result_paths, list):
                # 多个文件，查找第一个视频文件
                video_path = None
                for path in result_paths:
                    if Path(path).suffix.lower() in ['.mp4', '.avi', '.mov', '.webm']:
                        video_path = Path(path)
                        break
                if not video_path:
                    raise HTTPException(status_code=404, detail="未找到视频文件")
            else:
                # 单个文件
                video_path = Path(result_paths)
    except (json.JSONDecodeError, TypeError):
        # 如果不是JSON格式，按单个文件处理
        video_path = Path(task["result_path"])
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 检查文件扩展名是否为视频格式
    if video_path.suffix.lower() not in ['.mp4', '.avi', '.mov', '.webm']:
        raise HTTPException(status_code=400, detail="文件不是视频格式")
    
    return FileResponse(video_path, media_type="video/mp4")

@app.get("/api/history")
async def get_history(limit: int = 20, offset: int = 0, order: str = "asc", favorite_filter: str = None, time_filter: str = None):
    """获取历史记录"""
    try:
        # 尝试从缓存获取
        cached_result = cache_manager.get_history_cache(
            limit=limit, 
            offset=offset, 
            order=order, 
            favorite_filter=favorite_filter, 
            time_filter=time_filter
        )
        
        if cached_result:
            return cached_result
        
        # 缓存未命中，从数据库获取
        result = db_manager.get_tasks_with_filters(
            limit=limit, 
            offset=offset, 
            order=order, 
            favorite_filter=favorite_filter, 
            time_filter=time_filter
        )
        
        # 为每个任务添加缩略图URL
        for task in result.get('tasks', []):
            if task.get('image_urls'):
                task['thumbnail_urls'] = []
                for i, image_url in enumerate(task['image_urls']):
                    # 从image_url提取task_id
                    if '/api/image/' in image_url:
                        task_id = image_url.split('/api/image/')[1].split('/')[0]
                        # 生成缩略图URL
                        thumbnail_url = f"/api/thumbnail/{task_id}_{i}_small.jpg"
                        task['thumbnail_urls'].append(thumbnail_url)
                    else:
                        task['thumbnail_urls'].append(image_url)
        
        # 缓存结果
        cache_manager.set_history_cache(
            data=result,
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
        
        # 清除相关缓存
        cache_manager.invalidate_task_cache(task_id)
        cache_manager.invalidate_history_cache()
        
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


@app.post("/api/video/{task_id}/favorite")
async def toggle_video_favorite(task_id: str, filename: str = None):
    """切换视频收藏状态"""
    try:
        # 验证任务是否存在
        task = db_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        new_favorite = db_manager.toggle_video_favorite(task_id, filename)
        
        return {
            "task_id": task_id,
            "is_favorited": new_favorite,
            "message": "视频收藏状态已更新"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"切换视频收藏状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换视频收藏状态失败: {str(e)}")

@app.get("/api/favorites")
async def get_favorites():
    """获取收藏的图片和视频列表"""
    try:
        image_favorites = db_manager.get_favorite_images()
        video_favorites = db_manager.get_favorite_videos()
        
        # 合并图片和视频收藏
        all_favorites = image_favorites + video_favorites
        
        # 按创建时间排序
        all_favorites.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        return {
            "favorites": all_favorites,
            "total": len(all_favorites),
            "images": len(image_favorites),
            "videos": len(video_favorites)
        }
    except Exception as e:
        print(f"获取收藏列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取收藏列表失败: {str(e)}")

@app.get("/api/favorites/videos")
async def get_favorite_videos():
    """获取收藏的视频列表"""
    try:
        favorites = db_manager.get_favorite_videos()
        return {
            "favorites": favorites,
            "total": len(favorites)
        }
    except Exception as e:
        print(f"获取收藏视频列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取收藏视频列表失败: {str(e)}")


@app.delete("/api/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    try:
        # 先检查任务是否存在
        existing_task = db_manager.get_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 删除任务
        result_path = db_manager.delete_task(task_id)
        
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
        
        # 清除相关缓存
        cache_manager = get_cache_manager()
        cache_manager.invalidate_history_cache()
        cache_manager.invalidate_task_cache(task_id)
        cache_manager.invalidate_image_cache(task_id)
        print(f"🗑️ 已清除相关缓存，任务 {task_id} 已删除")
        
        return {
            "task_id": task_id,
            "message": "任务已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@app.delete("/api/favorites/images/{task_id}/{image_index}")
async def delete_image_favorite(task_id: str, image_index: int):
    """删除图片收藏"""
    try:
        print(f"收到删除图片收藏请求: task_id={task_id}, image_index={image_index}")
        
        # 先检查任务是否存在
        task = db_manager.get_task(task_id)
        if not task:
            print(f"任务不存在: {task_id}")
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        success = db_manager.remove_image_favorite(task_id, image_index)
        if not success:
            print(f"收藏记录不存在: task_id={task_id}, image_index={image_index}")
            raise HTTPException(status_code=404, detail=f"收藏记录不存在: task_id={task_id}, image_index={image_index}")
        
        # 清除相关缓存
        cache_manager = get_cache_manager()
        cache_manager.invalidate_history_cache()
        cache_manager.invalidate_task_cache(task_id)
        cache_manager.invalidate_image_cache(task_id)
        print(f"🗑️ 已清除相关缓存，图片收藏 {task_id}/{image_index} 已删除")
        
        print(f"成功删除图片收藏: task_id={task_id}, image_index={image_index}")
        return {
            "task_id": task_id,
            "image_index": image_index,
            "message": "图片收藏已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除图片收藏失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除图片收藏失败: {str(e)}")

@app.delete("/api/favorites/videos/{task_id}")
async def delete_video_favorite(task_id: str):
    """删除视频收藏"""
    try:
        success = db_manager.remove_video_favorite(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="收藏记录不存在")
        
        # 清除相关缓存
        cache_manager = get_cache_manager()
        cache_manager.invalidate_history_cache()
        cache_manager.invalidate_task_cache(task_id)
        cache_manager.invalidate_image_cache(task_id)
        print(f"🗑️ 已清除相关缓存，视频收藏 {task_id} 已删除")
        
        return {
            "task_id": task_id,
            "message": "视频收藏已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除视频收藏失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除视频收藏失败: {str(e)}")

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
    
    # 获取缓存统计信息
    cache_stats = cache_manager.get_cache_stats()
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "database_connected": db_healthy,
        "comfyui_connected": comfyui_status,
        "redis_cache": cache_stats,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/config/status")
async def config_status():
    """配置状态检查"""
    try:
        # 导入配置客户端
        from core.config_client import get_config_client
        
        config_client = get_config_client()
        
        # 检查后台服务健康状态
        backend_healthy = await config_client.check_backend_health()
        
        # 获取缓存状态
        cache_status = config_client.get_cache_status()
        
        # 获取配置信息
        try:
            all_configs = await config_client.get_all_configs()
            config_source = all_configs.get("config_source", "unknown")
            last_updated = all_configs.get("last_updated", "unknown")
        except Exception as e:
            config_source = "error"
            last_updated = "unknown"
        
        return {
            "status": "healthy" if backend_healthy else "degraded",
            "backend_connected": backend_healthy,
            "config_source": config_source,
            "last_config_update": last_updated,
            "cache_status": cache_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "backend_connected": False,
            "config_source": "error",
            "last_config_update": "unknown",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/config/image-gen")
async def get_image_gen_config():
    """获取生图配置"""
    try:
        from core.image_gen_config_manager import get_image_gen_config_summary
        
        config_summary = await get_image_gen_config_summary()
        return config_summary
    except Exception as e:
        return {
            "default_size": {"width": 1024, "height": 1024, "string": "1024x1024"},
            "default_steps": 20,
            "default_count": 1,
            "supported_ratios": ["1:1", "4:3", "3:4", "16:9", "9:16"],
            "supported_formats": ["png", "jpg", "jpeg", "webp"],
            "quality_settings": {
                "low": {"steps": 10, "cfg": 7.0},
                "medium": {"steps": 20, "cfg": 8.0},
                "high": {"steps": 30, "cfg": 9.0}
            },
            "config_source": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
