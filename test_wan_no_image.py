#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'back'))

from back.core.workflows.wan_workflow import WanWorkflow
from back.core.model_manager import get_model_config

async def test_no_image_mode():
    """测试无图模式"""
    print("🔍 测试WAN工作流无图模式...")
    
    # 创建模拟的模型配置
    class MockModelConfig:
        def __init__(self):
            self.display_name = "Wan2.2视频生成"
            self.model_name = "wan2.2_video_generation"
    
    model_config = MockModelConfig()
    workflow = WanWorkflow(model_config)
    
    # 创建无图模式工作流
    result = workflow.create_workflow(
        parameters={'fps': 16, 'duration': 5}, 
        description='test prompt', 
        reference_image_path=None  # 无参考图
    )
    
    print("\n📋 无图模式检查结果:")
    print(f"节点68 (开始图): {result.get('68', {}).get('inputs', {}).get('image', 'NOT_FOUND')}")
    print(f"节点62 (结束图): {result.get('62', {}).get('inputs', {}).get('image', 'NOT_FOUND')}")
    
    # 检查工作流中是否还有默认图像
    node68_image = result.get('68', {}).get('inputs', {}).get('image', '')
    node62_image = result.get('62', {}).get('inputs', {}).get('image', '')
    
    if 'generated-image' in node68_image or 'generated-image' in node62_image:
        print("⚠️ 无图模式下仍然包含默认参考图！")
    else:
        print("✅ 无图模式正确，无默认参考图")

if __name__ == "__main__":
    asyncio.run(test_no_image_mode())
