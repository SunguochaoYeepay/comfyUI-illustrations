#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗脚本：清洗code字段，移除中文和特殊字符
"""

import sqlite3
import re
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import BaseModel, Lora


def clean_code_string(text):
    """
    清洗字符串，生成符合规范的code
    - 移除中文字符
    - 移除特殊字符和空格
    - 转换为小写
    - 用下划线替换连字符
    """
    if not text:
        return ""
    
    # 移除中文字符
    text = re.sub(r'[\u4e00-\u9fff]', '', text)
    
    # 移除特殊字符，只保留字母、数字、下划线和连字符
    text = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    
    # 将连字符替换为下划线
    text = text.replace('-', '_')
    
    # 移除连续的下划线
    text = re.sub(r'_+', '_', text)
    
    # 移除开头和结尾的下划线
    text = text.strip('_')
    
    # 转换为小写
    text = text.lower()
    
    # 如果结果为空，使用默认值
    if not text:
        text = "unknown"
    
    return text


def generate_unique_code(base_code, existing_codes, prefix=""):
    """
    生成唯一的code，如果重复则添加数字后缀
    """
    if prefix:
        code = f"{prefix}_{base_code}"
    else:
        code = base_code
    
    if code not in existing_codes:
        return code
    
    # 如果重复，添加数字后缀
    counter = 1
    while f"{code}_{counter}" in existing_codes:
        counter += 1
    
    return f"{code}_{counter}"


def clean_database():
    """清洗数据库中的code字段"""
    print("🧹 开始清洗数据库code字段...")
    
    db = SessionLocal()
    try:
        # 获取所有现有的code值，用于检查重复
        existing_base_model_codes = set()
        existing_lora_codes = set()
        
        # 收集现有的code值
        base_models = db.query(BaseModel).all()
        for model in base_models:
            if model.code:
                existing_base_model_codes.add(model.code)
        
        loras = db.query(Lora).all()
        for lora in loras:
            if lora.code:
                existing_lora_codes.add(lora.code)
        
        print(f"📊 发现 {len(base_models)} 个基础模型，{len(loras)} 个LoRA")
        
        # 清洗基础模型的code字段
        print("🔧 清洗基础模型code字段...")
        for model in base_models:
            if model.code:
                # 从name字段生成新的code
                new_code = clean_code_string(model.name)
                new_code = generate_unique_code(new_code, existing_base_model_codes, "model")
                
                if new_code != model.code:
                    print(f"📝 基础模型: {model.name} -> {model.code} -> {new_code}")
                    model.code = new_code
                    existing_base_model_codes.add(new_code)
                else:
                    print(f"✅ 基础模型: {model.name} -> {model.code} (无需修改)")
        
        # 清洗LoRA的code字段
        print("🔧 清洗LoRA code字段...")
        for lora in loras:
            if lora.code:
                # 从name字段生成新的code
                new_code = clean_code_string(lora.name)
                new_code = generate_unique_code(new_code, existing_lora_codes, "lora")
                
                if new_code != lora.code:
                    print(f"📝 LoRA: {lora.name} -> {lora.code} -> {new_code}")
                    lora.code = new_code
                    existing_lora_codes.add(new_code)
                else:
                    print(f"✅ LoRA: {lora.name} -> {lora.code} (无需修改)")
        
        # 提交更改
        db.commit()
        print("✅ 数据库清洗完成！")
        
        # 显示清洗结果
        print("\n📋 清洗结果统计:")
        print(f"基础模型: {len(base_models)} 个")
        print(f"LoRA: {len(loras)} 个")
        
    except Exception as e:
        print(f"❌ 数据库清洗失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clean_database()
