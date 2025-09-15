#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建LoRA表
"""

import sqlite3

def create_lora_table():
    conn = sqlite3.connect('../admin.db')
    cursor = conn.cursor()
    
    try:
        # 创建LoRA表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE,
                display_name VARCHAR(255) NOT NULL,
                base_model VARCHAR(100) NOT NULL,
                description TEXT,
                file_path VARCHAR(500),
                file_size INTEGER,
                is_available BOOLEAN DEFAULT 1,
                is_managed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_loras_name ON loras(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_loras_base_model ON loras(base_model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_loras_is_available ON loras(is_available)")
        
        conn.commit()
        print("✅ LoRA表创建成功")
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(loras)")
        columns = cursor.fetchall()
        print("\nLoRA表结构:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ 创建LoRA表失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_lora_table()
