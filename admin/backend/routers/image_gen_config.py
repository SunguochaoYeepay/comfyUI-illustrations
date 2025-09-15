#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生图配置管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import json

from dependencies import get_db
import crud
from schemas import system_config

router = APIRouter()

@router.get("/image-gen-config", summary="获取生图配置")
async def get_image_gen_config(db: Session = Depends(get_db)):
    """获取生图配置"""
    try:
        # 获取基础模型排序配置
        base_model_order_config = crud.get_system_config(db, "image_gen_base_model_order")
        base_model_order = base_model_order_config.value.split(",") if base_model_order_config else []
        
        # 获取LoRA排序配置
        lora_order_config = crud.get_system_config(db, "image_gen_lora_order")
        if lora_order_config and lora_order_config.value:
            try:
                lora_order = json.loads(lora_order_config.value)
            except:
                lora_order = {}
        else:
            lora_order = {}
        
        # 获取默认尺寸配置
        default_size_config = crud.get_system_config(db, "image_gen_default_size")
        default_size = default_size_config.value.split(",") if default_size_config else ["1024", "1024"]
        
        # 获取支持的尺寸比例
        size_ratios_config = crud.get_system_config(db, "image_gen_size_ratios")
        size_ratios = size_ratios_config.value.split(",") if size_ratios_config else ["1:1", "4:3", "3:4", "16:9", "9:16"]
        
        return {
            "base_model_order": base_model_order,
            "lora_order": lora_order,
            "default_size": {
                "width": int(default_size[0]) if len(default_size) > 0 else 1024,
                "height": int(default_size[1]) if len(default_size) > 1 else 1024
            },
            "size_ratios": size_ratios
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取生图配置失败: {str(e)}")

@router.put("/image-gen-config", summary="更新生图配置")
async def update_image_gen_config(
    config_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新生图配置"""
    try:
        # 更新基础模型排序
        if "base_model_order" in config_data:
            base_model_order = ",".join(config_data["base_model_order"])
            config_update = system_config.SystemConfigUpdate(
                key="image_gen_base_model_order",
                value=base_model_order,
                description="基础模型排序配置，逗号分隔"
            )
            crud.update_system_config(db, "image_gen_base_model_order", config_update)
        
        # 更新LoRA排序
        if "lora_order" in config_data:
            lora_order = json.dumps(config_data["lora_order"])
            config_update = system_config.SystemConfigUpdate(
                key="image_gen_lora_order",
                value=lora_order,
                description="LoRA排序配置：按基础模型分组的JSON对象"
            )
            crud.update_system_config(db, "image_gen_lora_order", config_update)
        
        # 更新默认尺寸
        if "default_size" in config_data:
            default_size = config_data["default_size"]
            size_value = f"{default_size['width']},{default_size['height']}"
            config_update = system_config.SystemConfigUpdate(
                key="image_gen_default_size",
                value=size_value,
                description="默认生图尺寸：宽度,高度"
            )
            crud.update_system_config(db, "image_gen_default_size", config_update)
        
        # 更新支持的尺寸比例
        if "size_ratios" in config_data:
            size_ratios = ",".join(config_data["size_ratios"])
            config_update = system_config.SystemConfigUpdate(
                key="image_gen_size_ratios",
                value=size_ratios,
                description="支持的图片比例，逗号分隔"
            )
            crud.update_system_config(db, "image_gen_size_ratios", config_update)
        
        return {"message": "生图配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新生图配置失败: {str(e)}")

@router.get("/image-gen-config/base-models", summary="获取基础模型列表")
async def get_base_models_for_config(db: Session = Depends(get_db)):
    """获取基础模型列表用于配置排序"""
    try:
        # 获取所有基础模型
        base_models = crud.get_base_models(db, skip=0, limit=100)
        
        # 获取当前排序配置
        base_model_order_config = crud.get_system_config(db, "image_gen_base_model_order")
        current_order = base_model_order_config.value.split(",") if base_model_order_config else []
        
        # 构建模型列表
        model_list = []
        for model in base_models:
            model_list.append({
                "name": model.name,
                "display_name": model.display_name,
                "description": model.description,
                "available": model.is_available
            })
        
        return {
            "models": model_list,
            "current_order": current_order
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取基础模型列表失败: {str(e)}")

@router.get("/image-gen-config/loras", summary="获取LoRA列表")
async def get_loras_for_config(db: Session = Depends(get_db)):
    """获取LoRA列表用于配置排序"""
    try:
        # 获取所有LoRA
        loras = crud.get_loras(db, skip=0, limit=100)
        
        # 获取当前排序配置
        lora_order_config = crud.get_system_config(db, "image_gen_lora_order")
        current_order = lora_order_config.value.split(",") if lora_order_config else ["name"]
        
        # 构建LoRA列表
        lora_list = []
        for lora in loras:
            lora_list.append({
                "name": lora.name,
                "display_name": lora.display_name,
                "base_model": lora.base_model,
                "description": lora.description,
                "file_size": lora.file_size,
                "created_at": lora.created_at.isoformat() if lora.created_at else None
            })
        
        return {
            "loras": lora_list,
            "current_order": current_order,
            "available_order_options": [
                {"key": "name", "label": "名称"},
                {"key": "base_model", "label": "基础模型"},
                {"key": "created_at", "label": "创建时间"},
                {"key": "file_size", "label": "文件大小"}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取LoRA列表失败: {str(e)}")
