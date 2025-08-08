#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试URL构建问题
"""

import sqlite3
from pathlib import Path

def debug_url_building():
    """调试URL构建问题"""
    conn = sqlite3.connect('back/tasks.db')
    cursor = conn.cursor()
    
    # 查询放大任务
    cursor.execute("""
        SELECT id, result_path, reference_image_path 
        FROM tasks 
        WHERE task_type='upscale' 
        ORDER BY created_at DESC 
        LIMIT 3
    """)
    
    tasks = cursor.fetchall()
    
    print("=== URL构建调试 ===")
    for task in tasks:
        task_id, result_path, reference_image_path = task
        print(f"\n任务ID: {task_id}")
        print(f"结果路径: {result_path}")
        print(f"参考图片路径: {reference_image_path}")
        
        if result_path:
            # 模拟database_manager.py中的逻辑
            image_path = Path(result_path)
            filename = image_path.name
            url = f"/api/upscale/image/{task_id}/{filename}"
            print(f"提取的文件名: {filename}")
            print(f"构建的URL: {url}")
            
            # 检查文件是否存在
            task_output_dir = Path("back/outputs") / task_id
            image_file = task_output_dir / filename
            print(f"文件路径: {image_file}")
            print(f"文件是否存在: {image_file.exists()}")
            
            if task_output_dir.exists():
                files = list(task_output_dir.glob("*"))
                print(f"目录中的文件: {[f.name for f in files]}")
        
        print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    debug_url_building()
