#!/usr/bin/env python3
"""
修复数据库中的图片路径，将反斜杠替换为正斜杠
"""

import sqlite3
from pathlib import Path

def fix_image_paths():
    """修复数据库中的图片路径"""
    print("开始修复图片路径...")
    
    try:
        # 连接数据库
        conn = sqlite3.connect('admin.db')
        cursor = conn.cursor()
        
        # 查看当前路径
        cursor.execute('SELECT id, code, preview_image_path FROM loras WHERE preview_image_path IS NOT NULL')
        current_paths = cursor.fetchall()
        
        print("修复前的路径:")
        for row in current_paths:
            print(f"ID: {row[0]}, Code: {row[1]}, Path: {row[2]}")
        
        # 更新路径，将反斜杠替换为正斜杠
        cursor.execute('UPDATE loras SET preview_image_path = REPLACE(preview_image_path, "\\\\", "/") WHERE preview_image_path IS NOT NULL')
        updated_count = cursor.rowcount
        
        # 提交更改
        conn.commit()
        
        # 查看修复后的路径
        cursor.execute('SELECT id, code, preview_image_path FROM loras WHERE preview_image_path IS NOT NULL')
        fixed_paths = cursor.fetchall()
        
        print(f"\n修复了 {updated_count} 条记录")
        print("修复后的路径:")
        for row in fixed_paths:
            print(f"ID: {row[0]}, Code: {row[1]}, Path: {row[2]}")
        
        conn.close()
        print("✅ 图片路径修复完成")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_image_paths()
    if success:
        print("操作完成")
    else:
        print("操作失败")
