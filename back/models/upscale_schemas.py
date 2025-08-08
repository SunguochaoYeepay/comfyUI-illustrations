#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
放大服务相关的数据模型
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class UpscaleRequest(BaseModel):
    """放大请求模型"""
    image_path: str = Field(..., description="输入图像路径")
    scale_factor: int = Field(default=2, ge=1, le=4, description="放大倍数 (1-4)")
    algorithm: str = Field(default="ultimate", description="放大算法")


class UpscaleResponse(BaseModel):
    """放大响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")
    scale_factor: int = Field(..., description="放大倍数")
    algorithm: str = Field(..., description="使用的算法")


class UpscaleStatusResponse(BaseModel):
    """放大状态响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比 (0-100)")
    result: Optional[dict] = Field(None, description="结果信息")
    error: Optional[str] = Field(None, description="错误信息")


class UpscaleResult(BaseModel):
    """放大结果模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    original_image: str = Field(..., description="原始图像路径")
    upscaled_images: List[str] = Field(..., description="放大后的图像路径列表")
    output_dir: str = Field(..., description="输出目录")
    scale_factor: int = Field(..., description="放大倍数")
    algorithm: str = Field(..., description="使用的算法")


class UpscaleAlgorithm(BaseModel):
    """放大算法信息模型"""
    name: str = Field(..., description="算法名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="算法描述")
    supported_scales: List[int] = Field(..., description="支持的放大倍数")
    quality: str = Field(..., description="质量等级 (high/medium/low)")
    speed: str = Field(..., description="速度等级 (fast/medium/slow)")


# 预定义的放大算法（主要支持UltimateSDUpscale）
AVAILABLE_ALGORITHMS = {
    "ultimate": UpscaleAlgorithm(
        name="ultimate",
        display_name="UltimateSDUpscale",
        description="基于AI的专业放大算法，使用4x-UltraSharp模型，支持2-4倍放大",
        supported_scales=[2, 3, 4],
        quality="very_high",
        speed="medium"
    ),
    "lanczos": UpscaleAlgorithm(
        name="lanczos",
        display_name="Lanczos插值",
        description="高质量插值算法，适合照片和图像",
        supported_scales=[2, 3, 4],
        quality="high",
        speed="fast"
    ),
    "bicubic": UpscaleAlgorithm(
        name="bicubic",
        display_name="双三次插值",
        description="平衡质量和速度的插值算法",
        supported_scales=[2, 3, 4],
        quality="medium",
        speed="fast"
    ),
    "bilinear": UpscaleAlgorithm(
        name="bilinear",
        display_name="双线性插值",
        description="快速插值算法，适合实时处理",
        supported_scales=[2, 3, 4],
        quality="medium",
        speed="very_fast"
    ),
    "nearest": UpscaleAlgorithm(
        name="nearest",
        display_name="最近邻插值",
        description="最快的插值算法，保持像素边界",
        supported_scales=[2, 3, 4],
        quality="low",
        speed="very_fast"
    )
}
