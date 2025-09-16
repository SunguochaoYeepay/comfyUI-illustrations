#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化LoRA数据
根据主服务的LoRA目录扫描并初始化LoRA数据
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

def init_loras():
    """初始化LoRA数据"""
    print("🚀 LoRA初始化脚本")
    print("=" * 50)
    
    # 连接数据库
    conn = sqlite3.connect('../admin.db')
    cursor = conn.cursor()
    
    try:
        # 清空现有LoRA数据
        cursor.execute("DELETE FROM loras")
        print("🗑️ 已清空现有LoRA数据")
        
        # 主服务的LoRA目录路径
        lora_dirs = [
            "E:/AI-Image/ComfyUI-aki-v1.4/models/loras",
            "E:/AI-Image/ComfyUI-aki-v1.4/models/loras/flux",
            "E:/AI-Image/ComfyUI-aki-v1.4/models/loras/qwen",
            "E:/AI-Image/ComfyUI-aki-v1.4/models/loras/wan"
        ]
        
        lora_count = 0
        
        for lora_dir in lora_dirs:
            lora_path = Path(lora_dir)
            if not lora_path.exists():
                print(f"⚠️ LoRA目录不存在: {lora_dir}")
                continue
                
            print(f"\n📁 扫描目录: {lora_dir}")
            
            # 扫描.safetensors文件
            for file_path in lora_path.glob("*.safetensors"):
                lora_name = file_path.name
                file_size = file_path.stat().st_size
                
                # 根据文件名和目录判断基础模型
                base_model = determine_base_model(lora_name, lora_dir)
                
                # 生成显示名称
                display_name = generate_display_name(lora_name)
                
                # 生成描述
                description = generate_description(lora_name, base_model)
                
                # 插入数据库
                cursor.execute("""
                    INSERT INTO loras (
                        name, display_name, base_model, description, 
                        file_path, file_size, is_available, is_managed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lora_name,
                    display_name,
                    base_model,
                    description,
                    str(file_path),
                    file_size,
                    1,  # is_available
                    0   # is_managed (未管理状态)
                ))
                
                lora_count += 1
                print(f"  ✅ {lora_name} -> {base_model}")
        
        conn.commit()
        print(f"\n🎉 LoRA初始化完成！共扫描到 {lora_count} 个LoRA文件")
        
        # 显示统计信息
        cursor.execute("SELECT base_model, COUNT(*) FROM loras GROUP BY base_model")
        stats = cursor.fetchall()
        print("\n📊 按基础模型统计:")
        for base_model, count in stats:
            print(f"  - {base_model}: {count} 个")
            
    except Exception as e:
        print(f"❌ LoRA初始化失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def determine_base_model(lora_name, lora_dir):
    """根据LoRA文件名和目录确定基础模型"""
    lora_name_lower = lora_name.lower()
    dir_name = Path(lora_dir).name.lower()
    
    # 根据目录名判断
    if 'flux' in dir_name:
        return 'flux-dev'
    elif 'qwen' in dir_name:
        return 'qwen-image'
    elif 'wan' in dir_name:
        return 'wan2.2-video'
    
    # 根据文件名判断
    if any(keyword in lora_name_lower for keyword in ['flux', 'kontext', 'sdxl']):
        return 'flux-dev'
    elif any(keyword in lora_name_lower for keyword in ['qwen', '千问', 'qwen2']):
        return 'qwen-image'
    elif any(keyword in lora_name_lower for keyword in ['wan', 'video', '视频']):
        return 'wan2.2-video'
    elif any(keyword in lora_name_lower for keyword in ['gemini', 'banana']):
        return 'gemini-image'
    else:
        # 默认使用Flux
        return 'flux-dev'

def generate_display_name(lora_name):
    """生成显示名称"""
    # 移除.safetensors扩展名
    name = lora_name.replace('.safetensors', '')
    
    # 替换下划线和连字符为空格
    name = name.replace('_', ' ').replace('-', ' ')
    
    # 首字母大写
    name = name.title()
    
    return name

def generate_description(lora_name, base_model):
    """生成描述"""
    base_model_names = {
        'flux-dev': 'Flux Kontext',
        'qwen-image': 'Qwen',
        'wan2.2-video': 'Wan2.2 视频',
        'gemini-image': 'Nano Banana'
    }
    
    base_display = base_model_names.get(base_model, base_model)
    return f"适用于 {base_display} 模型的LoRA文件"

if __name__ == "__main__":
    init_loras()
