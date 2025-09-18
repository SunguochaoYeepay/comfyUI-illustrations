#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置同步API路由
提供配置查询API、支持批量配置获取、配置变更通知
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from dependencies import get_db
import crud
from schemas import system_config

router = APIRouter()


@router.get("/health", summary="配置服务健康检查")
async def health_check():
    """配置服务健康检查"""
    return {
        "status": "healthy",
        "service": "config-sync",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get("/models", summary="获取模型配置")
async def get_models_config(db: Session = Depends(get_db)):
    """获取模型配置"""
    try:
        # 获取所有基础模型
        base_models = crud.get_base_models(db, skip=0, limit=100)
        
        # 获取模型排序配置
        model_order_config = crud.get_system_config(db, "image_gen_base_model_order")
        model_order = model_order_config.value.split(",") if model_order_config else []
        
        # 构建模型列表
        models = []
        for model in base_models:
            models.append({
                "code": model.code,
                "name": model.name,
                "display_name": model.display_name,
                "model_type": model.model_type,
                "available": model.is_available,
                "sort_order": model_order.index(model.name) + 1 if model.name in model_order else 999,
                "description": model.description,
                "unet_file": model.unet_file,
                "clip_file": model.clip_file,
                "vae_file": model.vae_file,
                # template_path 已移除，完全数据库化
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None
            })
        
        # 按排序顺序排序
        models.sort(key=lambda x: x["sort_order"])
        
        return {
            "models": models,
            "config_source": "backend",
            "last_updated": datetime.now().isoformat(),
            "total_count": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型配置失败: {str(e)}")


@router.get("/loras", summary="获取LoRA配置")
async def get_loras_config(
    base_model: Optional[str] = Query(None, description="按基础模型过滤"),
    db: Session = Depends(get_db)
):
    """获取LoRA配置"""
    try:
        # 获取所有LoRA
        loras = crud.get_loras(db, skip=0, limit=100)
        
        # 获取LoRA排序配置
        lora_order_config = crud.get_system_config(db, "image_gen_lora_order")
        lora_order = {}
        if lora_order_config and lora_order_config.value:
            try:
                lora_order = json.loads(lora_order_config.value)
            except:
                lora_order = {}
        
        # 构建LoRA列表
        lora_list = []
        grouped_by_model = {}
        
        for lora in loras:
            # 按基础模型过滤
            if base_model and lora.base_model != base_model:
                continue
            
            lora_data = {
                "code": lora.code,
                "name": lora.name,
                "display_name": lora.display_name,
                "base_model": lora.base_model,
                "available": lora.is_available,
                "description": lora.description,
                "file_size": lora.file_size,
                "created_at": lora.created_at.isoformat() if lora.created_at else None,
                "updated_at": lora.updated_at.isoformat() if lora.updated_at else None
            }
            
            # 应用排序 - 优先使用code字段，如果没有则使用name字段
            lora_identifier = lora.code or lora.name
            if lora.base_model in lora_order and lora_identifier in lora_order[lora.base_model]:
                lora_data["sort_order"] = lora_order[lora.base_model].index(lora_identifier) + 1
            else:
                lora_data["sort_order"] = 999
            
            lora_list.append(lora_data)
            
            # 按模型分组
            if lora.base_model not in grouped_by_model:
                grouped_by_model[lora.base_model] = []
            grouped_by_model[lora.base_model].append(lora.name)
        
        # 按排序顺序排序
        lora_list.sort(key=lambda x: x["sort_order"])
        
        return {
            "loras": lora_list,
            "grouped_by_model": grouped_by_model,
            "config_source": "backend",
            "last_updated": datetime.now().isoformat(),
            "total_count": len(lora_list),
            "filtered_by_model": base_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取LoRA配置失败: {str(e)}")


@router.get("/workflows", summary="获取工作流配置")
async def get_workflows_config(
    base_model_type: Optional[str] = Query(None, description="按基础模型类型过滤"),
    workflow_type: Optional[str] = Query(None, description="按工作流类型过滤"),
    db: Session = Depends(get_db)
):
    """获取工作流配置"""
    try:
        # 获取所有工作流
        workflows = crud.get_workflows(db, skip=0, limit=100)
        
        # 构建工作流列表
        workflow_list = []
        for workflow in workflows:
            # 按基础模型类型过滤
            if base_model_type and workflow.base_model_type != base_model_type:
                continue
            
            # 按工作流类型过滤
            if workflow_type and workflow.base_model_type != workflow_type:
                continue
            
            workflow_data = {
                "id": workflow.id,
                "code": workflow.code,  # 不可变的系统标识符
                "name": workflow.name,  # 可变的显示名称
                "display_name": workflow.name,  # 使用name作为display_name
                "base_model_type": workflow.base_model_type,
                "workflow_type": workflow.base_model_type,  # 使用base_model_type作为workflow_type
                "workflow_json": workflow.workflow_json,
                "available": workflow.status == "enabled",  # 根据status判断是否可用
                "description": workflow.description,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
            }
            
            workflow_list.append(workflow_data)
        
        return {
            "workflows": workflow_list,
            "config_source": "backend",
            "last_updated": datetime.now().isoformat(),
            "total_count": len(workflow_list),
            "filtered_by_model": base_model_type,
            "filtered_by_type": workflow_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流配置失败: {str(e)}")


@router.get("/image-gen", summary="获取生图配置")
async def get_image_gen_config(db: Session = Depends(get_db)):
    """获取生图配置"""
    try:
        # 获取基础模型排序配置
        base_model_order_config = crud.get_system_config(db, "image_gen_base_model_order")
        base_model_order = base_model_order_config.value.split(",") if base_model_order_config else []
        
        # 获取LoRA排序配置
        lora_order_config = crud.get_system_config(db, "image_gen_lora_order")
        lora_order = {}
        if lora_order_config and lora_order_config.value:
            try:
                lora_order = json.loads(lora_order_config.value)
            except:
                lora_order = {}
        
        # 获取默认尺寸配置
        default_size_config = crud.get_system_config(db, "image_gen_default_size")
        default_size = default_size_config.value.split(",") if default_size_config else ["1024", "1024"]
        
        # 获取支持的尺寸比例
        size_ratios_config = crud.get_system_config(db, "image_gen_size_ratios")
        size_ratios = size_ratios_config.value.split(",") if size_ratios_config else ["1:1", "4:3", "3:4", "16:9", "9:16"]
        
        # 获取默认步数配置
        default_steps_config = crud.get_system_config(db, "image_gen_default_steps")
        default_steps = int(default_steps_config.value) if default_steps_config else 20
        
        # 获取默认数量配置
        default_count_config = crud.get_system_config(db, "image_gen_default_count")
        default_count = int(default_count_config.value) if default_count_config else 1
        
        return {
            "base_model_order": base_model_order,
            "lora_order": lora_order,
            "default_size": {
                "width": int(default_size[0]) if len(default_size) > 0 else 1024,
                "height": int(default_size[1]) if len(default_size) > 1 else 1024
            },
            "size_ratios": size_ratios,
            "default_steps": default_steps,
            "default_count": default_count,
            "config_source": "backend",
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取生图配置失败: {str(e)}")


@router.get("/all", summary="获取所有配置")
async def get_all_configs(db: Session = Depends(get_db)):
    """获取所有配置"""
    try:
        # 获取各种配置
        models_config = await get_models_config(db)
        loras_config = await get_loras_config(db=db)
        workflows_config = await get_workflows_config(db=db)
        image_gen_config = await get_image_gen_config(db)
        
        return {
            "models": models_config,
            "loras": loras_config,
            "workflows": workflows_config,
            "image_gen": image_gen_config,
            "config_source": "backend",
            "last_updated": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取所有配置失败: {str(e)}")


@router.get("/config-status", summary="获取配置状态")
async def get_config_status(db: Session = Depends(get_db)):
    """获取配置状态信息"""
    try:
        # 统计各种配置的数量
        models_count = len(crud.get_base_models(db, skip=0, limit=1000))
        loras_count = len(crud.get_loras(db, skip=0, limit=1000))
        workflows_count = len(crud.get_workflows(db, skip=0, limit=1000))
        
        # 获取系统配置数量
        system_configs = crud.get_system_configs(db, skip=0, limit=1000)
        system_config_count = len(system_configs)
        
        # 获取最后更新时间
        last_updated = None
        if system_configs:
            last_updated = max(
                config.updated_at for config in system_configs 
                if config.updated_at
            ).isoformat()
        
        return {
            "status": "healthy",
            "config_counts": {
                "models": models_count,
                "loras": loras_count,
                "workflows": workflows_count,
                "system_configs": system_config_count
            },
            "last_updated": last_updated,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置状态失败: {str(e)}")


@router.get("/config-version", summary="获取配置版本信息")
async def get_config_version():
    """获取配置版本信息"""
    return {
        "version": "1.0.0",
        "api_version": "1.0.0",
        "supported_formats": ["json"],
        "endpoints": [
            "/health",
            "/models",
            "/loras",
            "/workflows", 
            "/image-gen",
            "/all",
            "/config-status",
            "/config-version"
        ],
        "timestamp": datetime.now().isoformat()
    }
