#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
画布历史记录API测试脚本
用于测试画布历史记录相关的API接口
"""

import json
import time
import uuid
from datetime import datetime

import requests

# API基础URL
BASE_URL = "http://localhost:8000/api/canvas"

def test_create_history_record():
    """测试创建历史记录"""
    print("🧪 测试创建历史记录...")
    
    record_data = {
        "id": str(uuid.uuid4()),
        "task_id": str(uuid.uuid4()),
        "prompt": "测试提示词",
        "original_image_url": "/api/image/upload/test.jpg",
        "result_image_url": "/api/image/result/test.jpg",
        "parameters": {
            "brush_size": 20,
            "opacity": 0.8,
            "mode": "inpainting"
        },
        "timestamp": int(time.time() * 1000),
        "type": "inpainting"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/history", json=record_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 创建成功: {result['id']}")
            return result['id']
        else:
            print(f"❌ 创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def test_get_history_records():
    """测试获取历史记录列表"""
    print("🧪 测试获取历史记录列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/history?limit=10&offset=0&order=desc")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取成功: 共 {result['total']} 条记录")
            return result['records']
        else:
            print(f"❌ 获取失败: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return []

def test_get_single_history_record(record_id):
    """测试获取单个历史记录"""
    print(f"🧪 测试获取单个历史记录: {record_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/history/{record_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取成功: {result['prompt']}")
            return result
        else:
            print(f"❌ 获取失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def test_update_history_record(record_id):
    """测试更新历史记录"""
    print(f"🧪 测试更新历史记录: {record_id}")
    
    update_data = {
        "prompt": "更新后的提示词",
        "parameters": {
            "brush_size": 30,
            "opacity": 0.9,
            "mode": "outpainting"
        }
    }
    
    try:
        response = requests.put(f"{BASE_URL}/history/{record_id}", json=update_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 更新成功: {result['prompt']}")
            return result
        else:
            print(f"❌ 更新失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def test_batch_create_history_records():
    """测试批量创建历史记录"""
    print("🧪 测试批量创建历史记录...")
    
    records_data = {
        "records": [
            {
                "id": str(uuid.uuid4()),
                "task_id": str(uuid.uuid4()),
                "prompt": f"批量测试记录 {i}",
                "original_image_url": f"/api/image/upload/batch_{i}.jpg",
                "result_image_url": f"/api/image/result/batch_{i}.jpg",
                "parameters": {"test": True, "batch_id": i},
                "timestamp": int(time.time() * 1000) + i,
                "type": "inpainting"
            }
            for i in range(3)
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/history/batch", json=records_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 批量创建成功: {result['success_count']}/{result['total_count']}")
            return True
        else:
            print(f"❌ 批量创建失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_delete_history_record(record_id):
    """测试删除历史记录"""
    print(f"🧪 测试删除历史记录: {record_id}")
    
    try:
        response = requests.delete(f"{BASE_URL}/history/{record_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 删除成功: {result['message']}")
            return True
        else:
            print(f"❌ 删除失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试画布历史记录API...")
    print("=" * 50)
    
    # 测试创建记录
    record_id = test_create_history_record()
    print()
    
    # 测试获取记录列表
    records = test_get_history_records()
    print()
    
    # 测试获取单个记录
    if record_id:
        test_get_single_history_record(record_id)
        print()
        
        # 测试更新记录
        test_update_history_record(record_id)
        print()
    
    # 测试批量创建
    test_batch_create_history_records()
    print()
    
    # 测试删除记录
    if record_id:
        test_delete_history_record(record_id)
        print()
    
    print("=" * 50)
    print("🎉 测试完成！")

if __name__ == "__main__":
    main()
