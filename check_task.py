import sqlite3
import requests
import json
from pathlib import Path

def check_specific_tasks():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    # 查找特定任务
    task_ids = ['9f6bd6fc-345a-4a5d-bd56-a86f7dc0ccbd', '91aa4654-5345-476b-bdb0-4b9fb95ffd2e']
    
    # 首先查看所有completed任务的result_path状态
    cursor.execute("SELECT id, status, result_path FROM tasks WHERE status = 'completed'")
    completed_tasks = cursor.fetchall()
    print(f"所有completed任务:")
    for task in completed_tasks:
        print(f"  {task[0]}: status={task[1]}, result_path={task[2]}")
    
    for task_id in task_ids:
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            task_info = dict(zip(columns, result))
            print(f"\nTask {task_id}:")
            for key, value in task_info.items():
                print(f"  {key}: {value}")
            
            # 检查结果文件是否存在
            if task_info.get('result_path'):
                result_path = Path(task_info['result_path'])
                print(f"  Result file exists: {result_path.exists()}")
                if result_path.exists():
                    print(f"  File size: {result_path.stat().st_size} bytes")
        else:
            print(f"\nTask {task_id}: Not found")
    
    conn.close()
    
    # 检查outputs目录
    print("\nChecking outputs directory:")
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        files = list(outputs_dir.glob("*"))
        print(f"Files in outputs: {[f.name for f in files]}")
    else:
        print("Outputs directory does not exist")
    
    # 检查ComfyUI输出目录
    print("\nChecking ComfyUI output directory:")
    comfyui_output_dir = Path("D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output")
    if comfyui_output_dir.exists():
        files = list(comfyui_output_dir.glob("*.png"))[-5:]  # 最近5个PNG文件
        print(f"Recent PNG files in ComfyUI output: {[f.name for f in files]}")
    else:
        print("ComfyUI output directory not found")

if __name__ == '__main__':
    check_specific_tasks()