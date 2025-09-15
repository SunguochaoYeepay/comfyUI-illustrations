#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动执行数据库迁移
"""

import sqlite3

def manual_migration():
    conn = sqlite3.connect('admin.db')
    cursor = conn.cursor()
    
    try:
        # 检查表结构
        cursor.execute("PRAGMA table_info(base_models)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"当前base_models表字段: {columns}")
        
        # 添加新字段
        new_columns = [
            "ALTER TABLE base_models ADD COLUMN display_name VARCHAR(200)",
            "ALTER TABLE base_models ADD COLUMN model_type VARCHAR(50)",
            "ALTER TABLE base_models ADD COLUMN template_path VARCHAR(500)",
            "ALTER TABLE base_models ADD COLUMN is_available BOOLEAN DEFAULT 0",
            "ALTER TABLE base_models ADD COLUMN is_default BOOLEAN DEFAULT 0",
            "ALTER TABLE base_models ADD COLUMN sort_order INTEGER DEFAULT 0"
        ]
        
        for sql in new_columns:
            try:
                cursor.execute(sql)
                print(f"✅ 执行成功: {sql}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️ 字段已存在: {sql}")
                else:
                    print(f"❌ 执行失败: {sql} - {e}")
        
        # 重命名字段
        rename_operations = [
            ("unet_path", "unet_file"),
            ("clip_path", "clip_file"),
            ("vae_path", "vae_file")
        ]
        
        for old_name, new_name in rename_operations:
            if old_name in columns and new_name not in columns:
                try:
                    # SQLite不支持直接重命名，需要创建新表
                    cursor.execute(f"ALTER TABLE base_models RENAME COLUMN {old_name} TO {new_name}")
                    print(f"✅ 重命名字段: {old_name} -> {new_name}")
                except sqlite3.OperationalError as e:
                    print(f"❌ 重命名字段失败: {old_name} -> {new_name} - {e}")
            else:
                print(f"⚠️ 跳过重命名: {old_name} -> {new_name}")
        
        conn.commit()
        
        # 检查最终表结构
        cursor.execute("PRAGMA table_info(base_models)")
        final_columns = cursor.fetchall()
        print("\n最终base_models表结构:")
        for col in final_columns:
            print(f"  - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    manual_migration()
