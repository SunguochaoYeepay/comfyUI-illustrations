#!/usr/bin/env python3
"""
数据库迁移脚本：为LoRA表添加preview_image_path字段
"""

import os
import sys
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database import engine, Base
from models import Lora
from sqlalchemy import text

def migrate_database():
    """执行数据库迁移"""
    print("开始执行LoRA预览图片字段迁移...")
    
    try:
        # 检查数据库文件是否存在
        db_path = project_root / "admin.db"
        if not db_path.exists():
            print(f"❌ 数据库文件不存在: {db_path}")
            return False
        
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查preview_image_path字段是否已存在
        cursor.execute("PRAGMA table_info(loras)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'preview_image_path' in columns:
            print("✅ preview_image_path字段已存在，跳过迁移")
            conn.close()
            return True
        
        # 添加preview_image_path字段
        print("正在添加preview_image_path字段...")
        cursor.execute("ALTER TABLE loras ADD COLUMN preview_image_path VARCHAR(500)")
        
        conn.commit()
        conn.close()
        
        print("✅ LoRA预览图片字段迁移完成")
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    
    if success:
        print("操作完成")
        sys.exit(0)
    else:
        print("操作失败")
        sys.exit(1)
