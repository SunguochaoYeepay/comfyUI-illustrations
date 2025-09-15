#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化系统配置脚本
设置基础模型文件路径配置
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
import crud
from schemas import system_config

def init_system_config():
    """初始化系统配置"""
    
    # 创建数据库表
    models.Base.metadata.create_all(bind=engine)
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 系统配置数据
        configs_data = [
            {
                "key": "comfyui_models_dir",
                "value": "E:/AI-Image/ComfyUI-aki-v1.4/models",
                "description": "ComfyUI模型文件基础目录"
            },
            {
                "key": "comfyui_workflows_dir", 
                "value": "E:/AI-Image/ComfyUI-aki-v1.4/workflows",
                "description": "ComfyUI工作流文件基础目录"
            },
            {
                "key": "model_paths_flux",
                "value": "checkpoints,clip,vae",
                "description": "Flux模型文件子目录：UNet,CLIP,VAE"
            },
            {
                "key": "model_paths_qwen",
                "value": "diffusion_models,text_encoders,vae", 
                "description": "Qwen模型文件子目录：UNet,CLIP,VAE"
            },
            {
                "key": "model_paths_wan",
                "value": "diffusion_models,text_encoders,vae",
                "description": "Wan模型文件子目录：UNet,CLIP,VAE"
            },
            {
                "key": "model_paths_flux1",
                "value": "unet,clip,vae",
                "description": "Flux1模型文件子目录：UNet,CLIP,VAE"
            },
            {
                "key": "model_paths_gemini",
                "value": ",,",
                "description": "Gemini模型文件子目录：API模型无需本地文件"
            }
        ]
        
        print("开始初始化系统配置...")
        
        # 批量创建系统配置
        for config_data in configs_data:
            try:
                # 检查是否已存在
                existing = crud.get_system_config(db, config_data["key"])
                if existing:
                    print(f"⚠️ 配置已存在: {config_data['key']}")
                    continue
                
                # 创建配置对象
                config_create = system_config.SystemConfigCreate(**config_data)
                
                # 保存到数据库
                created_config = crud.create_system_config(db=db, config=config_create)
                print(f"✅ 创建系统配置: {created_config.key} = {created_config.value}")
                
            except Exception as e:
                print(f"❌ 创建系统配置失败 {config_data['key']}: {e}")
        
        print(f"🎉 系统配置初始化完成！共创建 {len(configs_data)} 个配置")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

def show_configs():
    """显示当前数据库中的系统配置"""
    db = SessionLocal()
    try:
        configs = crud.get_system_configs(db, skip=0, limit=100)
        if configs:
            print(f"\n📋 当前数据库中的系统配置 ({len(configs)} 个):")
            for config in configs:
                print(f"  - {config.key}: {config.value}")
                if config.description:
                    print(f"    {config.description}")
        else:
            print("📋 数据库中没有系统配置")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 系统配置初始化脚本")
    print("=" * 50)
    
    # 显示当前配置
    show_configs()
    
    # 询问是否初始化
    response = input("\n是否要初始化系统配置？(y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        init_system_config()
        print("\n" + "=" * 50)
        show_configs()
    else:
        print("取消初始化")
