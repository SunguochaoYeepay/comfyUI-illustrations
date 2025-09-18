#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为基础模型和LoRA添加code字段
"""

import sqlite3
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models

def migrate_database():
    """执行数据库迁移"""
    print("🔄 开始数据库迁移：添加code字段...")
    
    db = SessionLocal()
    try:
        # 检查是否已经存在code字段
        cursor = db.connection().connection.cursor()
        
        # 检查base_models表是否有code字段
        cursor.execute("PRAGMA table_info(base_models)")
        base_model_columns = [column[1] for column in cursor.fetchall()]
        
        if 'code' not in base_model_columns:
            print("📝 为base_models表添加code字段...")
            cursor.execute("ALTER TABLE base_models ADD COLUMN code VARCHAR(100)")
            cursor.execute("CREATE UNIQUE INDEX ix_base_models_code ON base_models (code)")
            print("✅ base_models表code字段添加完成")
        else:
            print("ℹ️ base_models表已存在code字段")
        
        # 检查loras表是否有code字段
        cursor.execute("PRAGMA table_info(loras)")
        lora_columns = [column[1] for column in cursor.fetchall()]
        
        if 'code' not in lora_columns:
            print("📝 为loras表添加code字段...")
            cursor.execute("ALTER TABLE loras ADD COLUMN code VARCHAR(255)")
            cursor.execute("CREATE UNIQUE INDEX ix_loras_code ON loras (code)")
            print("✅ loras表code字段添加完成")
        else:
            print("ℹ️ loras表已存在code字段")
        
        db.commit()
        
        # 为现有数据填充code字段
        print("🔄 为现有数据填充code字段...")
        
        # 为基础模型填充code字段
        base_models = db.query(models.BaseModel).all()
        for model in base_models:
            if not model.code:
                # 使用name作为code的初始值
                model.code = model.name
                print(f"📝 设置基础模型code: {model.name} -> {model.code}")
        
        # 为LoRA填充code字段
        loras = db.query(models.Lora).all()
        for lora in loras:
            if not lora.code:
                # 使用name作为code的初始值
                lora.code = lora.name
                print(f"📝 设置LoRA code: {lora.name} -> {lora.code}")
        
        db.commit()
        print("✅ 现有数据code字段填充完成")
        
        print("🎉 数据库迁移完成！")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()
