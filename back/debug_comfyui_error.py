#!/usr/bin/env python3
"""
诊断ComfyUI提交工作流错误
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# ComfyUI配置
COMFYUI_BASE_URL = "http://localhost:8188"

async def test_comfyui_connection():
    """测试ComfyUI连接"""
    print("=== 测试ComfyUI连接 ===")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试基本连接
            async with session.get(f"{COMFYUI_BASE_URL}/system_stats") as response:
                if response.status == 200:
                    print("✅ ComfyUI服务正常运行")
                    stats = await response.json()
                    print(f"   系统状态: {stats}")
                else:
                    print(f"❌ ComfyUI服务异常，状态码: {response.status}")
                    return False
                    
            # 测试队列状态
            async with session.get(f"{COMFYUI_BASE_URL}/queue") as response:
                if response.status == 200:
                    queue_data = await response.json()
                    print(f"✅ 队列状态正常")
                    print(f"   运行中: {len(queue_data.get('queue_running', []))}")
                    print(f"   等待中: {len(queue_data.get('queue_pending', []))}")
                else:
                    print(f"❌ 获取队列状态失败，状态码: {response.status}")
                    
            return True
            
    except Exception as e:
        print(f"❌ 连接ComfyUI失败: {e}")
        return False

async def test_workflow_submission():
    """测试工作流提交"""
    print("\n=== 测试工作流提交 ===")
    
    # 创建一个简单的工作流进行测试
    test_workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "v1-5-pruned.ckpt"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "a beautiful sunset",
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality",
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 123456,
                "steps": 20,
                "cfg": 7,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": "test"
            }
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("📤 提交测试工作流...")
            
            async with session.post(
                f"{COMFYUI_BASE_URL}/prompt",
                json={"prompt": test_workflow}
            ) as response:
                
                print(f"   响应状态码: {response.status}")
                print(f"   响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 工作流提交成功")
                    print(f"   prompt_id: {result.get('prompt_id')}")
                    return result.get('prompt_id')
                else:
                    error_text = await response.text()
                    print(f"❌ 工作流提交失败")
                    print(f"   错误响应: {error_text}")
                    
                    try:
                        error_json = await response.json()
                        print(f"   错误JSON: {json.dumps(error_json, indent=2)}")
                    except:
                        pass
                        
                    return None
                    
    except Exception as e:
        print(f"❌ 提交工作流时发生异常: {e}")
        return None

async def test_our_workflow():
    """测试我们的实际工作流"""
    print("\n=== 测试我们的工作流 ===")
    
    # 加载我们的工作流模板
    try:
        with open('flux_kontext_dev_basic.json', 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        print("✅ 成功加载工作流模板")
        
        # 模拟我们的customize_workflow逻辑
        # 这里我们简化一下，只测试基本的工作流结构
        
        # 检查工作流中的关键节点
        required_nodes = ["42", "142", "146", "124", "177", "31"]
        missing_nodes = []
        
        for node_id in required_nodes:
            if node_id not in workflow:
                missing_nodes.append(node_id)
        
        if missing_nodes:
            print(f"❌ 工作流缺少必要节点: {missing_nodes}")
            return None
        else:
            print("✅ 工作流包含所有必要节点")
        
        # 尝试提交工作流
        try:
            async with aiohttp.ClientSession() as session:
                print("📤 提交我们的工作流...")
                
                async with session.post(
                    f"{COMFYUI_BASE_URL}/prompt",
                    json={"prompt": workflow}
                ) as response:
                    
                    print(f"   响应状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 我们的工作流提交成功")
                        print(f"   prompt_id: {result.get('prompt_id')}")
                        return result.get('prompt_id')
                    else:
                        error_text = await response.text()
                        print(f"❌ 我们的工作流提交失败")
                        print(f"   错误响应: {error_text}")
                        
                        try:
                            error_json = await response.json()
                            print(f"   错误JSON: {json.dumps(error_json, indent=2)}")
                        except:
                            pass
                            
                        return None
                        
        except Exception as e:
            print(f"❌ 提交我们的工作流时发生异常: {e}")
            return None
            
    except FileNotFoundError:
        print("❌ 找不到工作流模板文件: flux_kontext_dev_basic.json")
        return None
    except Exception as e:
        print(f"❌ 加载工作流模板失败: {e}")
        return None

async def main():
    """主函数"""
    print("🔍 开始诊断ComfyUI错误...")
    
    # 1. 测试连接
    if not await test_comfyui_connection():
        print("\n❌ ComfyUI连接失败，请检查ComfyUI是否正在运行")
        return
    
    # 2. 测试简单工作流
    test_prompt_id = await test_workflow_submission()
    
    # 3. 测试我们的工作流
    our_prompt_id = await test_our_workflow()
    
    print("\n=== 诊断结果 ===")
    if test_prompt_id:
        print("✅ 简单工作流可以正常提交")
    else:
        print("❌ 简单工作流提交失败")
        
    if our_prompt_id:
        print("✅ 我们的工作流可以正常提交")
    else:
        print("❌ 我们的工作流提交失败")
        
    if not test_prompt_id and not our_prompt_id:
        print("\n💡 建议:")
        print("1. 检查ComfyUI是否正常运行")
        print("2. 检查ComfyUI的模型文件是否存在")
        print("3. 检查ComfyUI的日志输出")

if __name__ == "__main__":
    asyncio.run(main())
