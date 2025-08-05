import requests
import json
from pathlib import Path

def test_image_access():
    """测试图像访问功能"""
    base_url = "http://localhost:9000"
    
    # 测试的任务ID
    task_ids = ['9f6bd6fc-345a-4a5d-bd56-a86f7dc0ccbd', '91aa4654-5345-476b-bdb0-4b9fb95ffd2e']
    
    for task_id in task_ids:
        print(f"\n测试任务 {task_id}:")
        
        # 1. 检查任务状态
        try:
            response = requests.get(f"{base_url}/api/task/{task_id}")
            if response.status_code == 200:
                task_data = response.json()
                print(f"  任务状态: {task_data['status']}")
                print(f"  结果路径: {task_data.get('result_path', 'None')}")
                
                # 检查本地文件是否存在
                if task_data.get('result_path'):
                    local_path = Path(task_data['result_path'])
                    print(f"  本地文件存在: {local_path.exists()}")
            else:
                print(f"  获取任务状态失败: {response.status_code}")
        except Exception as e:
            print(f"  获取任务状态异常: {e}")
        
        # 2. 测试图像访问
        try:
            response = requests.get(f"{base_url}/api/image/{task_id}")
            print(f"  图像访问状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  图像大小: {len(response.content)} bytes")
                print(f"  内容类型: {response.headers.get('content-type', 'unknown')}")
            else:
                print(f"  图像访问失败: {response.text}")
        except Exception as e:
            print(f"  图像访问异常: {e}")
    
    # 3. 检查outputs目录
    print("\n检查outputs目录:")
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        files = list(outputs_dir.glob("*"))
        print(f"  文件列表: {[f.name for f in files]}")
        for file in files:
            if file.is_file():
                print(f"    {file.name}: {file.stat().st_size} bytes")
    else:
        print("  outputs目录不存在")

if __name__ == '__main__':
    test_image_access()