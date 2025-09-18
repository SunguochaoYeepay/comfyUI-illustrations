#!/usr/bin/env python3
"""
数据库迁移脚本：为LoRA表添加category字段
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
    print("开始执行LoRA分类字段迁移...")
    
    try:
        # 检查数据库文件是否存在
        db_path = project_root / "admin.db"
        if not db_path.exists():
            print(f"❌ 数据库文件不存在: {db_path}")
            return False
        
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查category字段是否已存在
        cursor.execute("PRAGMA table_info(loras)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category' in columns:
            print("✅ category字段已存在，跳过迁移")
            conn.close()
            return True
        
        # 添加category字段
        print("正在添加category字段...")
        cursor.execute("ALTER TABLE loras ADD COLUMN category VARCHAR(50)")
        
        # 创建索引
        print("正在创建category字段索引...")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_loras_category ON loras(category)")
        
        # 提交更改
        conn.commit()
        conn.close()
        
        print("✅ LoRA分类字段迁移完成")
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        return False

def rollback_migration():
    """回滚迁移（删除category字段）"""
    print("开始回滚LoRA分类字段迁移...")
    
    try:
        db_path = project_root / "admin.db"
        if not db_path.exists():
            print(f"❌ 数据库文件不存在: {db_path}")
            return False
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查category字段是否存在
        cursor.execute("PRAGMA table_info(loras)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category' not in columns:
            print("✅ category字段不存在，无需回滚")
            conn.close()
            return True
        
        # SQLite不支持直接删除列，需要重建表
        print("正在回滚category字段...")
        
        # 1. 创建临时表（不包含category字段）
        cursor.execute("""
            CREATE TABLE loras_temp AS 
            SELECT id, code, name, display_name, base_model, description, 
                   file_path, file_size, is_available, is_managed, 
                   created_at, updated_at 
            FROM loras
        """)
        
        # 2. 删除原表
        cursor.execute("DROP TABLE loras")
        
        # 3. 重命名临时表
        cursor.execute("ALTER TABLE loras_temp RENAME TO loras")
        
        # 4. 重建索引
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_loras_code ON loras(code)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_loras_name ON loras(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_loras_base_model ON loras(base_model)")
        
        conn.commit()
        conn.close()
        
        print("✅ LoRA分类字段回滚完成")
        return True
        
    except Exception as e:
        print(f"❌ 回滚失败: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LoRA分类字段数据库迁移")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_migration()
    else:
        success = migrate_database()
    
    if success:
        print("操作完成")
        sys.exit(0)
    else:
        print("操作失败")
        sys.exit(1)
