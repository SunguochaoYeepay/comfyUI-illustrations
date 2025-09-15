#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化基础模型配置脚本
将主工程的基础模型配置导入到管理后台数据库
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
import crud
from schemas import base_model

def init_base_models():
    """初始化基础模型配置"""
    
    # 创建数据库表
    models.Base.metadata.create_all(bind=engine)
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 检查是否已有数据
        existing_models = crud.get_base_models(db, skip=0, limit=100)
        if existing_models:
            print(f"数据库中已有 {len(existing_models)} 个基础模型，跳过初始化")
            return
        
        # 主工程的基础模型配置
        base_models_data = [
            {
                "name": "flux1-dev",
                "display_name": "Flux Kontext",
                "model_type": "flux",
                "description": "Flux Kontext开发版本，支持高质量图像生成",
                "unet_file": "flux1-dev-kontext_fp8_scaled.safetensors",
                "clip_file": "clip_l.safetensors",
                "vae_file": "ae.safetensors",
                "template_path": None,  # 工作流独立管理
                "is_available": True,
                "is_default": False,
                "sort_order": 1
            },
            {
                "name": "qwen-image",
                "display_name": "Qwen",
                "model_type": "qwen",
                "description": "千问图像模型，支持单图生成和多图融合",
                "unet_file": "qwen_image_fp8_e4m3fn.safetensors",
                "clip_file": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                "vae_file": "qwen_image_vae.safetensors",
                "template_path": None,  # 工作流独立管理
                "is_available": True,
                "is_default": True,  # 设为默认模型
                "sort_order": 2
            },
            {
                "name": "wan2.2-video",
                "display_name": "Wan2.2 视频",
                "model_type": "wan",
                "description": "Wan2.2图像到视频模型，支持高质量视频生成",
                "unet_file": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
                "clip_file": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "vae_file": "wan_2.1_vae.safetensors",
                "template_path": None,  # 工作流独立管理
                "is_available": True,
                "is_default": False,
                "sort_order": 3
            },
            {
                "name": "flux1",
                "display_name": "Flux1基础模型",
                "model_type": "flux1",
                "description": "Flux1基础模型，支持多种工作流，可配置不同LoRA，输出高质量图像",
                "unet_file": "FLUX.1-FP16-dev.sft",
                "clip_file": "clip_l.safetensors",
                "vae_file": "ae.safetensors",
                "template_path": None,  # 工作流独立管理
                "is_available": True,
                "is_default": False,
                "sort_order": 4
            },
            {
                "name": "gemini-image",
                "display_name": "Nano Banana",
                "model_type": "gemini",
                "description": "Google Gemin图像编辑&融合，支持无图、1图、2图的智能合成",
                "unet_file": "",
                "clip_file": "",
                "vae_file": "",
                "template_path": None,  # 工作流独立管理
                "is_available": True,
                "is_default": False,
                "sort_order": 5
            }
        ]
        
        print("开始初始化基础模型配置...")
        
        # 批量创建基础模型
        for model_data in base_models_data:
            try:
                # 创建基础模型对象
                base_model_create = base_model.BaseModelCreate(**model_data)
                
                # 保存到数据库
                created_model = crud.create_base_model(db=db, base_model=base_model_create)
                print(f"✅ 创建基础模型: {created_model.display_name} ({created_model.name})")
                
            except Exception as e:
                print(f"❌ 创建基础模型失败 {model_data['name']}: {e}")
        
        print(f"🎉 基础模型初始化完成！共创建 {len(base_models_data)} 个模型")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

def show_models():
    """显示当前数据库中的基础模型"""
    db = SessionLocal()
    try:
        models = crud.get_base_models(db, skip=0, limit=100)
        if models:
            print(f"\n📋 当前数据库中的基础模型 ({len(models)} 个):")
            for model in models:
                status = "✅ 可用" if model.is_available else "❌ 不可用"
                default = " (默认)" if model.is_default else ""
                print(f"  - {model.display_name} ({model.name}) - {model.model_type} - {status}{default}")
        else:
            print("📋 数据库中没有基础模型")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 基础模型初始化脚本")
    print("=" * 50)
    
    # 显示当前模型
    show_models()
    
    # 询问是否初始化
    response = input("\n是否要初始化基础模型配置？(y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        init_base_models()
        print("\n" + "=" * 50)
        show_models()
    else:
        print("取消初始化")
