#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YeePay AI图像生成服务 - 数据模型定义
定义API请求和响应的数据结构
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class TaskResponse(BaseModel):
    """任务创建响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="任务进度百分比")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")


class HistoryResponse(BaseModel):
    """历史记录响应"""
    tasks: List[Dict[str, Any]] = Field(..., description="任务列表")
    total: int = Field(..., description="总任务数")
    limit: int = Field(..., description="每页限制")
    offset: int = Field(..., description="偏移量")


class FavoriteResponse(BaseModel):
    """收藏响应"""
    task_id: str = Field(..., description="任务ID")
    is_favorited: bool = Field(..., description="是否已收藏")
    message: str = Field(..., description="响应消息")


class DeleteResponse(BaseModel):
    """删除响应"""
    task_id: str = Field(..., description="任务ID")
    message: str = Field(..., description="响应消息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    database_connected: bool = Field(..., description="数据库连接状态")
    comfyui_connected: bool = Field(..., description="ComfyUI连接状态")
    redis_cache: Optional[Dict[str, Any]] = Field(None, description="Redis缓存状态")
    timestamp: str = Field(..., description="检查时间戳")


class GenerateFusionRequest(BaseModel):
    """多图融合生成请求"""
    description: str = Field(..., description="描述文本")
    reference_images: List[str] = Field(..., description="参考图像路径列表")
    fusion_mode: str = Field(default="concat", description="融合模式")
    steps: int = Field(default=20, description="生成步数")
    cfg: float = Field(default=2.5, description="CFG值")
    seed: Optional[int] = Field(None, description="随机种子")
    model: str = Field(..., description="模型名称")
    size: str = Field(default="1024x1024", description="图像尺寸")


class ImageGenerationRequest(BaseModel):
    """图像生成请求"""
    description: str = Field(..., description="描述文本")
    reference_image: Optional[str] = Field(None, description="参考图像路径")
    count: int = Field(default=1, description="生成数量")
    size: str = Field(default="1024x1024", description="图像尺寸")
    steps: int = Field(default=20, description="生成步数")
    seed: Optional[int] = Field(None, description="随机种子")
    model: str = Field(..., description="模型名称")
    loras: Optional[List[Dict[str, Any]]] = Field(None, description="LoRA配置")


class VideoGenerationRequest(BaseModel):
    """视频生成请求"""
    description: str = Field(..., description="描述文本")
    reference_image: str = Field(..., description="参考图像路径")
    fps: int = Field(default=16, description="帧率")
    duration: int = Field(default=5, description="时长（秒）")
    model: str = Field(..., description="模型名称")
    loras: Optional[List[Dict[str, Any]]] = Field(None, description="LoRA配置")


class TranslationRequest(BaseModel):
    """翻译请求"""
    text: str = Field(..., description="待翻译文本")


class TranslationResponse(BaseModel):
    """翻译响应"""
    original: str = Field(..., description="原文")
    translated: str = Field(..., description="译文")
    success: bool = Field(..., description="是否成功")
    timestamp: str = Field(..., description="时间戳")


class ConfigStatusResponse(BaseModel):
    """配置状态响应"""
    status: str = Field(..., description="配置状态")
    backend_connected: bool = Field(..., description="后台服务连接状态")
    config_source: str = Field(..., description="配置来源")
    last_config_update: str = Field(..., description="最后配置更新时间")
    cache_status: Optional[Dict[str, Any]] = Field(None, description="缓存状态")
    timestamp: str = Field(..., description="检查时间戳")


class ImageGenConfigResponse(BaseModel):
    """图像生成配置响应"""
    default_size: Dict[str, Union[int, str]] = Field(..., description="默认尺寸")
    default_steps: int = Field(..., description="默认步数")
    default_count: int = Field(..., description="默认数量")
    supported_ratios: List[str] = Field(..., description="支持的宽高比")
    supported_formats: List[str] = Field(..., description="支持的格式")
    quality_settings: Dict[str, Dict[str, Union[int, float]]] = Field(..., description="质量设置")
    config_source: str = Field(..., description="配置来源")
    timestamp: str = Field(..., description="时间戳")
    error: Optional[str] = Field(None, description="错误信息")


class ModelListResponse(BaseModel):
    """模型列表响应"""
    models: List[Dict[str, Any]] = Field(..., description="模型列表")
    config_source: str = Field(..., description="配置来源")
    timestamp: str = Field(..., description="时间戳")
    error: Optional[str] = Field(None, description="错误信息")


class LoRAListResponse(BaseModel):
    """LoRA列表响应"""
    loras: List[Dict[str, Any]] = Field(..., description="LoRA列表")
    config_source: str = Field(..., description="配置来源")
    timestamp: str = Field(..., description="时间戳")
    error: Optional[str] = Field(None, description="错误信息")


class UploadResponse(BaseModel):
    """上传响应"""
    message: str = Field(..., description="响应消息")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小")


class FavoritesResponse(BaseModel):
    """收藏列表响应"""
    favorites: List[Dict[str, Any]] = Field(..., description="收藏列表")
    total: int = Field(..., description="总数")
    images: int = Field(..., description="图片数量")
    videos: int = Field(..., description="视频数量")
