#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前台配置API路由
为前台提供统一的配置接口，包括基础模型、LoRA、图片尺寸等
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import json

from dependencies import get_db
import crud

router = APIRouter()

@router.get("/frontend-config", summary="获取前台配置")
async def get_frontend_config(db: Session = Depends(get_db)):
    """获取前台所需的所有配置"""
    try:
        # 1. 获取基础模型配置
        available_models = crud.get_available_base_models(db)
        base_model_order_config = crud.get_system_config(db, "image_gen_base_model_order")
        configured_order = base_model_order_config.value.split(",") if base_model_order_config else []
        
        # 按配置排序重新排列模型
        final_order = []
        for model_name in configured_order:
            if any(m.name == model_name and m.is_available for m in available_models):
                final_order.append(model_name)
        
        # 添加未配置但可用的模型
        for model in available_models:
            if model.name not in final_order:
                final_order.append(model.name)
        
        # 构建模型列表
        models_list = []
        for model_name in final_order:
            model = next((m for m in available_models if m.name == model_name), None)
            if model:
                models_list.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "model_type": model.model_type,
                    "description": model.description,
                    "available": model.is_available,
                    "sort_order": model.sort_order
                })
        
        # 2. 获取LoRA配置
        loras = crud.get_loras(db, skip=0, limit=100)
        lora_order_config = crud.get_system_config(db, "image_gen_lora_order")
        lora_order = {}
        if lora_order_config and lora_order_config.value:
            try:
                lora_order = json.loads(lora_order_config.value)
            except:
                lora_order = {}
        
        # 构建LoRA列表
        loras_list = []
        for lora in loras:
            loras_list.append({
                "name": lora.name,
                "display_name": lora.display_name,
                "base_model": lora.base_model,
                "description": lora.description,
                "file_size": lora.file_size,
                "created_at": lora.created_at.isoformat() if lora.created_at else None
            })
        
        # 3. 获取图片尺寸配置
        default_size_config = crud.get_system_config(db, "image_gen_default_size")
        default_size = default_size_config.value.split(",") if default_size_config else ["1024", "1024"]
        
        size_ratios_config = crud.get_system_config(db, "image_gen_size_ratios")
        size_ratios = size_ratios_config.value.split(",") if size_ratios_config else ["1:1", "4:3", "3:4", "16:9", "9:16"]
        
        return {
            "models": {
                "list": models_list,
                "order": final_order,
                "count": len(models_list)
            },
            "loras": {
                "list": loras_list,
                "order": lora_order,
                "count": len(loras_list)
            },
            "image_sizes": {
                "default": {
                    "width": int(default_size[0]) if len(default_size) > 0 else 1024,
                    "height": int(default_size[1]) if len(default_size) > 1 else 1024
                },
                "ratios": size_ratios
            },
            "config_source": "admin_backend",
            "timestamp": "2025-09-17T20:30:00.000000"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取前台配置失败: {str(e)}")

@router.get("/frontend-config/models", summary="获取前台模型配置")
async def get_frontend_models_config(db: Session = Depends(get_db)):
    """获取前台模型配置"""
    try:
        # 获取可用模型
        available_models = crud.get_available_base_models(db)
        base_model_order_config = crud.get_system_config(db, "image_gen_base_model_order")
        configured_order = base_model_order_config.value.split(",") if base_model_order_config else []
        
        # 按配置排序
        final_order = []
        for model_name in configured_order:
            if any(m.name == model_name and m.is_available for m in available_models):
                final_order.append(model_name)
        
        for model in available_models:
            if model.name not in final_order:
                final_order.append(model.name)
        
        # 构建模型列表
        models_list = []
        for model_name in final_order:
            model = next((m for m in available_models if m.name == model_name), None)
            if model:
                models_list.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "model_type": model.model_type,
                    "description": model.description,
                    "available": model.is_available,
                    "sort_order": model.sort_order
                })
        
        return {
            "models": models_list,
            "order": final_order,
            "config_source": "admin_backend",
            "timestamp": "2025-09-17T20:30:00.000000"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型配置失败: {str(e)}")

@router.get("/frontend-config/loras", summary="获取前台LoRA配置")
async def get_frontend_loras_config(
    model: Optional[str] = Query(None, description="基础模型过滤"),
    db: Session = Depends(get_db)
):
    """获取前台LoRA配置"""
    try:
        # 获取LoRA列表
        loras = crud.get_loras(db, skip=0, limit=100)
        
        # 如果指定了模型，过滤LoRA
        if model:
            loras = [lora for lora in loras if lora.base_model == model]
        
        # 构建LoRA列表
        loras_list = []
        for lora in loras:
            loras_list.append({
                "name": lora.name,
                "display_name": lora.display_name,
                "base_model": lora.base_model,
                "description": lora.description,
                "file_size": lora.file_size,
                "created_at": lora.created_at.isoformat() if lora.created_at else None
            })
        
        return {
            "loras": loras_list,
            "model": model,
            "count": len(loras_list),
            "config_source": "admin_backend",
            "timestamp": "2025-09-17T20:30:00.000000"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取LoRA配置失败: {str(e)}")

@router.get("/frontend-config/image-sizes", summary="获取前台图片尺寸配置")
async def get_frontend_image_sizes_config(db: Session = Depends(get_db)):
    """获取前台图片尺寸配置"""
    try:
        # 获取默认尺寸
        default_size_config = crud.get_system_config(db, "image_gen_default_size")
        default_size = default_size_config.value.split(",") if default_size_config else ["1024", "1024"]
        
        # 获取支持的尺寸比例
        size_ratios_config = crud.get_system_config(db, "image_gen_size_ratios")
        size_ratios = size_ratios_config.value.split(",") if size_ratios_config else ["1:1", "4:3", "3:4", "16:9", "9:16"]
        
        return {
            "default": {
                "width": int(default_size[0]) if len(default_size) > 0 else 1024,
                "height": int(default_size[1]) if len(default_size) > 1 else 1024
            },
            "ratios": size_ratios,
            "config_source": "admin_backend",
            "timestamp": "2025-09-17T20:30:00.000000"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片尺寸配置失败: {str(e)}")
