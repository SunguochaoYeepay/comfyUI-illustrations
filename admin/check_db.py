#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import sqlite3

def check_database():
    conn = sqlite3.connect('admin.db')
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("数据库中的表:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 检查每个表的结构和数据
    for table in tables:
        table_name = table[0]
        print(f"\n=== {table_name} 表 ===")
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("表结构:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 获取数据
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"数据行数: {count}")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            print("前5行数据:")
            for row in rows:
                print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
