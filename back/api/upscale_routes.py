#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像高清放大API路由
"""

import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pathlib import Path

from core.upscale_manager import UpscaleManager
from core.comfyui_client import ComfyUIClient
from models.upscale_schemas import (
    UpscaleRequest, 
    UpscaleResponse, 
    UpscaleStatusResponse,
    UpscaleResult,
    AVAILABLE_ALGORITHMS
)
from config.settings import (
    COMFYUI_URL, UPLOAD_DIR, OUTPUT_DIR
)

# 创建路由器
router = APIRouter(prefix="/api/upscale", tags=["图像放大"])

# 全局变量存储放大管理器实例
upscale_manager: UpscaleManager = None

def get_upscale_manager() -> UpscaleManager:
    """获取放大管理器实例"""
    global upscale_manager
    if upscale_manager is None:
        comfyui_client = ComfyUIClient(COMFYUI_URL)
        # 导入数据库管理器
        from core.database_manager import DatabaseManager
        from config.settings import DB_PATH
        db_manager = DatabaseManager(DB_PATH)
        upscale_manager = UpscaleManager(comfyui_client, OUTPUT_DIR, db_manager)
    return upscale_manager


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
