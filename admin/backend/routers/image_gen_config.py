#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生图配置管理API路由
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    """获取生图配置 - 智能过滤可用模型"""
    try:
        print("🔍 开始获取生图配置...")
        # 1. 获取所有可用模型
        print("🔍 获取可用模型...")
        available_models = crud.get_available_base_models(db)
        print(f"🔍 获取到{len(available_models)}个可用模型")
        
        # 2. 获取当前生图配置排序
        print("🔍 获取基础模型排序配置...")
        base_model_order_config = crud.get_system_config(db, "image_gen_base_model_order")
        if base_model_order_config and base_model_order_config.value:
            configured_order = str(base_model_order_config.value).split(",")
        else:
            configured_order = []
        print(f"🔍 配置的模型排序: {configured_order}")
        
        # 3. 智能合并：保留配置的排序，过滤掉不可用的模型
        final_order = []
        for model_name in configured_order:
            if any(m.name == model_name and m.is_available for m in available_models):
                final_order.append(model_name)
        
        # 4. 添加新可用但未配置的模型
        for model in available_models:
            if model.name not in final_order:
                final_order.append(model.name)
        
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
        if default_size_config and default_size_config.value:
            default_size = str(default_size_config.value).split(",")
        else:
            default_size = ["1024", "1024"]
        
        # 获取支持的尺寸比例配置
        size_ratios_config = crud.get_system_config(db, "image_gen_size_ratios")
        if size_ratios_config and size_ratios_config.value:
            try:
                # 尝试解析为JSON格式（新格式）
                size_ratios_data = json.loads(size_ratios_config.value)
                size_ratios = size_ratios_data
            except:
                # 降级到旧格式（逗号分隔的字符串）
                size_ratios_list = size_ratios_config.value.split(",")
                # 转换为新格式
                default_sizes = {
                    '1:1': {'width': 1024, 'height': 1024},
                    '4:3': {'width': 1024, 'height': 768},
                    '3:4': {'width': 768, 'height': 1024},
                    '16:9': {'width': 1024, 'height': 576},
                    '9:16': {'width': 576, 'height': 1024},
                    '21:9': {'width': 1024, 'height': 439},
                    '3:2': {'width': 1024, 'height': 683},
                    '2:3': {'width': 683, 'height': 1024}
                }
                size_ratios = []
                for ratio in size_ratios_list:
                    if ratio.strip():
                        default_size = default_sizes.get(ratio.strip(), {'width': 1024, 'height': 1024})
                        size_ratios.append({
                            'ratio': ratio.strip(),
                            'width': default_size['width'],
                            'height': default_size['height'],
                            'description': ''
                        })
        else:
            # 默认配置
            size_ratios = [
                {'ratio': '1:1', 'width': 1024, 'height': 1024, 'description': ''},
                {'ratio': '4:3', 'width': 1024, 'height': 768, 'description': ''},
                {'ratio': '3:4', 'width': 768, 'height': 1024, 'description': ''},
                {'ratio': '16:9', 'width': 1024, 'height': 576, 'description': ''},
                {'ratio': '9:16', 'width': 576, 'height': 1024, 'description': ''}
            ]
        
        # 确保default_size是列表格式
        if not isinstance(default_size, list):
            default_size = ["1024", "1024"]
        
        # 获取默认生图数量配置
        default_count_config = crud.get_system_config(db, "image_gen_default_count")
        default_count = int(default_count_config.value) if default_count_config else 1
        
        return {
            "base_model_order": final_order,
            "lora_order": lora_order,
            "default_size": {
                "width": int(default_size[0]) if len(default_size) > 0 else 1024,
                "height": int(default_size[1]) if len(default_size) > 1 else 1024
            },
            "size_ratios": size_ratios,
            "default_count": default_count
        }
    except Exception as e:
        import traceback
        error_detail = f"获取生图配置失败: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@router.put("/image-gen-config", summary="更新生图配置")
async def update_image_gen_config(
    config_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新生图配置 - 只允许配置可用模型"""
    try:
        # 更新基础模型排序 - 验证所有模型都是可用的
        if "base_model_order" in config_data:
            requested_models = config_data["base_model_order"]
            available_models = crud.get_available_base_models(db)
            available_names = [m.name for m in available_models]
            
            # 过滤掉不可用的模型
            valid_models = [name for name in requested_models if name in available_names]
            
            if len(valid_models) != len(requested_models):
                removed_models = set(requested_models) - set(valid_models)
                print(f"⚠️ 生图配置中移除了不可用模型: {removed_models}")
            
            base_model_order = ",".join(valid_models)
            config_update = system_config.SystemConfigUpdate(
                key="image_gen_base_model_order",
                value=base_model_order,
                description="基础模型排序配置，逗号分隔（仅包含可用模型）"
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
        
        # 更新支持的尺寸比例配置
        if "size_ratios" in config_data:
            size_ratios_data = config_data["size_ratios"]
            # 保存为JSON格式
            size_ratios_json = json.dumps(size_ratios_data, ensure_ascii=False)
            config_update = system_config.SystemConfigUpdate(
                key="image_gen_size_ratios",
                value=size_ratios_json,
                description="支持的图片比例配置，JSON格式，包含比例名称和像素尺寸"
            )
            crud.update_system_config(db, "image_gen_size_ratios", config_update)
        
        return {"message": "生图配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新生图配置失败: {str(e)}")

@router.get("/image-gen-config/base-models", summary="获取基础模型列表")
async def get_base_models_for_config(db: Session = Depends(get_db)):
    """获取基础模型列表用于配置排序 - 只返回可用模型"""
    try:
        # 只获取可用的基础模型
        available_models = crud.get_available_base_models(db)
        print(f"🔍 API获取到的可用模型数量: {len(available_models)}")
        for model in available_models:
            print(f"  - {model.name}: {model.display_name} (可用: {model.is_available})")
        
        # 获取当前排序配置
        base_model_order_config = crud.get_system_config(db, "image_gen_base_model_order")
        current_order = base_model_order_config.value.split(",") if base_model_order_config else []
        
        # 按配置排序重新排列模型
        final_order = []
        print(f"🔍 原始current_order: {current_order}")
        for model_name in current_order:
            if any(m.name == model_name and m.is_available for m in available_models):
                final_order.append(model_name)
                print(f"  ✅ 添加可用模型: {model_name}")
            else:
                print(f"  ❌ 跳过不可用模型: {model_name}")
        
        # 添加未配置但可用的模型
        for model in available_models:
            if model.name not in final_order:
                final_order.append(model.name)
                print(f"  ➕ 添加未配置但可用模型: {model.name}")
        
        print(f"🔍 最终final_order: {final_order}")
        
        # 构建模型列表（按最终排序）
        model_list = []
        for model_name in final_order:
            model = next((m for m in available_models if m.name == model_name), None)
            if model:
                model_list.append({
                    "code": model.code,
                    "name": model.name,
                    "display_name": model.display_name,
                    "model_type": model.model_type,
                    "description": model.description,
                    "available": model.is_available,
                    "unet_file": model.unet_file,
                    "clip_file": model.clip_file,
                    "vae_file": model.vae_file
                })
        
        return {
            "models": model_list,
            "current_order": final_order
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

