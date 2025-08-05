import sqlite3
import shutil
from pathlib import Path
import requests
import json

def fix_existing_tasks():
    """修复现有任务的结果路径"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    # 查找状态为completed但result_path为空的任务
    cursor.execute("SELECT id, prompt_id FROM tasks WHERE status = 'completed' AND (result_path IS NULL OR result_path = '')")
    tasks = cursor.fetchall()
    
    print(f"找到 {len(tasks)} 个需要修复的任务")
    
    comfyui_url = "http://127.0.0.1:8188"
    comfyui_output_dir = Path("D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output")
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    for task_id, prompt_id in tasks:
        print(f"\n处理任务 {task_id} (prompt_id: {prompt_id})")
        
        try:
            # 从ComfyUI获取历史记录
            response = requests.get(f"{comfyui_url}/history/{prompt_id}")
            if response.status_code == 200:
                history = response.json()
                
                if prompt_id in history:
                    task_info = history[prompt_id]
                    if "outputs" in task_info:
                        outputs = task_info["outputs"]
                        
                        for node_id, output in outputs.items():
                            if "images" in output:
                                image_info = output["images"][0]
                                filename = image_info['filename']
                                
                                print(f"  找到输出文件: {filename}")
                                
                                # 检查源文件是否存在
                                source_path = comfyui_output_dir / filename
                                if source_path.exists():
                                    # 复制到outputs目录
                                    dest_path = outputs_dir / filename
                                    shutil.copy2(source_path, dest_path)
                                    
                                    # 更新数据库
                                    result_path = f"outputs/{filename}"
                                    cursor.execute(
                                        "UPDATE tasks SET result_path = ? WHERE id = ?",
                                        (result_path, task_id)
                                    )
                                    conn.commit()
                                    
                                    print(f"  ✅ 已复制文件并更新数据库: {result_path}")
                                    break
                                else:
                                    print(f"  ❌ 源文件不存在: {source_path}")
                        else:
                            print(f"  ❌ 未找到图像输出")
                    else:
                        print(f"  ❌ 任务无输出")
                else:
                    print(f"  ❌ 历史记录中未找到任务")
            else:
                print(f"  ❌ 获取历史记录失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 处理异常: {e}")
    
    conn.close()
    print("\n修复完成！")

if __name__ == '__main__':
    fix_existing_tasks()