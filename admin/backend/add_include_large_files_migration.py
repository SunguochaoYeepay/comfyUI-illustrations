#!/usr/bin/env python3
"""
数据库迁移：添加 include_large_files 字段到 backup_schedules 表
"""

from database import engine
from sqlalchemy import text

def migrate():
    """执行迁移"""
    print("🔄 开始迁移：添加 include_large_files 字段到 backup_schedules 表...")
    
    with engine.connect() as conn:
        try:
            # 检查列是否已存在
            result = conn.execute(text("PRAGMA table_info(backup_schedules)"))
            columns = [col[1] for col in result.fetchall()]
            
            if 'include_large_files' in columns:
                print("✅ include_large_files 列已存在，跳过迁移")
                return
            
            # 添加新列
            conn.execute(text('ALTER TABLE backup_schedules ADD COLUMN include_large_files BOOLEAN DEFAULT 0'))
            conn.commit()
            print("✅ 成功添加 include_large_files 列到 backup_schedules 表")
            
            # 验证迁移结果
            result = conn.execute(text("PRAGMA table_info(backup_schedules)"))
            columns = result.fetchall()
            print("📋 当前 backup_schedules 表结构:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - 默认值: {col[4]}")
                
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            raise

if __name__ == "__main__":
    migrate()
