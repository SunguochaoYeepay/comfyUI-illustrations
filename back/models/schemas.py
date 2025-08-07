#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块
包含所有Pydantic模型定义和API响应模式
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel

from config.settings import DEFAULT_COUNT, DEFAULT_IMAGE_SIZE, DEFAULT_STEPS


class GenerateImageRequest(BaseModel):
    """图像生成请求模型"""
    description: str
    parameters: Optional[Dict[str, Any]] = {
        "count": DEFAULT_COUNT,
        "size": DEFAULT_IMAGE_SIZE,
        "steps": DEFAULT_STEPS,
        "seed": None
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
