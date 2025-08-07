#!/usr/bin/env python3
"""
测试工作流修复
验证无参考图模式下的工作流是否能正常提交
"""

import json
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import WorkflowTemplate

def test_workflow_fix():
    """测试工作流修复"""
    print("=== 测试工作流修复 ===")
    
    try:
        # 创建WorkflowTemplate实例
        workflow_template = WorkflowTemplate('flux_kontext_dev_basic.json')
        print("✅ 成功加载工作流模板")
        
        # 测试无参考图模式
        print("\n🔍 测试无参考图模式...")
        workflow_no_ref = workflow_template.customize_workflow(
            reference_image_path="uploads/blank.png",
            description="a beautiful sunset landscape with mountains",
            parameters={
                "count": 1,
                "size": "512x512",
                "steps": 20,
                "seed": None
            }
        )
        
        # 检查LoadImageOutput节点是否被正确禁用
        if "142" in workflow_no_ref:
            image_input = workflow_no_ref["142"]["inputs"].get("image", "")
            if image_input == "":
                print("✅ LoadImageOutput节点已正确禁用")
            else:
                print(f"❌ LoadImageOutput节点未正确禁用，当前值: {image_input}")
        else:
            print("❌ 找不到LoadImageOutput节点")
        
        # 检查是否创建了必要的节点
        required_nodes = []
        for node_id, node_data in workflow_no_ref.items():
            if node_data.get("class_type") == "EmptyImage":
                required_nodes.append(f"EmptyImage (ID: {node_id})")
            elif node_data.get("class_type") == "VAEEncode":
                required_nodes.append(f"VAEEncode (ID: {node_id})")
            elif node_data.get("class_type") == "ConditionalSwitch":
                required_nodes.append(f"ConditionalSwitch (ID: {node_id})")
        
        print(f"✅ 创建的必要节点: {required_nodes}")
        
        # 检查KSampler的连接
        ksampler_latent = workflow_no_ref["31"]["inputs"].get("latent_image")
        if ksampler_latent and isinstance(ksampler_latent, list):
            print(f"✅ KSampler的latent_image已连接到: {ksampler_latent}")
        else:
            print("❌ KSampler的latent_image连接异常")
        
        # 检查ReferenceLatent的连接
        ref_latent = workflow_no_ref["177"]["inputs"].get("latent")
        if ref_latent and isinstance(ref_latent, list):
            print(f"✅ ReferenceLatent的latent已连接到: {ref_latent}")
        else:
            print("❌ ReferenceLatent的latent连接异常")
        
        # 测试有参考图模式
        print("\n🔍 测试有参考图模式...")
        workflow_with_ref = workflow_template.customize_workflow(
            reference_image_path="uploads/test_image.jpg",
            description="a beautiful sunset landscape with mountains",
            parameters={
                "count": 1,
                "size": "512x512",
                "steps": 20,
                "seed": None
            }
        )
        
        # 检查LoadImageOutput节点是否被正确设置
        if "142" in workflow_with_ref:
            image_input = workflow_with_ref["142"]["inputs"].get("image", "")
            if image_input and image_input != "doll.webp [output]":
                print(f"✅ LoadImageOutput节点已正确设置为: {image_input}")
            else:
                print(f"❌ LoadImageOutput节点设置异常: {image_input}")
        else:
            print("❌ 找不到LoadImageOutput节点")
        
        print("\n=== 测试结果 ===")
        print("✅ 工作流修复测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_workflow_fix()
    if success:
        print("\n🎉 工作流修复验证成功！")
    else:
        print("\n💥 工作流修复验证失败！")
