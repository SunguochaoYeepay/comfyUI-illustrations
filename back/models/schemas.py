#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块
包含所有Pydantic模型定义和API响应模式
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

from config.settings import DEFAULT_COUNT, DEFAULT_IMAGE_SIZE, DEFAULT_STEPS


class LoRAConfig(BaseModel):
    """LoRA配置模型"""
    name: str = Field(..., description="LoRA文件名（.safetensors格式）")
    strength_model: float = Field(1.0, ge=0.0, le=2.0, description="UNET权重强度 (0.0-2.0)")
    strength_clip: float = Field(1.0, ge=0.0, le=2.0, description="CLIP权重强度 (0.0-2.0)")
    trigger_word: Optional[str] = Field(None, description="触发词（可选）")
    enabled: bool = Field(True, description="是否启用此LoRA")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "anime_style.safetensors",
                "strength_model": 0.8,
                "strength_clip": 0.7,
                "trigger_word": "anime style",
                "enabled": True
            }
        }


class GenerateImageRequest(BaseModel):
    """图像生成请求模型"""
    description: str = Field(..., description="图像描述文本")
    parameters: Optional[Dict[str, Any]] = Field(
        default={
            "count": DEFAULT_COUNT,
            "size": DEFAULT_IMAGE_SIZE,
            "steps": DEFAULT_STEPS,
            "seed": None
        },
        description="生成参数"
    )
    loras: Optional[List[LoRAConfig]] = Field(
        default=[],
        max_items=4,
        description="LoRA配置列表（最多4个）"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "description": "A beautiful anime girl with blue hair",
                "parameters": {
                    "count": 1,
                    "steps": 20,
                    "seed": 12345
                },
                "loras": [
                    {
                        "name": "anime_style.safetensors",
                        "strength_model": 0.8,
                        "strength_clip": 0.7,
                        "trigger_word": "anime style",
                        "enabled": True
                    }
                ]
            }
        }


class GenerateFusionRequest(BaseModel):
    """多图融合请求模型"""
    description: str = Field(..., description="融合描述文本")
    fusion_mode: str = Field("concat", description="融合模式：concat(拼接), blend(混合), edit(编辑)")
    parameters: Optional[Dict[str, Any]] = Field(
        default={
            "steps": DEFAULT_STEPS,
            "seed": None,
            "cfg": 2.5
        },
        description="生成参数"
    )
    loras: Optional[List[LoRAConfig]] = Field(
        default=[],
        max_items=4,
        description="LoRA配置列表（最多4个，多图融合暂不支持）"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "description": "将三张图像拼接后，让左边的女人手里拎着中间棕色的包，坐在白色沙发上",
                "fusion_mode": "concat",
                "parameters": {
                    "steps": 20,
                    "cfg": 2.5,
                    "seed": 12345
                },
                "loras": []
            }
        }


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
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


class HistoryResponse(BaseModel):
    """历史记录响应模型"""
    tasks: list
    total: int
    has_more: bool
    limit: int
    offset: int
    order: str


class FavoriteResponse(BaseModel):
    """收藏状态响应模型"""
    task_id: str
    is_favorited: bool
    message: str


class DeleteResponse(BaseModel):
    """删除响应模型"""
    task_id: str
    message: str


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    comfyui_connected: bool
    timestamp: str
