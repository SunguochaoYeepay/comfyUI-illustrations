import sqlite3
import shutil
from pathlib import Path
import requests
import json

def manual_fix_tasks():
    """手动修复任务的结果文件"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    # 获取需要修复的任务
    task_data = [
        ('9f6bd6fc-345a-4a5d-bd56-a86f7dc0ccbd', '158050ad-e463-4511-beb4-bef87e5718af'),
        ('91aa4654-5345-476b-bdb0-4b9fb95ffd2e', 'a325e568-6463-42e4-b6ff-1b22d5be32a8')
    ]
    
    comfyui_url = "http://127.0.0.1:8188"
    comfyui_output_dir = Path("D:/AI-Image/ComfyUI-aki-v1.6/ComfyUI/output")
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    for task_id, prompt_id in task_data:
        print(f"\n处理任务 {task_id}")
        print(f"Prompt ID: {prompt_id}")
        
        try:
            # 从ComfyUI获取历史记录
            response = requests.get(f"{comfyui_url}/history/{prompt_id}")
            if response.status_code == 200:
                history = response.json()
                print(f"历史记录获取成功")
                
                if prompt_id in history:
                    task_info = history[prompt_id]
                    print(f"找到任务信息")
                    
                    if "outputs" in task_info:
                        outputs = task_info["outputs"]
                        print(f"输出节点: {list(outputs.keys())}")
                        
                        for node_id, output in outputs.items():
                            print(f"  节点 {node_id}: {list(output.keys())}")
                            if "images" in output:
                                for i, image_info in enumerate(output["images"]):
                                    filename = image_info['filename']
                                    print(f"    图像 {i}: {filename}")
                                    
                                    # 检查源文件是否存在
                                    source_path = comfyui_output_dir / filename
                                    print(f"    源文件路径: {source_path}")
                                    print(f"    源文件存在: {source_path.exists()}")
                                    
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
                                        
                                        print(f"    ✅ 已复制文件并更新数据库: {result_path}")
                                        break
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
    
    # 检查outputs目录
    print("\n检查outputs目录:")
    if outputs_dir.exists():
        files = list(outputs_dir.glob("*"))
        print(f"文件列表: {[f.name for f in files]}")
    else:
        print("outputs目录不存在")

if __name__ == '__main__':
    manual_fix_tasks()