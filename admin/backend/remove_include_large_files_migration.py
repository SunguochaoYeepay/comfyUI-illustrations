#!/usr/bin/env python3
"""
数据库迁移：移除 backup_schedules 表中的 include_large_files 字段
"""

from database import engine
from sqlalchemy import text

def migrate():
    """执行迁移"""
    print("🔄 开始迁移：移除 backup_schedules 表的 include_large_files 字段...")
    
    with engine.connect() as conn:
        try:
            # 检查列是否存在
            result = conn.execute(text("PRAGMA table_info(backup_schedules)"))
            columns = [col[1] for col in result.fetchall()]
            
            if 'include_large_files' not in columns:
                print("✅ include_large_files 列不存在，跳过迁移")
                return
            
            # SQLite 不支持直接删除列，需要重建表
            print("📋 重建 backup_schedules 表...")
            
            # 创建新表结构
            conn.execute(text("""
                CREATE TABLE backup_schedules_new (
                    id INTEGER PRIMARY KEY,
                    schedule_name VARCHAR(255) NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    frequency VARCHAR(20) NOT NULL,
                    schedule_time VARCHAR(10) NOT NULL,
                    backup_type VARCHAR(50) NOT NULL,
                    retention_days INTEGER DEFAULT 30,
                    last_run DATETIME,
                    next_run DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 复制数据（排除 include_large_files 列）
            conn.execute(text("""
                INSERT INTO backup_schedules_new (
                    id, schedule_name, enabled, frequency, schedule_time, 
                    backup_type, retention_days, last_run, next_run, 
                    created_at, updated_at
                )
                SELECT 
                    id, schedule_name, enabled, frequency, schedule_time,
                    backup_type, retention_days, last_run, next_run,
                    created_at, updated_at
                FROM backup_schedules
            """))
            
            # 删除旧表，重命名新表
            conn.execute(text("DROP TABLE backup_schedules"))
            conn.execute(text("ALTER TABLE backup_schedules_new RENAME TO backup_schedules"))
            
            conn.commit()
            print("✅ 成功移除 include_large_files 列")
            
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
