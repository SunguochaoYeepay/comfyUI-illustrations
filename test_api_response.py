#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端API返回的数据
"""

import requests
import json

def test_api_response():
    """测试后端API返回的数据"""
    try:
        # 测试历史记录API
        response = requests.get("http://localhost:9001/api/history?limit=5&offset=0&order=desc")
        
        if response.status_code == 200:
            data = response.json()
            print("=== API响应数据 ===")
            print(f"状态码: {response.status_code}")
            print(f"任务数量: {len(data.get('tasks', []))}")
            
            # 检查放大任务
            upscale_tasks = [task for task in data.get('tasks', []) if task.get('task_type') == 'upscale']
            print(f"\n放大任务数量: {len(upscale_tasks)}")
            
            for i, task in enumerate(upscale_tasks[:3]):
                print(f"\n--- 放大任务 {i+1} ---")
                print(f"任务ID: {task.get('id')}")
                print(f"状态: {task.get('status')}")
                print(f"描述: {task.get('description')}")
                print(f"image_urls: {task.get('image_urls')}")
                print(f"image_count: {task.get('image_count')}")
                print(f"result_path: {task.get('result_path')}")
                print(f"reference_image_path: {task.get('reference_image_path')}")
                
                # 如果有image_urls，测试第一个URL
                if task.get('image_urls') and len(task['image_urls']) > 0:
                    first_url = task['image_urls'][0]
                    print(f"第一个图片URL: {first_url}")
                    
                    # 测试图片URL
                    try:
                        img_response = requests.get(f"http://localhost:9001{first_url}")
                        print(f"图片请求状态码: {img_response.status_code}")
                        if img_response.status_code != 200:
                            print(f"图片请求失败: {img_response.text}")
                    except Exception as e:
                        print(f"图片请求异常: {e}")
                
                print("-" * 50)
        else:
            print(f"API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_api_response()
