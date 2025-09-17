#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YeePay AI图像生成服务 - 图像放大相关数据模型定义
定义图像放大API请求和响应的数据结构
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class UpscaleRequest(BaseModel):
    """图像放大请求"""
    image_path: str = Field(..., description="图像文件路径")
    scale_factor: int = Field(default=2, ge=1, le=4, description="放大倍数")
    algorithm: str = Field(default="ultimate", description="放大算法")


class UpscaleResponse(BaseModel):
    """图像放大响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    scale_factor: int = Field(..., description="放大倍数")
    algorithm: str = Field(..., description="使用的算法")


class UpscaleStatusResponse(BaseModel):
    """图像放大状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="任务进度百分比")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")


class UpscaleResult(BaseModel):
    """图像放大结果"""
    task_id: str = Field(..., description="任务ID")
    original_image: str = Field(..., description="原始图像路径")
    upscaled_images: List[str] = Field(..., description="放大后的图像路径列表")
    output_dir: str = Field(..., description="输出目录")
    scale_factor: int = Field(..., description="放大倍数")
    algorithm: str = Field(..., description="使用的算法")


class BatchUpscaleRequest(BaseModel):
    """批量图像放大请求"""
    image_paths: List[str] = Field(..., description="图像文件路径列表")
    scale_factor: int = Field(default=2, ge=1, le=4, description="放大倍数")
    algorithm: str = Field(default="ultimate", description="放大算法")


class BatchUpscaleResponse(BaseModel):
    """批量图像放大响应"""
    total_images: int = Field(..., description="总图像数量")
    successful_tasks: List[Dict[str, Any]] = Field(..., description="成功的任务列表")
    failed_tasks: List[Dict[str, Any]] = Field(..., description="失败的任务列表")
    scale_factor: int = Field(..., description="放大倍数")
    algorithm: str = Field(..., description="使用的算法")


class AlgorithmInfo(BaseModel):
    """算法信息"""
    name: str = Field(..., description="算法名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="算法描述")
    supported_formats: List[str] = Field(..., description="支持的格式")
    max_scale_factor: int = Field(..., description="最大放大倍数")
    quality: str = Field(..., description="质量等级")


# 可用的放大算法配置
AVAILABLE_ALGORITHMS = {
    "ultimate": AlgorithmInfo(
        name="ultimate",
        display_name="Ultimate SD Upscale",
        description="基于AI的超分辨率放大算法，提供最佳质量",
        supported_formats=["png", "jpg", "jpeg", "webp"],
        max_scale_factor=4,
        quality="high"
    ),
    "lanczos": AlgorithmInfo(
        name="lanczos",
        display_name="Lanczos",
        description="传统的高质量插值算法",
        supported_formats=["png", "jpg", "jpeg", "webp"],
        max_scale_factor=4,
        quality="medium"
    ),
    "bicubic": AlgorithmInfo(
        name="bicubic",
        display_name="Bicubic",
        description="双三次插值算法",
        supported_formats=["png", "jpg", "jpeg", "webp"],
        max_scale_factor=4,
        quality="medium"
    ),
    "nearest": AlgorithmInfo(
        name="nearest",
        display_name="Nearest Neighbor",
        description="最近邻插值算法，速度快但质量较低",
        supported_formats=["png", "jpg", "jpeg", "webp"],
        max_scale_factor=4,
        quality="low"
    )
}
