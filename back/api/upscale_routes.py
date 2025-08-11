#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像高清放大API路由
"""

import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pathlib import Path

from core.service_manager import get_upscale_manager
from models.upscale_schemas import (
    UpscaleRequest, 
    UpscaleResponse, 
    UpscaleStatusResponse,
    UpscaleResult,
    AVAILABLE_ALGORITHMS
)
from config.settings import (
    UPLOAD_DIR, OUTPUT_DIR
)

# 创建路由器
router = APIRouter(prefix="/api/upscale", tags=["图像放大"])


@router.post("/", response_model=UpscaleResponse)
async def upscale_image(
    image: UploadFile = File(..., description="要放大的图像文件"),
    scale_factor: int = Form(default=2, ge=1, le=4, description="放大倍数"),
    algorithm: str = Form(default="ultimate", description="放大算法")
):
    """图像高清放大接口"""
    try:
        # 验证算法（现在主要支持UltimateSDUpscale）
        if algorithm not in AVAILABLE_ALGORITHMS and algorithm != "ultimate":
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的放大算法: {algorithm}，推荐使用 ultimate"
            )
        
        # 验证文件类型
        if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            raise HTTPException(
                status_code=400, 
                detail="只支持PNG、JPG、JPEG、WEBP格式的图像"
            )
        
        # 保存上传的图像
        upload_dir = Path(UPLOAD_DIR)
        upload_dir.mkdir(exist_ok=True)
        
        image_filename = f"upscale_{image.filename}"
        image_path = upload_dir / image_filename
        
        # 读取并保存文件
        content = await image.read()
        with open(image_path, 'wb') as f:
            f.write(content)
        
        # 获取放大管理器
        manager = get_upscale_manager()
        
        # 提交放大任务
        result = await manager.upscale_image(
            str(image_path),
            scale_factor,
            algorithm
        )
        
        return UpscaleResponse(
            task_id=result["task_id"],
            status=result["status"],
            message="放大任务已提交，正在处理中",
            scale_factor=scale_factor,
            algorithm=algorithm
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"放大任务创建失败: {str(e)}")


@router.post("/by-path", response_model=UpscaleResponse)
async def upscale_image_by_path(
    image_path: str = Form(..., description="要放大的图像文件路径"),
    scale_factor: int = Form(default=2, ge=1, le=4, description="放大倍数"),
    algorithm: str = Form(default="ultimate", description="放大算法")
):
    """通过文件路径进行图像高清放大接口"""
    try:
        # 验证算法
        if algorithm not in AVAILABLE_ALGORITHMS and algorithm != "ultimate":
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的放大算法: {algorithm}，推荐使用 ultimate"
            )
        
        # 解析路径
        print(f"🔍 原始图像路径: {image_path}")
        
        # 处理不同的路径格式
        if image_path.startswith('/api/images/') or image_path.startswith('\\api\\image\\') or image_path.startswith('/api/image/'):
            # 前端传递的格式: 
            # - /api/images/task_id/filename
            # - \api\image\task_id?index=N
            # - /api/image/task_id?index=N
            
            # 标准化路径分隔符
            normalized_path = image_path.replace('\\', '/').replace('/api/image/', '/api/images/')
            
            # 解析查询参数 (如 ?index=0)
            query_params = {}
            if '?' in normalized_path:
                path_part, query_part = normalized_path.split('?', 1)
                normalized_path = path_part
                # 解析查询参数
                for param in query_part.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
            
            path_parts = normalized_path.split('/')
            
            if len(path_parts) >= 4:
                task_id = path_parts[3]
                filename = path_parts[4] if len(path_parts) > 4 else None
                image_index = int(query_params.get('index', 0))  # 获取index参数
                
                print(f"📁 任务ID: {task_id}")
                print(f"📝 图片索引: {image_index}")
                
                # 如果没有指定文件名，需要在outputs目录中查找该任务的图片
                if not filename:
                    print(f"🔍 在outputs目录中查找task_id: {task_id}, index: {image_index}")
                    
                    # 查找与该任务相关的图片文件
                    # 从数据库中获取该任务的实际图片路径
                    pattern_files = []
                    
                    # 方法1: 从数据库查询该任务的图片路径
                    from core.database_manager import DatabaseManager
                    from config.settings import DB_PATH
                    
                    try:
                        db_manager = DatabaseManager(DB_PATH)
                        task_info = db_manager.get_task(task_id)
                        
                        if task_info and task_info.get('result_path'):
                            import json
                            image_paths = json.loads(task_info['result_path'])
                            print(f"📋 数据库中的图片路径: {image_paths}")
                            
                            # 根据index参数选择正确的图片
                            if 0 <= image_index < len(image_paths):
                                target_image_path = image_paths[image_index]
                                print(f"🎯 目标图片路径 (index={image_index}): {target_image_path}")
                                
                                # 构建完整文件路径
                                file_path = Path(target_image_path)
                                actual_file_path = OUTPUT_DIR.parent / file_path
                                if actual_file_path.exists():
                                    pattern_files.append(actual_file_path)
                                    print(f"✅ 找到目标文件: {actual_file_path}")
                                else:
                                    print(f"❌ 目标文件不存在: {actual_file_path}")
                            else:
                                print(f"❌ 无效的index值: {image_index}, 总共有 {len(image_paths)} 张图片")
                            
                            # 备用方案：从路径中提取实际文件名 (如果上面的精确匹配失败)
                            if not pattern_files:
                                print("🔄 使用备用方案：遍历所有图片路径")
                                for url in image_paths:
                                    if isinstance(url, str) and 'outputs/' in url:
                                        # 提取文件路径，如 "outputs/yeepay_00327_.png"
                                        file_path = Path(url)
                                        actual_file_path = OUTPUT_DIR.parent / file_path  # 因为url已包含outputs/前缀
                                        if actual_file_path.exists():
                                            pattern_files.append(actual_file_path)
                                            print(f"📄 从数据库找到文件: {actual_file_path}")
                    except Exception as e:
                        print(f"⚠️ 数据库查询失败: {e}")
                    
                    # 方法2: 传统方式查找
                    if not pattern_files:
                        # 在根目录查找包含task_id的文件
                        root_files = list(OUTPUT_DIR.glob(f"*{task_id}*.png")) + list(OUTPUT_DIR.glob(f"*{task_id}*.jpg")) + list(OUTPUT_DIR.glob(f"*{task_id}*.jpeg"))
                        pattern_files.extend(root_files)
                        
                        # 在任务ID子目录中查找
                        task_dir = OUTPUT_DIR / task_id
                        if task_dir.exists() and task_dir.is_dir():
                            print(f"📁 检查任务目录: {task_dir}")
                            task_files = list(task_dir.glob("*.png")) + list(task_dir.glob("*.jpg")) + list(task_dir.glob("*.jpeg"))
                            pattern_files.extend(task_files)
                            print(f"📄 任务目录中的文件: {[f.name for f in task_files]}")
                        
                        # 递归查找所有子目录中包含task_id的文件
                        recursive_files = list(OUTPUT_DIR.glob(f"**/*{task_id}*.png")) + list(OUTPUT_DIR.glob(f"**/*{task_id}*.jpg")) + list(OUTPUT_DIR.glob(f"**/*{task_id}*.jpeg"))
                        pattern_files.extend(recursive_files)
                    
                    print(f"📁 找到的匹配文件: {[f.name for f in pattern_files]}")
                    
                    if pattern_files:
                        # 如果找到多个文件，取第一个
                        local_image_path = pattern_files[0]
                        filename = local_image_path.name
                        print(f"📄 自动找到文件: {filename}")
                        print(f"📂 文件完整路径: {local_image_path}")
                    else:
                        # 列出所有文件进行调试
                        all_files = list(OUTPUT_DIR.glob("*"))
                        print(f"📂 outputs目录中所有文件: {[f.name for f in all_files[:10]]}")
                        
                        # 检查是否有任务ID目录
                        if task_dir.exists():
                            sub_files = list(task_dir.glob("*"))
                            print(f"📂 {task_id}目录中的文件: {[f.name for f in sub_files[:10]]}")
                        
                        raise HTTPException(
                            status_code=404,
                            detail=f"未找到任务 {task_id} 相关的图片文件。请检查outputs目录结构。"
                        )
                else:
                    # 构建本地文件路径
                    local_image_path = OUTPUT_DIR / filename
                
                print(f"📄 最终文件名: {filename}")
                print(f"📂 本地路径: {local_image_path}")
                
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无效的图像路径格式: {image_path}"
                )
        elif image_path.startswith('http'):
            # 处理完整URL，提取文件名
            from urllib.parse import urlparse
            parsed_url = urlparse(image_path)
            path_parts = parsed_url.path.split('/')
            
            # 查找文件名（通常是最后一个部分）
            filename = None
            for part in reversed(path_parts):
                if part and '.' in part:  # 包含扩展名的部分
                    filename = part
                    break
            
            if not filename:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无法从URL中提取文件名: {image_path}"
                )
            
            # 构建本地文件路径
            local_image_path = OUTPUT_DIR / filename
            
            print(f"🌐 URL解析:")
            print(f"   原始URL: {image_path}")
            print(f"   提取文件名: {filename}")
            print(f"   本地路径: {local_image_path}")
            
        else:
            # 直接使用传递的路径
            local_image_path = Path(image_path)
            print(f"📂 直接路径: {local_image_path}")
        
        # 验证文件是否存在
        if not local_image_path.exists():
            # 尝试查找可能的文件
            print(f"❌ 文件不存在: {local_image_path}")
            
            # 列出outputs目录中的文件
            if OUTPUT_DIR.exists():
                available_files = list(OUTPUT_DIR.glob("*.png")) + list(OUTPUT_DIR.glob("*.jpg")) + list(OUTPUT_DIR.glob("*.jpeg"))
                print(f"📂 可用文件: {[f.name for f in available_files[:10]]}")  # 只显示前10个
            
            raise HTTPException(
                status_code=404, 
                detail=f"源图像文件不存在: {local_image_path}"
            )
        
        # 获取放大管理器
        manager = get_upscale_manager()
        
        # 提交放大任务
        result = await manager.upscale_image(
            str(local_image_path),
            scale_factor,
            algorithm
        )
        
        return UpscaleResponse(
            task_id=result["task_id"],
            status=result["status"],
            message="放大任务已提交，正在处理中",
            scale_factor=scale_factor,
            algorithm=algorithm
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 通过路径放大失败: {str(e)}")
        import traceback
        print(f"❌ 详细错误信息: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"放大任务创建失败: {str(e)}")


@router.get("/{task_id}", response_model=UpscaleStatusResponse)
async def get_upscale_status(task_id: str):
    """获取放大任务状态"""
    try:
        manager = get_upscale_manager()
        
        # 检查任务结果
        result = await manager.get_upscale_result(task_id)
        
        if result:
            # 任务完成
            # 将文件路径转换为可访问的URL
            upscaled_urls = []
            for image_path in result["upscaled_images"]:
                # 从完整路径中提取文件名
                filename = Path(image_path).name
                # 构建API访问URL
                upscaled_urls.append(f"/api/upscale/image/{task_id}/{filename}")
            
            return UpscaleStatusResponse(
                task_id=task_id,
                status="completed",
                progress=100,
                result={
                    "original_image": f"/api/upscale/image/{task_id}/original",
                    "upscaled_images": upscaled_urls,
                    "output_dir": result["output_dir"]
                }
            )
        else:
            # 任务仍在处理中
            return UpscaleStatusResponse(
                task_id=task_id,
                status="processing",
                progress=50,
                result=None
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.get("/image/{task_id}/{filename}")
async def get_upscale_image(task_id: str, filename: str):
    """获取放大后的图片"""
    try:
        # 构建文件路径
        task_output_dir = Path("outputs") / task_id
        image_path = task_output_dir / filename
        
        print(f"🔍 查找放大图片: {image_path}")
        print(f"📁 文件是否存在: {image_path.exists()}")
        
        if not image_path.exists():
            # 列出目录中的所有文件，帮助调试
            if task_output_dir.exists():
                files = list(task_output_dir.glob("*"))
                print(f"📂 目录中的文件: {[f.name for f in files]}")
            else:
                print(f"❌ 任务目录不存在: {task_output_dir}")
            raise HTTPException(status_code=404, detail=f"图片文件不存在: {filename}")
        
        # 返回图片文件
        from fastapi.responses import FileResponse
        return FileResponse(str(image_path), media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.get("/algorithms/list")
async def list_algorithms():
    """获取可用的放大算法列表"""
    return {
        "algorithms": list(AVAILABLE_ALGORITHMS.values()),
        "total": len(AVAILABLE_ALGORITHMS)
    }


@router.get("/algorithms/{algorithm_name}")
async def get_algorithm_info(algorithm_name: str):
    """获取特定算法的详细信息"""
    if algorithm_name not in AVAILABLE_ALGORITHMS:
        raise HTTPException(
            status_code=404, 
            detail=f"算法不存在: {algorithm_name}"
        )
    
    return AVAILABLE_ALGORITHMS[algorithm_name]


@router.delete("/{task_id}")
async def cleanup_upscale_task(task_id: str):
    """清理放大任务文件"""
    try:
        manager = get_upscale_manager()
        success = await manager.cleanup_task(task_id)
        
        if success:
            return {"message": "任务文件清理成功"}
        else:
            raise HTTPException(status_code=500, detail="任务文件清理失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")


@router.post("/batch")
async def batch_upscale(
    images: list[UploadFile] = File(..., description="要放大的图像文件列表"),
    scale_factor: int = Form(default=2, ge=1, le=4, description="放大倍数"),
    algorithm: str = Form(default="lanczos", description="放大算法")
):
    """批量图像放大接口"""
    try:
        # 验证算法（现在主要支持UltimateSDUpscale）
        if algorithm not in AVAILABLE_ALGORITHMS and algorithm != "ultimate":
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的放大算法: {algorithm}，推荐使用 ultimate"
            )
        
        manager = get_upscale_manager()
        tasks = []
        
        for image in images:
            # 验证文件类型
            if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            
            # 保存上传的图像
            upload_dir = Path(UPLOAD_DIR)
            upload_dir.mkdir(exist_ok=True)
            
            image_filename = f"batch_upscale_{image.filename}"
            image_path = upload_dir / image_filename
            
            # 读取并保存文件
            content = await image.read()
            with open(image_path, 'wb') as f:
                f.write(content)
            
            # 创建放大任务
            task = manager.upscale_image(
                str(image_path),
                scale_factor,
                algorithm
            )
            tasks.append(task)
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        successful_tasks = []
        failed_tasks = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_tasks.append({
                    "index": i,
                    "filename": images[i].filename,
                    "error": str(result)
                })
            else:
                successful_tasks.append({
                    "index": i,
                    "filename": images[i].filename,
                    "task_id": result["task_id"]
                })
        
        return {
            "total_images": len(images),
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "scale_factor": scale_factor,
            "algorithm": algorithm
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量放大失败: {str(e)}")
